#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Write.py - creation of WriteProperty requests

    Used while defining an app
    Example::

        class BasicScript(WhoisIAm, WriteProperty)

    Class::

        WriteProperty()
            def write()

    Functions::

        print_debug()

'''
#--- standard Python modules ---
from queue import Empty
import time

#--- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real
from bacpypes.constructeddata import Array, Any
from bacpypes.iocb import IOCB

#--- this application's modules ---
from .IOExceptions import WritePropertyCastError, NoResponseFromController, WritePropertyException, WriteAccessDenied, ApplicationNotStarted
from ..functions.debug import log_debug, log_exception


#------------------------------------------------------------------------------

# some debugging
_debug = 0
_LOG = ModuleLogger(globals())


@bacpypes_debugging
class WriteProperty():
    """
    Defines BACnet Write functions: WriteProperty [WritePropertyMultiple not supported]

    A timeout of 10 seconds allows detection of invalid device or communciation errors.
    """
    _TIMEOUT = 10


    def write(self, args):
        """ Build a WriteProperty request, wait for an answer, and return status [True if ok, False if not].

        :param args: String with <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10'
            bacnet = BAC0.ReadWriteScript(localIPAddr = myIPAddr)
            bacnet.write('2:5 analogValue 1 presentValue 100')

        Direct the controller at (Network 2, address 5) to write 100 to the presentValues of 
        its analogValue 1 (AV:1)
        """
        if not self._started:
            raise ApplicationNotStarted('BACnet stack not running - use startApp()')
        #with self.this_application._lock:
        #    time.sleep(0.5)
        #self.this_application._lock = True
        args = args.split()
        log_debug(WriteProperty, "do_write %r", args)

        try:
            iocb = IOCB(self.build_wp_request(args))            # build a WriteProperty request
            self.this_application.request_io(iocb)              # pass to the BACnet stack

        except WritePropertyException as error:
            log_exception("exception: %r", error)               # construction error


        iocb.wait()             # Wait for BACnet response

        if iocb.ioResponse:     # successful response
            if not isinstance(iocb.ioResponse, SimpleAckPDU):   # expect an ACK
                log_debug(WriteProperty,"    - not an ack")
                return

        if iocb.ioError:        # unsuccessful: error/reject/abort
            raise NoResponseFromController()  

#            while True:
#                try:
#                    data, evt = self.this_application.ResponseQueue.get(
#                        timeout=self._TIMEOUT)
#                    evt.set()
#                    #self.this_application._lock = False
#                    return data
#                except Empty:
#                    #self.this_application._lock = False
#                    raise NoResponseFromController
                

    def build_wp_request(self, args):
        addr, obj_type, obj_inst, prop_id = args[:4]
        if obj_type.isdigit():
            obj_type = int(obj_type)
        obj_inst = int(obj_inst)
        value = args[4]

        indx = None
        if len(args) >= 6:
            if args[5] != "-":
                indx = int(args[5])
        log_debug(WriteProperty, "    - indx: %r", indx)

        priority = None
        if len(args) >= 7:
            priority = int(args[6])
        log_debug(WriteProperty, "    - priority: %r", priority)

        # get the datatype
        datatype = get_datatype(obj_type, prop_id)
        log_debug(WriteProperty, "    - datatype: %r", datatype)

        # change atomic values into something encodeable, null is a special
        # case
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
                raise TypeError(
                    "invalid result datatype, expecting %s" %
                    (datatype.subtype.__name__,))

        elif not isinstance(value, datatype):
            raise TypeError(
                "invalid result datatype, expecting %s" %
                (datatype.__name__,))
        log_debug(
            WriteProperty,
            "    - encodeable value: %r %s",
            value,
            type(value))

        # build a request
        request = WritePropertyRequest(
            objectIdentifier=(obj_type, obj_inst), propertyIdentifier=prop_id )
        request.pduDestination = Address(addr)

        # save the value
        request.propertyValue = Any()
        try:
            request.propertyValue.cast_in(value)
        except WritePropertyCastError as error:
            log_exception("WriteProperty cast error: %r", error)

        # optional array index
        if indx is not None:
            request.propertyArrayIndex = indx

        # optional priority
        if priority is not None:
            request.priority = priority

        log_debug(WriteProperty, "    - request: %r", request)
        return request
