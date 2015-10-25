#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module allows the creation of Whois and IAm requests by and app

Usage
Must be used while defining an app
ex.: class BasicScript(WhoisIAm):

Class : WhoisIAm

"""

from bacpypes.debugging import bacpypes_debugging
from bacpypes.apdu import WhoIsRequest, IAmRequest

from bacpypes.pdu import Address, GlobalBroadcast


# some debugging
_DEBUG = 0


@bacpypes_debugging
class WhoisIAm():
    """
    This class will be used by inheritance to add features to an app
    Will allows the usage of whois and iam functions
    """

    def __init__(self):
        self.this_application = None
        self.this_device = None

    def whois(self, *args):
        """
        Creation of a whois requests
        Requets is given to the app

        :param args: string built as [ <addr>] [ <lolimit> <hilimit> ] **optional**
        :returns: discoveredDevices as a defaultdict(int)

        Example::

            whois()
            #will create a broadcast whois request and every device will response by a Iam
            whois('2:5')
            #will create a whois request aimed at device 5
            whois('10 1000')
            #will create a whois request looking for device ID 10 to 1000

        """
        if args:
            args = args[0].split()

        if not args:
            msg = "any"
        else:
            msg = args

        log_debug("do_whois %r" % msg)

        try:
            # build a request
            request = WhoIsRequest()
            if (len(args) == 1) or (len(args) == 3):
                request.pduDestination = Address(args[0])
                del args[0]
            else:
                request.pduDestination = GlobalBroadcast()

            if len(args) == 2:
                request.deviceInstanceRangeLowLimit = int(args[0])
                request.deviceInstanceRangeHighLimit = int(args[1])
            log_debug("    - request: %r" % request)

            # give it to the application
            self.this_application.request(request)

        except Exception as error:
            log_exception("exception: %r" % error)

        self.discoveredDevices = self.this_application.i_am_counter

        return self.discoveredDevices

    def iam(self):
        """
        Creation of a iam request

        Iam requests are sent when whois requests ask for it
        Content is defined by the script (deviceId, vendor, etc...)

        :returns: bool

        Example::

            iam()
        """

        log_debug("do_iam")

        try:
            # build a request
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = self.this_device.objectIdentifier
            request.maxAPDULengthAccepted = self.this_device.maxApduLengthAccepted
            request.segmentationSupported = self.this_device.segmentationSupported
            request.vendorID = self.this_device.vendorIdentifier
            log_debug("    - request: %r" % request)

            # give it to the application
            self.this_application.request(request)
            return True

        except Exception as error:
            log_exception("exception: %r" % error)
            return False


def log_debug(txt, *args):
    """
    Helper function to log debug messages
    """
    if _DEBUG:
        if args:
            msg = txt % args
        else:
            msg = txt
        # pylint: disable=E1101,W0212
        WhoisIAm._debug(msg)


def log_exception(txt, *args):
    """
    Helper function to log debug messages
    """
    if args:
        msg = txt % args
    else:
        msg = txt
    # pylint: disable=E1101,W0212
    WhoisIAm._exception(msg)
