#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
WhoisIAm.py - creation of Whois and IAm requests

Used while defining an app
ex.: class BasicScript(WhoisIAm):

Class : WhoisIAm

'''
#--- standard Python modules ---

#--- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging
from bacpypes.apdu import WhoIsRequest, IAmRequest

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.object import get_object_class, get_datatype
from bacpypes.iocb import IOCB

#--- this application's modules ---
from ..io.IOExceptions import SegmentationNotSupported, ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController, ApplicationNotStarted
from ...core.utils.notes import note_and_log

#------------------------------------------------------------------------------


@note_and_log
class WhoisIAm():
    """
    Define BACnet WhoIs and IAm functions.
    """

    def whois(self, *args):
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
            raise ApplicationNotStarted(
                'BACnet stack not running - use startApp()')

        if args:
            args = args[0].split()
        msg = args if args else 'any'

        self._log.debug("do_whois {!r}".format(msg))

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
        self._log.debug("{:>12} {}".format("- request:", request))

        iocb = IOCB(request)                            # make an IOCB

        # pass to the BACnet stack
        self.this_application.request_io(iocb)

        iocb.wait()             # Wait for BACnet response

        if iocb.ioResponse:     # successful response
            apdu = iocb.ioResponse

        if iocb.ioError:        # unsuccessful: error/reject/abort
            pass

        self.discoveredDevices = self.this_application.i_am_counter
        return self.discoveredDevices

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

            iocb = self.this_application.request(
                request)       # pass to the BACnet stack
            iocb.wait()
            return True

        except Exception as error:
            self._log.error("exception: {!r}".format(error))
            return False
