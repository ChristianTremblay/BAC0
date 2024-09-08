#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Read.py - creation of ReadProperty and ReadPropertyMultiple requests

    Used while defining an app:
    Example::

        class BasicScript(WhoisIAm, ReadProperty)

    Class::

        ReadProperty()
            def read()
            def readMultiple()

"""

import re

# --- standard Python modules ---
import typing as t

# from bacpypes3.core import deferred
# from bacpypes.iocb import IOCB, TimeoutError
# from bacpypes3.object import get_object_class, registered_object_types
from bacpypes3.apdu import (
    AbortPDU,
    AbortReason,
    ErrorRejectAbortNack,
    PropertyReference,
    Range,
    ReadAccessSpecification,
    ReadPropertyMultipleRequest,
    ReadRangeACK,
    ReadRangeRequest,
    RejectPDU,
    RejectReason,
)
from bacpypes3.app import Application
from bacpypes3.basetypes import (
    DateTime,
    PropertyIdentifier,
    RangeByPosition,
    RangeBySequenceNumber,
    RangeByTime,
)
from bacpypes3.errors import NoResponse, ObjectError
from bacpypes3.object import get_vendor_info

# --- 3rd party modules ---
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Date, ObjectIdentifier, Tag, Time

from BAC0.core.app.asyncApp import BAC0Application

from ..utils.notes import note_and_log

# --- this application's modules ---
from .IOExceptions import (
    ApplicationNotStarted,
    NoResponseFromController,
    ReadRangeException,
    SegmentationNotSupported,
    UnknownObjectError,
    UnknownPropertyError,
    UnrecognizedService,
)

# ------------------------------------------------------------------------------


ReadValue = t.Union[float, str, t.List]
rpm_request_pattern = r"(?P<request>(?P<Object>[0-9A-Za-z-]+:\d+)[, ]+[(\[ ](?P<Properties>(?P<Property>[0-9A-Za-z-]+(\[\d+\])*[, ]*)+)[)\]]*)"


@note_and_log
class ReadProperty:
    """
    Defines BACnet Read functions: readProperty and readPropertyMultiple.
    Data exchange is made via a Queue object
    A timeout of 10 seconds allows detection of invalid device or communciation errors.
    """

    async def read(
        self,
        args: str,
        arr_index: t.Optional[int] = None,
        vendor_id: int = 0,
        bacoid=None,
        timeout: int = 10,
        show_property_name: bool = False,
    ) -> t.Union[ReadValue, t.Tuple[ReadValue, str], None]:
        """
        Build a ReadProperty request, wait for the answer and return the value

        :param args: String with <addr> <type> <inst> <prop> [ <indx> ]
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10/24'
            bacnet = BAC0.connect(ip = myIPAddr)
            bacnet.read('2:5 analogInput 1 presentValue')

        Requests the controller at (Network 2, address 5) for the presentValue of
        its analog input 1 (AI:1).
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        args_split = args.split()

        (
            device_address,
            object_identifier,
            property_identifier,
            property_array_index,
        ) = self.build_rp_request(
            args_split, arr_index=arr_index, vendor_id=vendor_id, bacoid=bacoid
        )

        self.log_title("Read property", args_split)
        # Do I know you ?
        dic = await self.this_application.app.device_info_cache.get_device_info(
            device_address
        )
        if dic is None:
            _iam = await self.this_application.app.who_is(address=device_address)
            try:
                await self.this_application.app.device_info_cache.set_device_info(
                    _iam[0]
                )
            except IndexError:
                self.log(
                    f"Trouble with Iam... Response received from {device_address} = {_iam}",
                    level="error",
                )
                if _iam == []:
                    raise NoResponseFromController
            dic = await self.this_application.app.device_info_cache.get_device_info(
                device_address
            )
            self.log(f"Device Info Cache : {dic}", level="debug")
        try:
            response = await _app.read_property(
                device_address,
                object_identifier,
                property_identifier,
                property_array_index,
            )

        except ErrorRejectAbortNack as err:
            response = err

            if "unknown-property" in str(err.reason):
                if "description" in args:
                    self._log.warning(
                        "The description property is not implemented in the device. "
                        "Using a default value for internal needs."
                    )
                    return "n/a"
                elif "inactiveText" in args:
                    self._log.warning(
                        "The inactiveText property is not implemented in the device. "
                        "Using a default value of Off for internal needs."
                    )
                    return "False"
                elif "activeText" in args:
                    self._log.warning(
                        "The activeText property is not implemented in the device. "
                        "Using a default value of On for internal needs."
                    )
                    return "True"
                else:
                    raise UnknownPropertyError(f"Unknown property {args}")
            else:
                self.log(f"Error : {err}", level="error")
        except ObjectError:
            raise UnknownObjectError(f"Unknown object {args}")

        # except bufferOverflow
        except NoResponse:
            raise NoResponseFromController

        if not isinstance(response, ErrorRejectAbortNack):
            return response

    def _split_the_read_request(self, args, arr_index):
        """
        When a device doesn't support segmentation, this function
        will split the request according to the length of the
        predicted result which can be known when reading the array_index
        number 0.

        This can be a very long process as some devices count a large
        number of properties without supporting segmentation
        (FieldServers are a good example)
        """
        # parameter arr_index appears to be unused in this function?
        nmbr_obj = self.read(args, arr_index=0)
        return [self.read(args, arr_index=i) for i in range(1, nmbr_obj + 1)]  # type: ignore

    async def readMultiple(
        self,
        args: str,
        request_dict=None,
        vendor_id: int = 0,
        timeout: int = 10,
        show_property_name: bool = False,
        from_regex=False,
    ) -> t.Union[t.Dict, t.List[t.Tuple[t.Any, str]]]:
        """Build a ReadPropertyMultiple request, wait for the answer and return the values

        :param args: String with <addr> ( <type> <inst> ( <prop> [ <indx> ] )... )...
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10/24'
            bacnet = BAC0.connect(ip = myIPAddr)
            bacnet.readMultiple('2:5 analogInput 1 presentValue units')

        Requests the controller at (Network 2, address 5) for the (presentValue and units) of
        its analog input 1 (AI:1).
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        if request_dict is not None:
            address, parameter_list = await self.build_rpm_request_from_dict(
                request_dict, vendor_id
            )
        elif from_regex:
            address, parameter_list = await self.build_rpm_request_from_regex(
                args, vendor_id=vendor_id
            )
            self.log_title(f"Read Multiple for {address} | params : {parameter_list}")

        else:
            args_list = args.split()
            address, parameter_list = await self.build_rpm_request(
                args_list, vendor_id=vendor_id
            )
            self.log_title("Read Multiple", args_list)

        # Force DeviceInfoCache
        dic = await self.this_application.app.device_info_cache.get_device_info(address)
        if dic is None:
            _iam = await self.this_application.app.who_is(address=address)
            await self.this_application.app.device_info_cache.set_device_info(_iam[0])
            dic = await self.this_application.app.device_info_cache.get_device_info(
                address
            )
            self.log(f"Device Info Cache : {dic}", level="debug")

        values = []
        dict_values = {}

        self.log(f"Parameter list : {parameter_list}", level="debug")

        try:
            # build an ReadPropertyMultiple request
            response = await _app.read_property_multiple(address, parameter_list)
            self.log(f"Response : {response}", level="debug")

        except ErrorRejectAbortNack as err:
            # construction error
            response = err
            self._log.exception(f"exception: {err.reason}")
            if "segmentation-not-supported" in str(err.reason):
                raise SegmentationNotSupported
            if "unrecognized-service" in str(err.reason):
                raise UnrecognizedService()
            if "unknown-object" in str(err.reason):
                self.log(f"Unknown object {args}", level="warning")
                raise UnknownObjectError(f"Unknown object {args}")
            if "unknown-property" in str(err.reason):
                values.append("")  # type: ignore[arg-type]
                return values
            if "no-response" in str(err.reason):
                values.append("")  # type: ignore[arg-type]
                return values

        if not isinstance(response, ErrorRejectAbortNack):
            """
            TODO : Need improvement here and look for the property identifier that is coming from the response
            Then we'll be able to support multiple properties for the same object in the read multiple function
            """
            for (
                object_identifier,
                property_identifier,
                property_array_index,
                property_value,
            ) in response:
                self._log.debug(
                    "{!r:<20} {!r:<20} {!r:<30} {!r:<20}".format(
                        property_identifier,
                        property_array_index,
                        property_value,
                        # datatype,
                        "",
                    )
                )
                dict_values[str(object_identifier)] = []
                if show_property_name:
                    values.append((property_value, property_identifier))
                    dict_values[str(object_identifier)].append(
                        (property_identifier, (property_value, property_identifier))
                    )
                else:
                    values.append(property_value)
                    dict_values[str(object_identifier)].append(
                        (property_identifier, property_value)
                    )

            if request_dict is not None:
                return dict_values
            else:
                return values

        return values

    def build_rp_request(
        self, args: t.List[str], arr_index=None, vendor_id: int = 0, bacoid=None
    ) -> t.Tuple:
        vendor = get_vendor_info(vendor_id)
        try:
            addr, obj_type_str, obj_inst_str, prop_id_str = args[:4]
            object_identifier = ObjectIdentifier((obj_type_str, int(obj_inst_str)))
        except ValueError:
            addr, obj_type_str, prop_id_str = args[:3]
            object_identifier = ObjectIdentifier(obj_type_str)

        device_address = Address(addr)

        # TODO : This part needs work to find proprietary objects
        # obj_type = self.__get_obj_type(obj_type_str, vendor_id)

        if prop_id_str.isdigit():
            prop_id = int(prop_id_str)
        elif "@prop_" in prop_id_str or "@idx" in prop_id_str:
            if "@idx" in prop_id_str:
                prop_id, arr_index = prop_id_str.split("@idx:")
            if "@prop_" in prop_id_str:
                prop_id = int(prop_id_str.split("_")[1])
        else:
            prop_id = prop_id_str  # type: ignore
        prop_id = PropertyIdentifier(prop_id)

        if arr_index is None:
            arr_index = int(args[4]) if len(args) == 5 else arr_index
        params = (device_address, object_identifier, prop_id, arr_index)
        self.log(f"{'REQUEST':<20} {params!r}", level="debug")
        return params

    async def build_rpm_request(
        self, args: t.List[str], vendor_id: int = 0
    ) -> ReadPropertyMultipleRequest:
        """
        Build request from args
        """
        property_array_index = None
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        self.log(args, level="debug")

        vendor_id = vendor_id
        address = Address(args.pop(0))
        # get information about the device from the cache
        device_info = await _app.device_info_cache.get_device_info(address)

        # using the device info, look up the vendor information
        if device_info:
            vendor_info = get_vendor_info(device_info.vendor_identifier)
        else:
            vendor_info = get_vendor_info(vendor_id)

        parameter_list = []
        while args:
            # get the object identifier and using the vendor information, look
            # up the class
            obj_id = args.pop(0)
            if obj_id.isdigit():
                obj_id = int(obj_id)
            elif "@obj_" in obj_id:
                obj_id = int(obj_id.split("@obj_")[1])
            if ":" not in str(obj_id):
                obj_instance = args.pop(0)
            else:
                obj_instance = obj_id.split(":")[1]
                obj_id = obj_id.split(":")[0]
            object_identifier = vendor_info.object_identifier((obj_id, obj_instance))
            object_class = vendor_info.get_object_class(object_identifier[0])
            if not object_class:
                await self.response(f"unrecognized object type: {object_identifier}")
                return

            properties_list = []
            while args:
                # now get the property type from the class
                if "@obj_" in args[0]:
                    break
                elif "@prop_" in args[0] or "@idx" in args[0]:
                    if "@idx" in args[0]:
                        prop_id, arr_index = args.pop(0).split("@idx_")
                    else:
                        prop_id = int(args.pop(0).split("prop_")[1])
                else:
                    prop_id = args.pop(0)
                try:
                    property_identifier = vendor_info.property_identifier(prop_id)
                except ValueError:
                    try:
                        property_identifier = PropertyIdentifier(prop_id)
                    except ValueError:
                        break  # probably another object

                if property_identifier not in (
                    PropertyIdentifier.all,
                    PropertyIdentifier.required,
                    PropertyIdentifier.optional,
                    # "objectName",
                    # "objectType",
                    # "objectIdentifier",
                    # "polarity",
                ):
                    property_type = object_class.get_property_type(property_identifier)
                    if not property_type:
                        await _app.response(
                            f"unrecognized property: {property_identifier}"
                        )
                        return

                # check for a property array index
                if args and args[0].isdigit() and arr_index is None:
                    property_array_index = int(args.pop(0))
                    # save this as a parameter
                    properties_list.append((property_identifier, property_array_index))
                elif property_array_index is not None:
                    properties_list.append((property_identifier, arr_index))
                else:
                    properties_list.append(property_identifier)

                # crude check to see if the next thing is an object identifier
                if args and ((":" in args[0]) or ("," in args[0]) or ("-" in args[0])):
                    break
            parameter_list.append(object_identifier)
            parameter_list.append(properties_list)

        if not parameter_list:
            await _app.response("object identifier expected")
            return
        else:
            return (address, parameter_list)

    async def build_rpm_request_from_regex(self, args, vendor_id=0):
        pattern = re.compile(rpm_request_pattern)
        address = Address(args.split()[0])

        result = re.findall(pattern, args)
        request = []
        for each in result:
            _, object_identifier, properties, _, _ = each
            request.append(ObjectIdentifier(object_identifier))
            request.append([PropertyReference(x) for x in properties.split()])
        self.log(f"RPM Request from Regex : {address} | {request}", level="debug")
        return (address, request)

    async def build_rpm_request_from_dict(self, request_dict, vendor_id=0):
        """
        Read property multiple allow to read a lot of properties with only one request
        The existing RPM function is made using a string that must be created using bacpypes
        console style and is hard to automate.

        This new version will be an attempt to improve that::

            _rpm = {'address': '11:2',
                'objects': {'analogInput:1': ['presentValue', 'description', 'unit', 'objectList@idx:0'],
                            'analogInput:2': ['presentValue', 'description', 'unit', 'objectList@idx:0'],
                },
                vendor_id: 842
                }

        """

        vendor_id = vendor_id
        address = Address(request_dict["address"])
        objects = request_dict["objects"]
        if "vendor_id" in request_dict.keys():
            vendor_id = int(request_dict["vendor_id"])

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        # get information about the device from the cache
        device_info = await _app.device_info_cache.get_device_info(address)

        # using the device info, look up the vendor information
        if device_info:
            vendor_info = get_vendor_info(device_info.vendor_identifier)
        else:
            vendor_info = get_vendor_info(0)

        parameter_list = []
        arr_index = None

        for obj, list_of_properties in objects.items():
            object_identifier = ObjectIdentifier(obj)
            properties_list = []
            for each in list_of_properties:
                if "@obj_" in each:
                    break
                elif "@prop_" in each or "@idx" in each:
                    if "@idx_" in each:
                        prop_id, arr_index = each.split("@idx_")
                    else:
                        prop_id = int(each.split("@prop_")[1])  # there was no idx
                else:
                    prop_id = each
                property_identifier = vendor_info.property_identifier(prop_id)

                if arr_index:
                    properties_list.append(property_identifier, arr_index)
                else:
                    properties_list.append(property_identifier)
            parameter_list.append(object_identifier)
            parameter_list.append(properties_list)

        if not parameter_list:
            await _app.response("object identifier expected")
            return

        return (address, parameter_list)

    def build_rrange_request(
        self, args, range_params=None, arr_index=None, vendor_id=0, bacoid=None
    ):
        addr, obj_type, obj_inst, prop_id = args[:4]

        vendor_id = vendor_id
        bacoid = bacoid

        if obj_type.isdigit():
            obj_type = int(obj_type)

        obj_inst = int(obj_inst)

        if prop_id.isdigit():
            prop_id = int(prop_id)

        # build a request
        request = ReadRangeRequest(
            objectIdentifier=(obj_type, obj_inst), propertyIdentifier=prop_id
        )
        request.pduDestination = Address(addr)
        if range_params is not None:
            range_type, first, date, time, count = range_params
            if range_type == "p":
                rbp = RangeByPosition(referenceIndex=int(first), count=int(count))
                request.range = Range(byPosition=rbp)
            elif range_type == "s":
                rbs = RangeBySequenceNumber(
                    referenceSequenceNumber=int(first), count=int(count)
                )
                request.range = Range(bySequenceNumber=rbs)
            elif range_type == "t":
                rbt = RangeByTime(
                    referenceTime=DateTime(date=Date(date), time=Time(time)),
                    count=int(count),
                )
                request.range = Range(byTime=rbt)
            elif range_type == "x":
                # should be missing required parameter
                request.range = Range()
            else:
                raise ValueError(f"unknown range type: {range_type!r}")

        if len(args) == 5:
            request.propertyArrayIndex = int(args[4])
        self.log(f"{'REQUEST':<20} {request!r}", level="debug")
        return request

    async def readRange(
        self,
        args,
        range_params=None,
        arr_index=None,
        vendor_id=0,
        bacoid=None,
        timeout=10,
    ):
        """
        Build a ReadRangeRequest request, wait for the answer and return the value

        :param args: String with <addr> <type> <inst> <prop> [ <indx> ]
        :param range_params: parameters defining how to query the range, a list of five elements
        :returns: data read from device (list of LogRecords)

        range_params: a list of five elements: (range_type: str, first: int, date: str, time: str, count: int)
            range_type: one of ['p', 's', 't']
                        p - RangeByPosition:
                                uses (first, count)
                        s - RangeBySequenceNumber:
                                uses (first, count)
                        t - RangeByTime: Filter by the given time
                                uses (date, time, count)
            first: int, first element when querying by Position or Sequence Number
            date: str, "YYYY-mm-DD" passed to bacpypes.primitivedata.Date constructor
            time: str, "HH:MM:SS" passed to bacpypes.primitivedata.Time constructor
            count: int, number of elements to return, negative numbers reverse direction of search

        *Example*::

            import BAC0
            from bacpypes.basetypes import Date, Time
            myIPAddr = '192.168.1.10/24'
            bacnet = BAC0.connect(ip=myIPAddr)

            log_records = bacnet.readRange('2:5 trendLog 1 logBuffer', range_params=('t', None, '2023-05-12', '12:00:00', 2))
            for log_record in log_records:
              print(Date(log_record.timestamp.date), Time(log_record.timestamp.time), log_record.logDatum.realValue)
            # Date(2023-5-12 fri) Time(12:10:00.00) 130.331
            # Date(2023-5-12 fri) Time(12:20:00.00) 134.123

            log_records = bacnet.readRange('2:5 trendLog 1 logBuffer', range_params=('t', None, '2023-05-12', '12:00:00', -2))
            for log_record in log_records:
              print(Date(log_record.timestamp.date), Time(log_record.timestamp.time), log_record.logDatum.realValue)
            # Date(2023-5-12 fri) Time(11:40:00.00) 123.4
            # Date(2023-5-12 fri) Time(11:50:00.00) 125.1213
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        args_split = args.split()

        self.log_title("Read range ", args_split)

        # get information about the device from the cache
        device_info = await _app.device_info_cache.get_device_info(
            Address(args_split[0])
        )

        # using the device info, look up the vendor information
        if device_info:
            vendor_info = get_vendor_info(device_info.vendor_identifier)
        else:
            vendor_info = get_vendor_info(0)

        try:
            # build ReadProperty request
            request = self.build_rrange_request(
                args_split,
                range_params=range_params,
                arr_index=arr_index,
                vendor_id=vendor_id,
                bacoid=bacoid,
            )

            self.log(f"{'request':<20} {request!r}", level="debug")

        except ReadRangeException as error:
            # construction error
            self._log.exception(f"exception: {error!r}")

        response = await _app.request(request)

        if isinstance(response, ErrorRejectAbortNack):
            return response
        if not isinstance(response, ReadRangeACK):
            return None

        object_class = vendor_info.get_object_class(response.objectIdentifier[0])
        datatype = object_class.get_property_type(response.propertyIdentifier)

        value = response.itemData.cast_out(datatype)

        return value

    async def read_priority_array(self, addr, obj, obj_instance) -> t.List:
        pa = await self.read(f"{addr} {obj} {obj_instance} priorityArray")
        res = [pa]
        for each in range(1, 17):
            _pa = pa[each]  # type: ignore[index]
            for k, v in _pa.__dict__.items():
                if v is not None:
                    res.append(v)
        return res


def find_reason(apdu):
    try:
        if apdu is TimeoutError:
            return "Timeout"
        elif apdu.pduType == RejectPDU.pduType:
            reasons = RejectReason.enumerations
        elif apdu.pduType == AbortPDU.pduType:
            reasons = AbortReason.enumerations
        else:
            _code = None
            try:
                _code = apdu.errorCode
            except AttributeError:
                try:
                    _code = apdu.errorType.errorCode
                except AttributeError:
                    raise ValueError("Cannot find reason...")

            if _code:
                return f"{_code}"
        code = apdu.apduAbortRejectReason
        try:
            return [k for k, v in reasons.items() if v == code][0]
        except IndexError:
            return code
    except KeyError as err:
        return f"KeyError: {type(apdu)} has no key {err.args[0]!r}"


def cast_datatype_from_tag(propertyValue, obj_id, prop_id):
    try:
        tag_list = propertyValue.tagList.tagList
        if tag_list[0].tagClass == 0:
            tag = tag_list[0].tagNumber

            datatype = Tag._app_tag_class[tag]
        else:
            from bacpypes3.constructeddata import ArrayOf

            subtype_tag = propertyValue.tagList.tagList[0].tagList[0].tagNumber
            datatype = ArrayOf(Tag._app_tag_class[subtype_tag])
        value = {f"{obj_id}_{prop_id}": propertyValue.cast_out(datatype)}
    except Exception:
        value = {f"{obj_id}_{prop_id}": propertyValue}
    return value


def build_read_access_spec(obj_type, obj_instance, property_reference_list):
    return ReadAccessSpecification(
        objectIdentifier=(obj_type, obj_instance),
        listOfPropertyReferences=property_reference_list,
    )


def build_property_reference_list(obj_type, list_of_properties):
    property_reference_list = []
    for prop in list_of_properties:
        idx = None
        if "@idx:" in prop:
            prop, idx = prop.split("@idx:")
        prop_id = validate_property_id(obj_type, prop)
        prop_reference = PropertyReference(propertyIdentifier=prop_id)
        if idx:
            prop_reference.propertyArrayIndex = int(idx)
        property_reference_list.append(prop_reference)
    return property_reference_list


def validate_property_id(obj_type, prop_id):
    if prop_id in PropertyIdentifier.enumerations:
        if prop_id in (
            "all",
            "required",
            "optional",
            "objectName",
            "objectType",
            "objectIdentifier",
            "polarity",
        ):
            return prop_id
        # elif validate_datatype(obj_type, prop_id) is not None:
        #    return prop_id
        else:
            raise ValueError(
                f"invalid property for object type : {obj_type} | {prop_id}"
            )
    elif "@prop_" in prop_id:
        return int(prop_id.split("_")[1])
    else:
        raise ValueError(f"{prop_id} is an invalid property for {obj_type}")


# def validate_datatype(obj_type, prop_id, vendor_id=842):
#    return get_datatype(obj_type, prop_id, vendor_id=vendor_id) if not None else False
