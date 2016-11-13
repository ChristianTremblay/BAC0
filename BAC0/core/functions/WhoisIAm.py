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
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.object import get_object_class, get_datatype
from bacpypes.iocb import IOCB

from ..functions.debug import log_debug, log_exception
from ..io.IOExceptions import SegmentationNotSupported, ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController, ApplicationNotStarted


@bacpypes_debugging
class WhoisIAm():
    """
    This class will be used by inheritance to add features to an app
    Will allows the usage of whois and iam functions
    """
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
        if not self._started:
            raise ApplicationNotStarted('App not running, use startApp() function')
        if args:
            args = args[0].split()

        if not args:
            msg = "any"
        else:
            msg = args

        log_debug(WhoisIAm, "do_whois %r" % msg)


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
        log_debug(WhoisIAm, "    - request: %r" % request)


         # make an IOCB
        iocb = IOCB(request)
        log_debug(WhoisIAm, "    - iocb: %r", iocb)

        # give it to the application
        self.this_application.request_io(iocb)
        # give it to the application
#        print(self.this_application)
#        self.this_application.request(request)
#        iocb = self.this_application.request(request)
        iocb.wait()
#        
#        # do something for success
#        if iocb.ioResponse:
#            apdu = iocb.ioResponse
#            # should be an ack
#            if not isinstance(apdu, IAmRequest) and not isinstance(apdu, WhoIsRequest):
#                log_debug(WhoisIAm,"    - not an ack")
#                return
#            # find the datatype
#            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
#            log_debug(WhoisIAm,"    - datatype: %r", datatype)
#            if not datatype:
#                raise TypeError("unknown datatype")
#                
#            # special case for array parts, others are managed by cast_out
#            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
#                if apdu.propertyArrayIndex == 0:
#                    value = apdu.propertyValue.cast_out(Unsigned)
#                else:
#                    value = apdu.propertyValue.cast_out(datatype.subtype)
#            else:
#                value = apdu.propertyValue.cast_out(datatype)
#            log_debug(WhoisIAm,"    - value: %r", value)
#                
#            if isinstance(apdu, IAmRequest):
#                # build a key from the source, just use the instance number
#                key = (str(apdu.pduSource),
#                       apdu.iAmDeviceIdentifier[1],)
#                # count the times this has been received
#                self.i_am_counter[key] += 1
#    
#            # Given an Who Is request, cache it.
#            if isinstance(apdu, WhoIsRequest):
#                # build a key from the source and parameters
#                key = (str(apdu.pduSource),
#                       apdu.deviceInstanceRangeLowLimit,
#                       apdu.deviceInstanceRangeHighLimit,
#                       )
#
#            # count the times this has been received
#            self.who_is_counter[key] += 1

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

        log_debug(WhoisIAm, "do_iam")

        try:
            # build a request
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = self.this_device.objectIdentifier
            request.maxAPDULengthAccepted = self.this_device.maxApduLengthAccepted
            request.segmentationSupported = self.this_device.segmentationSupported
            request.vendorID = self.this_device.vendorIdentifier
            log_debug(WhoisIAm, "    - request: %r" % request)

            # give it to the application
            iocb = self.this_application.request(request)
            iocb.wait()
            return True

        except Exception as error:
            log_exception("exception: %r" % error)
            return False



