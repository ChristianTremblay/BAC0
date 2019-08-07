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
# --- standard Python modules ---
from collections import defaultdict

# --- 3rd party modules ---
from bacpypes.app import ApplicationIOController
from bacpypes.pdu import Address
from bacpypes.service.object import ReadWritePropertyMultipleServices
from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.bvllservice import BIPSimple, BIPForeign, AnnexJCodec, UDPMultiplexer
from bacpypes.appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from bacpypes.comm import ApplicationServiceElement, bind

# basic services
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices

# --- this application's modules ---
from ..utils.notes import note_and_log
from ..functions.Discover import NetworkServiceElementWithRequests

# ------------------------------------------------------------------------------


class BAC0Common:
    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        self.log("do_WhoIsRequest {!r}".format(apdu))

        # build a key from the source and parameters
        key = (
            str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
        )

        # count the times this has been received
        self.who_is_counter[key] += 1

        # continue with the default implementation

    #        BIPSimpleApplication.do_WhoIsRequest(self, apdu)

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        self.log("do_IAmRequest {!r}".format(apdu))
 
        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource), apdu.iAmDeviceIdentifier[1])
        self.i_am_counter[key] += 1
        self._last_i_am_received.append(key)


@note_and_log
class BAC0Application(
    ApplicationIOController,
    WhoIsIAmServices,
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
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
        bbmdAddress=None,
        bbmdTTL=0,
        deviceInfoCache=None,
        aseID=None,
    ):

        ApplicationIOController.__init__(
            self, localDevice, deviceInfoCache, aseID=aseID
        )

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
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the BIP stack to the network, no network number
        self.nsap.bind(self.bip, address=self.localAddress)

        self.i_am_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)

        # keep track of requests to line up responses
        self._request = None
        self._last_i_am_received = []

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        self.log("do_IAmRequest {!r}".format(apdu))

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource), apdu.iAmDeviceIdentifier[1])
        self.i_am_counter[key] += 1
        self._last_i_am_received.append(key)

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        self.log("do_WhoIsRequest {!r}".format(apdu))

        # build a key from the source and parameters
        key = (
            str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
        )

        # count the times this has been received
        self.who_is_counter[key] += 1

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
    ApplicationIOController,
    WhoIsIAmServices,
    ReadWritePropertyServices,
    ReadWritePropertyMultipleServices,
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
        bbmdAddress=None,
        bbmdTTL=0,
        deviceInfoCache=None,
        aseID=None,
    ):

        ApplicationIOController.__init__(
            self, localDevice, deviceInfoCache, aseID=aseID
        )

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
        self.who_is_counter = defaultdict(int)
        # keep track of requests to line up responses
        self._request = None
        self._last_i_am_received = []

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        self.log("do_IAmRequest {!r}".format(apdu))

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource), apdu.iAmDeviceIdentifier[1])
        self.i_am_counter[key] += 1
        self._last_i_am_received.append(key)
        # continue with the default implementation

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        self.log("do_WhoIsRequest {!r}".format(apdu))

        # build a key from the source and parameters
        key = (
            str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
        )

        # count the times this has been received
        self.who_is_counter[key] += 1

    def close_socket(self):
        # pass to the multiplexer, then down to the sockets
        self.mux.close_socket()
