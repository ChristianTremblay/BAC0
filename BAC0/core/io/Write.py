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
#--- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real
from bacpypes.constructeddata import Array, Any
from bacpypes.iocb import IOCB
from bacpypes.core import deferred

#--- this application's modules ---
from .IOExceptions import WritePropertyCastError, NoResponseFromController, WritePropertyException, WriteAccessDenied, ApplicationNotStarted
from ...core.utils.notes import note_and_log

#------------------------------------------------------------------------------

# some debugging
_debug = 0
_LOG = ModuleLogger(globals())


@note_and_log
class WriteProperty():
    """
    Defines BACnet Write functions: WriteProperty [WritePropertyMultiple not supported]

    """

    def write(self, args, vendor_id=0):
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
            raise ApplicationNotStarted(
                'BACnet stack not running - use startApp()')
        args = args.split()
        self.log_title("Write property",args)

        try:
            # build a WriteProperty request
            iocb = IOCB(self.build_wp_request(args, vendor_id=vendor_id))
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)
            self._log.debug("{:<20} {!r}".format('iocb', iocb))

        except WritePropertyException as error:
            # construction error
            self._log.exception("exception: {!r}".format(error))

        iocb.wait()             # Wait for BACnet response

        if iocb.ioResponse:     # successful response
            apdu = iocb.ioResponse
            
            if not isinstance(iocb.ioResponse, SimpleAckPDU):   # expect an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug("Not an ack. | APDU : {} / {}".format((apdu, type(apdu))))
                return

        if iocb.ioError:        # unsuccessful: error/reject/abort
            raise NoResponseFromController()

    def build_wp_request(self, args, vendor_id=0):
        addr, obj_type, obj_inst, prop_id = args[:4]
        vendor_id = vendor_id
        if obj_type.isdigit():
            obj_type = int(obj_type)
        obj_inst = int(obj_inst)
        value = args[4]

        indx = None
        if len(args) >= 6:
            if args[5] != "-":
                indx = int(args[5])

        priority = None
        if len(args) >= 7:
            priority = int(args[6])

        # get the datatype
        if prop_id.isdigit():
            prop_id = int(prop_id)
        datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)

        self.log_subtitle("Creating Request")
        self._log.debug(
                "{:<20} {:<20} {:<20} {:<20}".format(
                'indx',
                'priority',
                'datatype',
                'value'))
        self._log.debug(
                "{!r:<20} {!r:<20} {!r:<20} {!r:<20}".format(
                indx,
                priority,
                datatype,
                value
                ))
        
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
                    "invalid result datatype, expecting {}".format(
                        (datatype.subtype.__name__,)))

        elif not isinstance(value, datatype):
            raise TypeError(
                "invalid result datatype, expecting {}".format(
                    (datatype.__name__,)))
        self._log.debug("{:<20} {!r} {}".format(
            "Encodeable value", value, type(value)))

        # build a request
        request = WritePropertyRequest(objectIdentifier=(obj_type, obj_inst),
                                       propertyIdentifier=prop_id)
        request.pduDestination = Address(addr)

        # save the value
        request.propertyValue = Any()
        try:
            request.propertyValue.cast_in(value)
        except WritePropertyCastError as error:
            self._log.error("WriteProperty cast error: {!r}".format(error))

        # optional array index
        if indx is not None:
            request.propertyArrayIndex = indx

        # optional priority
        if priority is not None:
            request.priority = priority

        self._log.debug("{:<20} {}".format("REQUEST", request))
        return request
