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
import re

from bacpypes3.apdu import (
    ErrorRejectAbortNack,
)
from bacpypes3.app import Application
from bacpypes3.basetypes import PropertyIdentifier

# --- 3rd party modules ---
from bacpypes3.debugging import ModuleLogger
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier, Null

from BAC0.tasks.DoOnce import DoOnce

from ..app.asyncApp import BAC0Application
from ..utils.notes import note_and_log

# --- this application's modules ---
from .IOExceptions import (
    ApplicationNotStarted,
    NoResponseFromController,
    WritePropertyException,
)

# ------------------------------------------------------------------------------

# some debugging
_debug = 0
_LOG = ModuleLogger(globals())
WRITE_REGEX = r"(?P<address>\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d+)?\b|(\b\d+:\d+\b)) (?P<objId>(@obj_)?[-\w:]*[: ]*\d*) (?P<propId>(@prop_)?\w*(-\w*)?)[ ]?(?P<value>-*\w*)?[ ]?(?P<indx>-|\d*)?[ ]?(?P<priority>(1[0-6]|[0-9]))?"
write_pattern = re.compile(WRITE_REGEX)


@note_and_log
class WriteProperty:
    """
    Defines BACnet Write functions: WriteProperty [WritePropertyMultiple not supported]

    """

    def write(self, args, vendor_id=0, timeout=10):
        # asyncio.create_task(
        #    self._write(args=args, vendor_id=vendor_id, timeout=timeout)
        # )
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self._write(args=args, vendor_id=vendor_id, timeout=timeout))
        write_task = DoOnce((self._write, [args, vendor_id, timeout]))
        write_task.start()

    async def _write(self, args, vendor_id=0, timeout=10):
        """Build a WriteProperty request, wait for an answer, and return status [True if ok, False if not].

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

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        self.log_title("Write property", args)

        (
            device_address,
            object_identifier,
            property_identifier,
            value,
            property_array_index,
            priority,
        ) = self.build_wp_request(args)

        try:
            response = await _app.write_property(
                device_address,
                object_identifier,
                property_identifier,
                value,
                property_array_index,
                priority,
            )

        except ErrorRejectAbortNack as err:
            self.log(f"exception: {err!r}", level="error")
            raise NoResponseFromController(f"APDU Abort Reason : {response}")

        except ValueError as err:
            self.log(f"exception: {err!r}", level="error")
            raise ValueError(f"Invalid value for property : {err} | {response}")

        except WritePropertyException as error:
            # construction error
            self._log.exception(f"exception: {error!r}")

    @classmethod
    def _parse_wp_args(cls, args):
        """
        Utility to parse the string of the request.
        Supports @obj_ and @prop_ syntax for objest type and property id, useful with proprietary objects and properties.
        """
        global write_pattern
        match = write_pattern.search(args)
        try:
            address = match.group("address")
            objId = match.group("objId")
            prop_id = match.group("propId")
            value = match.group("value")
            indx = match.group("indx")
            priority = match.group("priority")
        except AttributeError:
            raise ValueError(f"Invalid request | {args}")
        if ":" in objId:
            obj_type, obj_inst = objId.split(":")
        else:
            obj_type, obj_inst = objId.split(" ")
        if obj_type.isdigit():
            obj_type = int(obj_type)
        elif "@obj_" in obj_type:
            obj_type = int(obj_type.split("_")[1])
        obj_inst = int(obj_inst)
        if "@prop_" in prop_id:
            prop_id = prop_id.split("_")[1]
        if prop_id.isdigit():
            prop_id = int(prop_id)

        value = Null(()) if value == "null" else value
        indx = None if indx == "-" or indx is None or indx == "" else int(indx)
        priority = None if priority is None else int(priority)

        return (address, obj_type, obj_inst, prop_id, value, priority, indx)

    def build_wp_request(self, args, vendor_id=0):
        vendor_id = vendor_id
        (
            address,
            obj_type,
            obj_inst,
            prop_id,
            value,
            priority,
            indx,
        ) = WriteProperty._parse_wp_args(args)

        object_identifier = ObjectIdentifier((obj_type, obj_inst))
        property_identifier = PropertyIdentifier(prop_id)
        device_address = Address(address)

        request = (
            device_address,
            object_identifier,
            property_identifier,
            value,
            indx,
            priority,
        )

        self.log_subtitle("Creating Request")
        self.log(
            f"{'indx':<20} {'priority':<20} {'datatype':<20} {'value':<20}",
            level="debug",
        )

        self.log(f"{'REQUEST':<20} {request}", level="debug")
        return request


'''
    def writeMultiple(self, addr=None, args=None, vendor_id=0, timeout=10):
        """Build a WritePropertyMultiple request, wait for an answer

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
            self.log(f"{'iocb':<20} {iocb!r}", level='debug')

        except WritePropertyException as error:
            # construction error
            self._log.exception(f"exception: {error!r}")

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self.log("Not an ack, see debug for more infos.", level='warning')
                self.log(f"Not an ack. | APDU : {apdu} / {type(apdu)}", level='debug')
                return

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController(f"APDU Abort Reason : {reason}")

    def build_wpm_request(self, args, vendor_id=0, addr=None):
        if not addr:
            raise ValueError("Please provide addr")

        address = Address(addr)

        self.log_subtitle("Creating Write Multiple Request")
        self.log(f"{'indx':<20} {'priority':<20} {'datatype':<20} {'value':<20}", level='debug')

        was = []
        listOfObjects = []
        for each in args:
            property_values = []
            if isinstance(each, str):
                (
                    object_identifier,
                    property_identifier,
                    value,
                    priority,
                    indx,
                ) = self._parse_wp_args(each)
            elif isinstance(each, tuple):
                # Supported but not really the best choice as the parser will
                # catch some edge cases for you
                object_identifier, property_identifier, value, priority, indx = each
            else:
                raise ValueError("Wrong encoding of request")

            existingObject = next(
                (obj for obj in was if obj.objectIdentifier == (obj_type, obj_inst)),
                None,
            )

            if existingObject is None:
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
                f"{indx!r:<20} {priority!r:<20} {datatype!r:<20} {value!r:<20}"
            )

        # build a request
        request = WritePropertyMultipleRequest(listOfWriteAccessSpecs=was)
        request.pduDestination = Address(addr)

        self.log(f"{'REQUEST':<20} {request}", level='debug')
        return request
'''
