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

import time


# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class WriteProperty():
    def __init__(self):
        self.this_application = None
    
    def write(self, args):
        """write <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]"""
        if not self._started : raise Exception('App not running, use startApp() function')
        args = args.split()
        WriteProperty._debug("do_write %r", args)

        try:
            addr, obj_type, obj_inst, prop_id = args[:4]
            if obj_type.isdigit():
                obj_type = int(obj_type)
            obj_inst = int(obj_inst)
            value = args[4]

            indx = None
            if len(args) >= 6:
                if args[5] != "-":
                    indx = int(args[5])
            if _debug: WriteProperty._debug("    - indx: %r", indx)

            priority = None
            if len(args) >= 7:
                priority = int(args[6])
            if _debug: WriteProperty._debug("    - priority: %r", priority)

            # get the datatype
            datatype = get_datatype(obj_type, prop_id)
            if _debug: WriteProperty._debug("    - datatype: %r", datatype)

            # change atomic values into something encodeable, null is a special case
            if (value == 'null'):
                value = Null()
            elif issubclass(datatype, Atomic):
                if datatype is Integer:
                    value = int(value)
                elif datatype is Real:
                    value = float(value)
                elif datatype is Unsigned:
                    value = int(value)
                value = datatype(value)
            elif issubclass(datatype, Array) and (indx is not None):
                if indx == 0:
                    value = Integer(value)
                elif issubclass(datatype.subtype, Atomic):
                    value = datatype.subtype(value)
                elif not isinstance(value, datatype.subtype):
                    raise TypeError("invalid result datatype, expecting %s" % (datatype.subtype.__name__,))
            elif not isinstance(value, datatype):
                raise TypeError("invalid result datatype, expecting %s" % (datatype.__name__,))
            if _debug: WriteProperty._debug("    - encodeable value: %r %s", value, type(value))

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id
                )
            request.pduDestination = Address(addr)

            # save the value
            request.propertyValue = Any()
            try:
                request.propertyValue.cast_in(value)
            except Exception as e:
                WriteProperty._exception("WriteProperty cast error: %r", e)

            # optional array index
            if indx is not None:
                request.propertyArrayIndex = indx

            # optional priority
            if priority is not None:
                request.priority = priority

            if _debug: WriteProperty._debug("    - request: %r", request)

            # give it to the application
            self.this_application.request(request)

        except Exception as e:
            WriteProperty._exception("exception: %r", e)
 