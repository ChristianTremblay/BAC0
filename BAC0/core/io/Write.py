#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module allows the creation of WriteProperty requests by and app

    Must be used while defining an app
    Example::
    
        class BasicScript(WhoisIAm, WriteProperty)
    
    Class::
    
        WriteProperty()
            def write()            
    
    Functions::

        print_debug()

"""
from bacpypes.debugging import bacpypes_debugging, ModuleLogger


from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import WritePropertyRequest

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real
from bacpypes.constructeddata import Array, Any

from queue import Empty

from .IOExceptions import WritePropertyException, WritePropertyCastError, NoResponseFromController

# some debugging
_debug = 0
_LOG = ModuleLogger(globals())

@bacpypes_debugging
class WriteProperty():
    """
    This class define function to write to bacnet objects
    Will implement a Queue object waiting for an acknowledgment
    """
    """
    This class defines functions to write to bacnet properties.
    It handles writeProperty
    Data exchange is made via a Queue object
    A timeout of 2 seconds allow detection of invalid device or communciation
    errors.
    """
    _TIMEOUT = 2
    
    def __init__(self):
        """ This function is a fake one so spyder can see local variables
        """
        self.this_application = None

    def write(self, args):
        """ This function build a write request wait for an acknowledgment and 
        return a boolean status (True if ok, False if not)
        
        :param args: String with <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]
        :returns: data read from device (str representing data like 10 or True)
        
        *Example*::
            
            import BAC0
            myIPAddr = '192.168.1.10'
            bacnet = BAC0.ReadWriteScript(localIPAddr = myIPAddr)          
            bacnet.write('2:5 analogValue 1 presentValue 100')
        
        will write 100 to AV:1 of a controller with a MAC address of 5 in the network 2
        """
        if not self._started: raise Exception('App not running, use startApp() function')
        args = args.split()
        print_debug("do_write %r", args)

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
            print_debug("    - indx: %r", indx)

            priority = None
            if len(args) >= 7:
                priority = int(args[6])
            print_debug("    - priority: %r", priority)

            # get the datatype
            datatype = get_datatype(obj_type, prop_id)
            print_debug("    - datatype: %r", datatype)

            # change atomic values into something encodeable, null is a special case
            if value == 'null':
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
            print_debug("    - encodeable value: %r %s", value, type(value))

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
            except WritePropertyCastError as error:
                WriteProperty._exception("WriteProperty cast error: %r", error)

            # optional array index
            if indx is not None:
                request.propertyArrayIndex = indx

            # optional priority
            if priority is not None:
                request.priority = priority

            print_debug("    - request: %r", request)

            # give it to the application
            self.this_application.request(request)

        except WritePropertyException as error:
            WriteProperty._exception("exception: %r", error)

        while True:
            try:
                data, evt = self.this_application.ResponseQueue.get(timeout=self._TIMEOUT)
                evt.set()
                return data
            except Empty:
                raise NoResponseFromController
                return None

def print_debug(msg, *args):
    """
    Used to print info to console when debug mode active
    """
    if _debug:
        WriteProperty._debug(msg, args)