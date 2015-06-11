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
from bacnetScript.bacnetBasicApp import BacnetBasicApp
from bacnetScript.bacnetDiscoverPoints import *


# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class BacnetScript(BacnetBasicApp,ReadProperty,WriteProperty):
    """ 
    This class build a running bacnet application and will accept read ans write requests
    
    """
    def __init__(self, localIPAddr = '127.0.0.1', localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorID = '15' ):
        """
        Initialization requires information on the local device
        Default values are localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorID = '15' )
        Local IP address must be given in a string.
        Normally, the address must be in the same subnet than the bacnet network (if no BBMD or Foreign device is used)        
        """     
        if _debug: _log.debug("Configurating app")
        BacnetBasicApp.__init__(self, localIPAddr = localIPAddr, localObjName = localObjName, Boid = Boid,maxAPDULengthAccepted = maxAPDULengthAccepted,segmentationSupported = segmentationSupported, vendorID = vendorID )
        
        # Force and gloab whois to find all devices on the network
        self.whois()
   
    def discover(self,addr):     
        discoverPoints(self,addr)
            
            
#
#   __main__
#
if __name__ == '__main__':
    bacnet = BacnetScript(localIPAddr = '192.168.210.63')




