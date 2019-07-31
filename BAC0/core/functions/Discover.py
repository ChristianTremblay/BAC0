#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
WhoisIAm.py - creation of Whois and IAm requests

Used while defining an app
ex.: class BasicScript(WhoisIAm):

Class : WhoisIAm

"""
# --- standard Python modules ---
import time

# --- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging
from bacpypes.apdu import WhoIsRequest, IAmRequest

from bacpypes.core import deferred
from bacpypes.pdu import Address, GlobalBroadcast, LocalBroadcast
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.object import get_object_class, get_datatype
from bacpypes.iocb import IOCB

from bacpypes.netservice import NetworkServiceAccessPoint, NetworkServiceElement
from bacpypes.npdu import (
    WhoIsRouterToNetwork,
    IAmRouterToNetwork,
    InitializeRoutingTable,
    InitializeRoutingTableAck,
    WhatIsNetworkNumber,
    NetworkNumberIs,
    RejectMessageToNetwork,
)

# --- this application's modules ---
from ..io.IOExceptions import (
    SegmentationNotSupported,
    ReadPropertyException,
    ReadPropertyMultipleException,
    NoResponseFromController,
    ApplicationNotStarted,
)
from ...core.utils.notes import note_and_log

# ------------------------------------------------------------------------------
class NetworkServiceElementWithRequests(NetworkServiceElement):
    """
    This class will add the capability to send requests at network level
    """

    def __init__(self):
        NetworkServiceElement.__init__(self)

        # no pending request
        self._request = None
        self._iartn = []

    def request(self, adapter, npdu):
        # save a copy of the request
        self._request = npdu

        # forward it along
        NetworkServiceElement.request(self, adapter, npdu)

    def indication(self, adapter, npdu):
        if isinstance(npdu, IAmRouterToNetwork):
            if isinstance(self._request, WhoIsRouterToNetwork):
                print("{} router to {}".format(npdu.pduSource, npdu.iartnNetworkList))
                address = str(npdu.pduSource)
                self._iartn.append(address)

        elif isinstance(npdu, InitializeRoutingTableAck):
            print("{} routing table".format(npdu.pduSource))
            for rte in npdu.irtaTable:
                print("    {} {} {}".format(rte.rtDNET, rte.rtPortID, rte.rtPortInfo))

        elif isinstance(npdu, NetworkNumberIs):
            print("{} network number is {}".format(npdu.pduSource, npdu.nniNet))

        elif isinstance(npdu, RejectMessageToNetwork):
            print(
                "{} Rejected message to network (reason : {}) | Request was : {}".format(
                    npdu.pduSource, npdu.rmtnRejectionReason, self._request
                )
            )

        # forward it along
        NetworkServiceElement.indication(self, adapter, npdu)

    def response(self, adapter, npdu):
        # forward it along
        NetworkServiceElement.response(self, adapter, npdu)

    def confirmation(self, adapter, npdu):
        # forward it along
        NetworkServiceElement.confirmation(self, adapter, npdu)


@note_and_log
class Discover:
    """
    Define BACnet WhoIs and IAm functions.
    """

    def whois(self, *args, global_broadcast=False):
        """
        Build a WhoIs request

        :param args: string built as [ <addr>] [ <lolimit> <hilimit> ] **optional**
        :returns: discoveredDevices as a defaultdict(int)

        Example::

            whois()             # WhoIs broadcast globally.  Every device will respond with an IAm
            whois('2:5')        # WhoIs looking for the device at (Network 2, Address 5)
            whois('10 1000')    # WhoIs looking for devices in the ID range (10 - 1000) 

        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        if args:
            args = args[0].split()
        msg = args if args else "any"

        self._log.debug("do_whois {!r}".format(msg))

        # build a request
        request = WhoIsRequest()
        if (len(args) == 1) or (len(args) == 3):
            request.pduDestination = Address(args[0])
            del args[0]
        else:
            if global_broadcast:
                request.pduDestination = GlobalBroadcast()
            else:
                request.pduDestination = LocalBroadcast()

        if len(args) == 2:
            request.deviceInstanceRangeLowLimit = int(args[0])
            request.deviceInstanceRangeHighLimit = int(args[1])
        self._log.debug("{:>12} {}".format("- request:", request))

        iocb = IOCB(request)  # make an IOCB
        self.this_application._last_i_am_received = []
        # pass to the BACnet stack
        deferred(self.this_application.request_io, iocb)

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

        if iocb.ioError:  # unsuccessful: error/reject/abort
            pass

        time.sleep(3)
        self.discoveredDevices = self.this_application.i_am_counter
        return self.this_application._last_i_am_received

    def iam(self):
        """
        Build an IAm response.  IAm are sent in response to a WhoIs request that;  
        matches our device ID, whose device range includes us, or is a broadcast.
        Content is defined by the script (deviceId, vendor, etc...)

        :returns: bool

        Example::

            iam()
        """

        self._log.debug("do_iam")

        try:
            # build a response
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # fill the response with details about us (from our device object)
            request.iAmDeviceIdentifier = self.this_device.objectIdentifier
            request.maxAPDULengthAccepted = self.this_device.maxApduLengthAccepted
            request.segmentationSupported = self.this_device.segmentationSupported
            request.vendorID = self.this_device.vendorIdentifier
            self._log.debug("{:>12} {}".format("- request:", request))

            iocb = IOCB(request)  # make an IOCB
            deferred(self.this_application.request_io, iocb)
            iocb.wait()
            return True

        except Exception as error:
            self._log.error("exception: {!r}".format(error))
            return False

    def whois_router_to_network(self, args):
        # build a request
        try:
            request = WhoIsRouterToNetwork()
            if not args:
                request.pduDestination = LocalBroadcast()
            elif args[0].isdigit():
                request.pduDestination = LocalBroadcast()
                request.wirtnNetwork = int(args[0])
            else:
                request.pduDestination = Address(args[0])
                if len(args) > 1:
                    request.wirtnNetwork = int(args[1])
        except:
            print("invalid arguments")
            return
        self.this_application.nse.request(
            self.this_application.nsap.local_adapter, request
        )

        # sleep for responses
        time.sleep(3.0)
        self.init_routing_table(str(self.this_application.nse._iartn.pop()))

    def init_routing_table(self, address):
        """
        irt <addr>

        Send an empty Initialize-Routing-Table message to an address, a router
        will return an acknowledgement with its routing table configuration.
        """
        # build a request
        print("Addr : ", address)
        try:
            request = InitializeRoutingTable()
            request.pduDestination = Address(address)
        except:
            print("invalid arguments")
            return

        # give it to the network service element
        self.this_application.nse.request(
            self.this_application.nsap.local_adapter, request
        )

    def what_is_network_number(self, args=""):
        """
        winn [ <addr> ]

        Send a What-Is-Network-Number message.  If the address is unspecified
        the message is locally broadcast.
        """
        args = args.split()

        # build a request
        try:
            request = WhatIsNetworkNumber()
            if len(args) > 0:
                request.pduDestination = Address(args[0])
            else:
                request.pduDestination = LocalBroadcast()
        except:
            print("invalid arguments")
            return

        # give it to the network service element
        self.this_application.nse.request(
            self.this_application.nsap.local_adapter, request
        )

        # sleep for responses
        time.sleep(3.0)
