#!/usr/bin/python

"""
Built around a simple BIPSimpleApplication this class allows to create read and write
requests and store read responses in a variables

For 'read' commands it will create ReadPropertyRequest PDUs, then lines up the
coorresponding ReadPropertyACK and return the value. 

For 'write' commands it will create WritePropertyRequst PDUs and prints out a simple acknowledgement.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.core import run as startBacnetIPApp
from bacpypes.core import stop as stopBacnetIPApp

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype

from bacpypes.apdu import Error, AbortPDU, SimpleAckPDU,ReadPropertyRequest, ReadPropertyACK, WritePropertyRequest, ReadPropertyMultipleRequest, PropertyReference, ReadAccessSpecification, ReadPropertyMultipleACK,WhoIsRequest, IAmRequest,UnconfirmedRequestPDU

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real
from bacpypes.constructeddata import Array, Any
from bacpypes.basetypes import ServicesSupported, PropertyIdentifier

from threading import Thread
import time
from collections import defaultdict
from bacnetScript.bacnetRead import ReadProperty
from bacnetScript.bacnetWrite import WriteProperty
from bacnetScript.bacnetScriptApplication import BacnetScriptApplication

# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class BacnetWhoisIAm():
    def __init__(self):
        self.this_application = None
           
    def whois(self, *args):
        """whois [ <addr>] [ <lolimit> <hilimit> ]"""
        if args:        
            args = args.split()
        if _debug: BacnetWhoisIAm._debug("do_whois %r" % args)

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
            if _debug: BacnetWhoisIAm._debug("    - request: %r" % request)

            # give it to the application
            self.this_application.request(request)

        except Exception as e:
            BacnetWhoisIAm._exception("exception: %r" % e)

        self.discoveredDevices = self.this_application.i_am_counter
      
        return self.discoveredDevices
        
#    def whois(self,*args):      
#        tools.printWhoisResult(self._whois(*args))
        

    def iam(self):
        """iam"""
        
        if _debug: BacnetWhoisIAm._debug("do_iam")

        try:
            # build a request
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = self.this_device.objectIdentifier
            request.maxAPDULengthAccepted = self.this_device.maxApduLengthAccepted
            request.segmentationSupported = self.this_device.segmentationSupported
            request.vendorID = self.this_device.vendorIdentifier
            if _debug: BacnetWhoisIAm._debug("    - request: %r" % request)

            # give it to the application
            self.this_application.request(request)
            return True

        except Exception as e:
            BacnetWhoisIAm._exception("exception: %r" % e)
            return False

