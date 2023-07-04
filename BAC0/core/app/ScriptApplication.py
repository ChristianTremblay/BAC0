#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
SimpleApplication
=================

A basic BACnet application (bacpypes BIPSimpleApplication) for interacting with
the bacpypes BACnet stack.  It enables the base-level BACnet functionality
(a.k.a. device discovery) - meaning it can send & receive WhoIs & IAm messages.

Additional functionality is enabled by inheriting this application, and then
extending it with more functions. [See BAC0.scripts for more examples of this.]

"""
import typing as t

# --- standard Python modules ---
from collections import defaultdict
from typing import Any, Dict, Optional

from bacpypes.apdu import IAmRequest, ReadRangeACK, SimpleAckPDU

# --- 3rd party modules ---
from bacpypes.app import ApplicationIOController
from bacpypes.appservice import ApplicationServiceAccessPoint, StateMachineAccessPoint
from bacpypes.bvllservice import (
    BIPBBMD,
    AnnexJCodec,
    BIPForeign,
    BIPSimple,
    UDPMultiplexer,
)
from bacpypes.comm import Client, bind
from bacpypes.constructeddata import (
    Array,
    List,
    SequenceOfAny,
)
from bacpypes.core import deferred
from bacpypes.errors import ExecutionError, RejectException
from bacpypes.iocb import IOCB
from bacpypes.local.device import LocalDeviceObject
from bacpypes.netservice import NetworkServiceAccessPoint
from bacpypes.object import PropertyError
from bacpypes.pdu import Address
from bacpypes.service.cov import ChangeOfValueServices

# basic services
from bacpypes.service.device import WhoHasIHaveServices, WhoIsIAmServices
from bacpypes.service.object import (
    ReadWritePropertyMultipleServices,
    ReadWritePropertyServices,
)

from ..functions.Discover import NetworkServiceElementWithRequests

# --- this application's modules ---
from ..utils.notes import note_and_log

# ------------------------------------------------------------------------------


class common_mixin:
    """
    They take message coming from the network that are not generated from
    a request we made.
    """

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        self._log.debug("do_IAmRequest {!r}".format(apdu))

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource), apdu.iAmDeviceIdentifier[1])
        self.i_am_counter[key] += 1
        self._last_i_am_received.append(key)

    def do_IHaveRequest(self, apdu):
        """Given an I-Have request, cache it."""
        self._log.debug("do_IHaveRequest {!r}".format(apdu))

        # build a key from the source, using object name
        key = (str(apdu.pduSource), apdu.objectName)
        self.i_have_counter[key] += 1
        self._last_i_have_received.append(key)

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""

        # build a key from the source and parameters
        key = (
            str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
        )
        self._log.debug(
            "do_WhoIsRequest from {} | {} to {}".format(key[0], key[1], key[2])
        )

        # count the times this has been received
        self.who_is_counter[key] += 1
        low_limit = key[1]
        high_limit = key[2]

        # count the times this has been received
        self.who_is_counter[key] += 1

        if low_limit is not None and self.localDevice.objectIdentifier[1] < low_limit:
            return
        if high_limit is not None and self.localDevice.objectIdentifier[1] > high_limit:
            return
        # generate an I-Am
        self._log.debug("Responding to Who is by a Iam")
        self.iam_req.pduDestination = apdu.pduSource
        iocb = IOCB(self.iam_req)  # make an IOCB
        deferred(self.request_io, iocb)

    def do_ConfirmedCOVNotificationRequest(self, apdu):
        # look up the process identifier
        context = self.subscription_contexts.get(apdu.subscriberProcessIdentifier, None)
        if not context or apdu.pduSource != context.address:
            self._log.warning(
                "Unsollicited COV Notification received from {} ({}). Have you restarted the application recently ?".format(
                    apdu.pduSource, apdu
                )
            )
            # this is turned into cancel_cov request and sent back to the client

        else:
            # now tell the context object
            elements = context.cov_notification(apdu)

            # success
            response = SimpleAckPDU(context=apdu)

            # send a confirmation
            self.response(response)
            self._log.debug("Confirmed COV Notification: {}".format(elements))
            self.subscription_contexts["context_callback"](elements)

            # execute callback
            if context.callback is not None:
                context.callback(elements=elements)

    def do_UnconfirmedCOVNotificationRequest(self, apdu):
        # look up the process identifier
        context = self.subscription_contexts.get(apdu.subscriberProcessIdentifier, None)
        if not context or apdu.pduSource != context.address:
            return

        # now tell the context object
        elements = context.cov_notification(apdu)
        self._log.debug("Unconfirmed COV Notification: {}".format(elements))
        self.subscription_contexts["context_callback"](elements)

        # execute callback
        if context.callback is not None:
            context.callback(elements=elements)

    def do_ReadRangeRequest(self, apdu):
        self._log.debug("do_ReadRangeRequest %r", apdu)

        # extract the object identifier
        objId = apdu.objectIdentifier

        # get the object
        obj = self.get_object_id(objId)
        self._log.debug("    - object: %r", obj)

        if not obj:
            raise ExecutionError(errorClass="object", errorCode="unknownObject")

        # get the datatype
        datatype = obj.get_datatype(apdu.propertyIdentifier)
        self._log.debug("    - datatype: %r", datatype)

        # must be a list, or an array of lists
        if issubclass(datatype, List):
            pass
        elif (
            (apdu.propertyArrayIndex is not None)
            and issubclass(datatype, Array)
            and issubclass(datatype.subtype, List)
        ):
            pass
        else:
            raise ExecutionError(errorClass="property", errorCode="propertyIsNotAList")

        # get the value
        self._log.debug(apdu.__dict__)
        value = obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex)
        self._log.debug(f"    - value: {value.__repr__()} | of type {type(value)}")
        if value is None:
            raise PropertyError(apdu.propertyIdentifier)
        if isinstance(value, List):
            self._log.debug("    - value is a list of: %r", datatype.subtype)
            # datatype = datatype.subtype

        if apdu.range.byPosition:
            range_by_position = apdu.range.byPosition
            self._log.debug("    - range_by_position: %r", range_by_position)

        elif apdu.range.bySequenceNumber:
            range_by_sequence_number = apdu.range.bySequenceNumber
            self._log.debug(
                "    - range_by_sequence_number: %r", range_by_sequence_number
            )

        elif apdu.range.byTime:
            range_by_time = apdu.range.byTime
            self._log.debug("    - range_by_time: %r", range_by_time)

        else:
            raise RejectException("missingRequiredParameter")

        # this is an ack
        resp = ReadRangeACK(context=apdu)
        resp.objectIdentifier = objId
        resp.propertyIdentifier = apdu.propertyIdentifier
        resp.propertyArrayIndex = apdu.propertyArrayIndex

        resp.resultFlags = [1, 1, 0]
        resp.itemCount = len(value)

        # save the result in the item data
        item_data = SequenceOfAny()
        item_data.cast_in(value)
        resp.itemData = item_data
        self._log.debug("    - itemData : %r", resp.itemData)
        self._log.debug("    - resp: %r", resp)
        self.response(resp)
        # return the result
        # iocb = IOCB(resp)  # make an IOCB
        # deferred(self.request_io, iocb)


@note_and_log
class BAC0Application(
    common_mixin,
    ApplicationIOController,
    WhoIsIAmServices,
    WhoHasIHaveServices,
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
    ChangeOfValueServices,
):
    """
    Defines a basic BACnet/IP application to process BACnet requests.

    :param *args: local object device, local IP address
        See BAC0.scripts.BasicScript for more details.

    """

    def __init__(
        self,
        localDevice: LocalDeviceObject,
        localAddress: Address,
        networkNumber: int = None,
        bbmdAddress=None,
        bbmdTTL: int = 0,
        deviceInfoCache=None,
        aseID=None,
        iam_req: Optional[IAmRequest] = None,
        subscription_contexts: Optional[Dict[Any, Any]] = None,
    ) -> None:

        ApplicationIOController.__init__(
            self, localDevice, deviceInfoCache, aseID=aseID
        )

        self.iam_req = iam_req
        # local address might be useful for subclasses
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)
        self.networkNumber = networkNumber
        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElementWithRequests()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the BIP stack to the network, no network number
        self.nsap.bind(self.bip, net=self.networkNumber, address=self.localAddress)

        self.i_am_counter: t.Dict[t.Tuple[str, int], int] = defaultdict(int)
        self.i_have_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)

        # keep track of requests to line up responses
        self._request = None
        self._last_i_am_received = []
        self._last_i_have_received = []

        # to support CoV
        self.subscription_contexts = subscription_contexts

    def close_socket(self):
        # pass to the multiplexer, then down to the sockets
        self.mux.close_socket()

    def request(self, apdu):
        # save a copy of the request
        self._request = apdu

        # forward it along
        super(BAC0Application, self).request(apdu)


@note_and_log
class BAC0ForeignDeviceApplication(
    common_mixin,
    ApplicationIOController,
    WhoIsIAmServices,
    WhoHasIHaveServices,
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
    ChangeOfValueServices,
):
    """
    Defines a basic BACnet/IP application to process BACnet requests.

    :param *args: local object device, local IP address
        See BAC0.scripts.BasicScript for more details.

    """

    def __init__(
        self,
        localDevice,
        localAddress,
        networkNumber: int = None,
        bbmdAddress=None,
        bbmdTTL=0,
        deviceInfoCache=None,
        aseID=None,
        iam_req=None,
        subscription_contexts=None,
    ):

        ApplicationIOController.__init__(
            self, localDevice, deviceInfoCache, aseID=aseID
        )

        self.iam_req = iam_req
        # local address might be useful for subclasses
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElementWithRequests()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPForeign(bbmdAddress, bbmdTTL)
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress, noBroadcast=True)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the NSAP to the stack, no network number
        self.nsap.bind(self.bip)

        self.i_am_counter = defaultdict(int)
        self.i_have_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)
        # keep track of requests to line up responses
        self._request = None
        self._last_i_am_received = []
        self._last_i_have_received = []

        # to support CoV
        self.subscription_contexts = subscription_contexts

    def close_socket(self):
        # pass to the multiplexer, then down to the sockets
        self.mux.close_socket()


class NullClient(Client):
    def __init__(self, cid=None):
        Client.__init__(self, cid=cid)

    def confirmation(self, *args, **kwargs):
        pass


@note_and_log
class BAC0BBMDDeviceApplication(
    common_mixin,
    ApplicationIOController,
    WhoIsIAmServices,
    WhoHasIHaveServices,
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
    ChangeOfValueServices,
):
    """
    Defines a basic BACnet/IP application to process BACnet requests.

    :param *args: local object device, local IP address
        See BAC0.scripts.BasicScript for more details.

    """

    bdt = []

    def __init__(
        self,
        localDevice,
        localAddress,
        networkNumber: int = None,
        bdtable=[],
        deviceInfoCache=None,
        aseID=None,
        iam_req=None,
        subscription_contexts=None,
    ):

        self.bdtable = bdtable

        null_client = NullClient()

        ApplicationIOController.__init__(
            self, localDevice, deviceInfoCache, aseID=aseID
        )

        self.iam_req = iam_req
        # local address might be useful for subclasses
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElementWithRequests()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPBBMD(self.localAddress)
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress, noBroadcast=False)

        # bind the bottom layers
        # bind(self.bip, self.annexj, self.mux.annexJ)
        bind(null_client, self.bip, self.annexj, self.mux.annexJ)

        if self.bdtable:
            for bdtentry in self.bdtable:
                self.add_peer(bdtentry)

        # bind the NSAP to the stack, no network number
        self.nsap.bind(self.bip)
        # self.nsap.bind(self.bip, net=self.networkNumber)

        self.i_am_counter = defaultdict(int)
        self.i_have_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)
        # keep track of requests to line up responses
        self._request = None
        self._last_i_am_received = []
        self._last_i_have_received = []

        # to support CoV
        self.subscription_contexts = subscription_contexts

    def add_peer(self, address):
        try:
            bdt_address = Address(address)
            self.bip.add_peer(bdt_address)
        except Exception:
            raise

    def remove_peer(self, address):
        try:
            bdt_address = Address(address)
            self.bip.remove_peer(bdt_address)
        except Exception:
            raise

    def close_socket(self):
        # pass to the multiplexer, then down to the sockets
        self.mux.close_socket()
