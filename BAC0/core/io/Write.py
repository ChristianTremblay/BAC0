#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Write.py - creation of WriteProperty requests

    Used while defining an app
    Example::

        class BasicScript(WhoisIAm, WriteProperty)

    Class::

        WriteProperty()
            def write()


"""
# --- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import (
    WritePropertyRequest,
    WritePropertyMultipleRequest,
    SimpleAckPDU,
    WriteAccessSpecification,
)

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real, Enumerated
from bacpypes.constructeddata import Array, Any, SequenceOf
from bacpypes.basetypes import PropertyValue, PropertyIdentifier
from bacpypes.iocb import IOCB
from bacpypes.core import deferred

# --- this application's modules ---
from .IOExceptions import (
    WritePropertyCastError,
    NoResponseFromController,
    WritePropertyException,
    WriteAccessDenied,
    ApplicationNotStarted,
)
from ...core.utils.notes import note_and_log
from .Read import find_reason

# ------------------------------------------------------------------------------

# some debugging
_debug = 0
_LOG = ModuleLogger(globals())


@note_and_log
class WriteProperty:
    """
    Defines BACnet Write functions: WriteProperty [WritePropertyMultiple not supported]

    """

    def write(self, args, vendor_id=0, timeout=10):
        """ Build a WriteProperty request, wait for an answer, and return status [True if ok, False if not].

        :param args: String with <addr> <type> <inst> <prop> <value> [ <indx> ] - [ <priority> ]
        :returns: return status [True if ok, False if not]

        *Example*::

            import BAC0
            bacnet = BAC0.lite()
            bacnet.write('2:5 analogValue 1 presentValue 100 - 8')

        Direct the controller at (Network 2, address 5) to write 100 to the presentValues of
        its analogValue 1 (AV:1) at priority 8
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")
        args = args.split()
        self.log_title("Write property", args)

        try:
            # build a WriteProperty request
            iocb = IOCB(self.build_wp_request(args, vendor_id=vendor_id))
            iocb.set_timeout(timeout)
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)
            self._log.debug("{:<20} {!r}".format("iocb", iocb))

        except WritePropertyException as error:
            # construction error
            self._log.exception("exception: {!r}".format(error))

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug(
                    "Not an ack. | APDU : {} / {}".format((apdu, type(apdu)))
                )
                return

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController("APDU Abort Reason : {}".format(reason))

    def _parse_wp_args(self, args):
        """
        Utility to parse the string of the request.
        Supports @obj_ and @prop_ syntax for objest type and property id, useful with proprietary objects and properties.
        """
        if not isinstance(args, list):
            args = args.split()
        obj_type, obj_inst, prop_id = args[:3]
        if obj_type.isdigit():
            obj_type = int(obj_type)
        elif "@obj_" in obj_type:
            obj_type = int(obj_type.split("_")[1])
        obj_inst = int(obj_inst)
        value = args[3]
        indx = None
        if len(args) >= 5 and args[4] != "-":
            indx = int(args[4])
        priority = None
        if len(args) >= 6:
            priority = int(args[5])
        if "@prop_" in prop_id:
            prop_id = prop_id.split("_")[1]
        if prop_id.isdigit():
            prop_id = int(prop_id)

        return (obj_type, obj_inst, prop_id, value, priority, indx)

    def _validate_value_vs_datatype(self, obj_type, prop_id, indx, vendor_id, value):
        """
        This will ensure the value can be encoded and is valid in the context
        """
        # get the datatype
        datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)
        # change atomic values into something encodeable, null is a special
        # case
        if value == "null":
            value = Null()
        elif issubclass(datatype, Atomic):
            if (
                datatype is Integer
                # or datatype is not Real
                or datatype is Unsigned
                or datatype is Enumerated
            ):
                value = int(value)
            elif datatype is Real:
                value = float(value)
                # value = datatype(value)
            else:
                # value = float(value)
                value = datatype(value)

            value = datatype(value)
        elif issubclass(datatype, Array) and (indx is not None):
            if indx == 0:
                value = Integer(value)
            elif issubclass(datatype.subtype, Atomic):
                value = datatype.subtype(value)
            elif not isinstance(value, datatype.subtype):
                raise TypeError(
                    "invalid result datatype, expecting {}".format(
                        (datatype.subtype.__name__,)
                    )
                )

        elif not isinstance(value, datatype):
            raise TypeError(
                "invalid result datatype, expecting {}".format((datatype.__name__,))
            )

        self._log.debug("{:<20} {!r} {}".format("Encodeable value", value, type(value)))

        _value = Any()
        try:
            _value.cast_in(value)
        except WritePropertyCastError as error:
            self._log.error("WriteProperty cast error: {!r}".format(error))
            raise

        return _value

    def build_wp_request(self, args, vendor_id=0):
        vendor_id = vendor_id
        addr = args[0]
        args = args[1:]
        obj_type, obj_inst, prop_id, value, priority, indx = self._parse_wp_args(args)

        value = self._validate_value_vs_datatype(
            obj_type, prop_id, indx, vendor_id, value
        )
        # build a request
        request = WritePropertyRequest(
            objectIdentifier=(obj_type, obj_inst), propertyIdentifier=prop_id
        )
        request.pduDestination = Address(addr)

        # save the value
        request.propertyValue = value

        # optional array index
        if indx is not None:
            request.propertyArrayIndex = indx

        # optional priority
        if priority is not None:
            request.priority = priority

        self.log_subtitle("Creating Request")
        self._log.debug(
            "{:<20} {:<20} {:<20} {:<20}".format(
                "indx", "priority", "datatype", "value"
            )
        )
        datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)

        self._log.debug(
            "{!r:<20} {!r:<20} {!r:<20} {!r:<20}".format(
                indx, priority, datatype, value
            )
        )

        self._log.debug("{:<20} {}".format("REQUEST", request))
        return request

    def writeMultiple(self, addr=None, args=None, vendor_id=0, timeout=10):
        """ Build a WritePropertyMultiple request, wait for an answer

        :param addr: destination of request (ex. '2:3' or '192.168.1.2')
        :param args: list of String with <type> <inst> <prop> <value> [ <indx> ] - [ <priority> ]
        :param vendor_id: Mandatory for registered proprietary object and properties
        :param timeout: used by IOCB to discard request if timeout reached
        :returns: return status [True if ok, False if not]

        *Example*::

            import BAC0
            bacnet = BAC0.lite()
            r = ['analogValue 1 presentValue 100','analogValue 2 presentValue 100','analogValue 3 presentValue 100 - 8','@obj_142 1 @prop_1042 True']
            bacnet.writeMultiple(addr='2:5',args=r,vendor_id=842)
            # or 
            # bacnet.writeMultiple('2:5',r)
            
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        self.log_title("Write property multiple", args)

        try:
            # build a WritePropertyMultiple request
            iocb = IOCB(self.build_wpm_request(args, vendor_id=vendor_id, addr=addr))
            iocb.set_timeout(timeout)
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)
            self._log.debug("{:<20} {!r}".format("iocb", iocb))

        except WritePropertyException as error:
            # construction error
            self._log.exception("exception: {!r}".format(error))

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug(
                    "Not an ack. | APDU : {} / {}".format((apdu, type(apdu)))
                )
                return

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController("APDU Abort Reason : {}".format(reason))

    def build_wpm_request(self, args, vendor_id=0, addr=None):
        if not addr:
            raise ValueError("Please provide addr")

        self.log_subtitle("Creating Write Multiple Request")
        self._log.debug(
            "{:<20} {:<20} {:<20} {:<20}".format(
                "indx", "priority", "datatype", "value"
            )
        )

        was = []
        for each in args:
            property_values = []
            if isinstance(each, str):
                obj_type, obj_inst, prop_id, value, priority, indx = self._parse_wp_args(
                    each
                )
            elif isinstance(each, tuple):
                # Supported but not really the best choice as the parser will
                # catch some edge cases for you
                obj_type, obj_inst, prop_id, value, priority, indx = each
            else:
                raise ValueError("Wrong encoding of request")
            value = self._validate_value_vs_datatype(
                obj_type, prop_id, indx, vendor_id, value
            )

            existingObject = next(
                (obj for obj in was if obj.objectIdentifier == (obj_type, obj_inst)),
                None,
            )

            if existingObject == None:
                property_values.append(
                    PropertyValue(
                        propertyIdentifier=prop_id,
                        propertyArrayIndex=indx,
                        value=value,
                        priority=priority,
                    )
                )

                was.append(
                    WriteAccessSpecification(
                        objectIdentifier=(obj_type, obj_inst),
                        listOfProperties=property_values,
                    )
                )
            else:
                existingObject.listOfProperties.append(
                    PropertyValue(
                        propertyIdentifier=prop_id,
                        propertyArrayIndex=indx,
                        value=value,
                        priority=priority,
                    )
                )

            datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)

            self._log.debug(
                "{!r:<20} {!r:<20} {!r:<20} {!r:<20}".format(
                    indx, priority, datatype, value
                )
            )

        # build a request
        request = WritePropertyMultipleRequest(listOfWriteAccessSpecs=was)
        request.pduDestination = Address(addr)

        self._log.debug("{:<20} {}".format("REQUEST", request))
        return request
