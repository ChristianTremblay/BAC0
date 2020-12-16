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

# --- standard Python modules ---

# --- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging

from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import (
    PropertyReference,
    ReadAccessSpecification,
    ReadPropertyRequest,
    ReadPropertyMultipleRequest,
    RejectReason,
    AbortReason,
    RejectPDU,
    AbortPDU,
)

from bacpypes.basetypes import PropertyIdentifier, DateTime
from bacpypes.apdu import (
    ReadPropertyMultipleACK,
    ReadPropertyACK,
    ReadRangeRequest,
    ReadRangeACK,
    Range,
    RangeByPosition,
    RangeBySequenceNumber,
    RangeByTime,
)
from bacpypes.primitivedata import Tag, ObjectIdentifier, Unsigned, Date, Time
from bacpypes.constructeddata import Array
from bacpypes.iocb import IOCB, TimeoutError
from bacpypes.core import deferred

# --- this application's modules ---
from .IOExceptions import (
    ReadPropertyException,
    ReadPropertyMultipleException,
    ReadRangeException,
    NoResponseFromController,
    ApplicationNotStarted,
    UnrecognizedService,
    SegmentationNotSupported,
    UnknownPropertyError,
    UnknownObjectError,
    BufferOverflow,
)

from ..utils.notes import note_and_log

# ------------------------------------------------------------------------------


@note_and_log
class ReadProperty:
    """
    Defines BACnet Read functions: readProperty and readPropertyMultiple.
    Data exchange is made via a Queue object
    A timeout of 10 seconds allows detection of invalid device or communciation errors.
    """

    def read(
        self,
        args,
        arr_index=None,
        vendor_id=0,
        bacoid=None,
        timeout=10,
        prop_id_required=False,
    ):
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

        args_split = args.split()

        self.log_title("Read property", args_split)

        vendor_id = vendor_id
        bacoid = bacoid

        try:
            # build ReadProperty request
            iocb = IOCB(
                self.build_rp_request(
                    args_split, arr_index=arr_index, vendor_id=vendor_id, bacoid=bacoid
                )
            )
            iocb.set_timeout(timeout)
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)
            self._log.debug("{:<20} {!r}".format("iocb", iocb))

        except ReadPropertyException as error:
            # construction error
            self._log.exception("exception: {!r}".format(error))

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, ReadPropertyACK):  # expecting an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug("Not an ack. | APDU : {}".format(apdu))
                return

            # find the datatype
            datatype = get_datatype(
                apdu.objectIdentifier[0], apdu.propertyIdentifier, vendor_id=vendor_id
            )
            if not datatype:
                # raise TypeError("unknown datatype")
                value = cast_datatype_from_tag(
                    apdu.propertyValue,
                    apdu.objectIdentifier[0],
                    apdu.propertyIdentifier,
                )
            else:
                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (
                    apdu.propertyArrayIndex is not None
                ):
                    if apdu.propertyArrayIndex == 0:
                        value = apdu.propertyValue.cast_out(Unsigned)
                    else:
                        value = apdu.propertyValue.cast_out(datatype.subtype)
                else:
                    value = apdu.propertyValue.cast_out(datatype)

                self._log.debug("{:<20} {:<20}".format("value", "datatype"))
                self._log.debug("{!r:<20} {!r:<20}".format(value, datatype))
            if prop_id_required:
                try:
                    int(apdu.propertyIdentifier)
                    prop_id = "@prop_{}".format(apdu.propertyIdentifier)
                    value = list(value.items())[0][1]
                except ValueError:
                    prop_id = apdu.propertyIdentifier
                return (value, prop_id)
            else:
                return value

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            if reason == "segmentationNotSupported":
                value = self._split_the_read_request(args, arr_index)
                return value
            else:
                if reason == "unknownProperty":
                    if "description" in args:
                        self._log.warning(
                            "The description property is not implemented in the device. Using a default value for internal needs."
                        )
                        return "Property Not Implemented"
                    elif "inactiveText" in args:
                        self._log.warning(
                            "The inactiveText property is not implemented in the device. Using a default value of Off for internal needs."
                        )
                        return "Off"
                    elif "activeText" in args:
                        self._log.warning(
                            "The activeText property is not implemented in the device. Using a default value of On for internal needs."
                        )
                        return "On"
                    else:
                        raise UnknownPropertyError("Unknown property {}".format(args))
                elif reason == "unknownObject":
                    self._log.warning("Unknown object {}".format(args))
                    raise UnknownObjectError("Unknown object {}".format(args))
                elif reason == "bufferOverflow":
                    self._log.warning(
                        "Buffer capacity exceeded in device {}".format(args)
                    )
                    return self._split_the_read_request(args, arr_index)
                else:
                    # Other error... consider NoResponseFromController (65)
                    # even if the real reason is another one
                    raise NoResponseFromController(
                        "APDU Abort Reason : {}".format(reason)
                    )

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
        nmbr_obj = self.read(args, arr_index=0)
        return [self.read(args, arr_index=i) for i in range(1, nmbr_obj + 1)]

    def readMultiple(
        self, args, request_dict=None, vendor_id=0, timeout=10, prop_id_required=False
    ):
        """ Build a ReadPropertyMultiple request, wait for the answer and return the values

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

        if request_dict is not None:
            request = self.build_rpm_request_from_dict(request_dict, vendor_id)
        else:
            args = args.split()
            request = self.build_rpm_request(args, vendor_id=vendor_id)
            self.log_title("Read Multiple", args)

        values = []
        dict_values = {}

        try:
            # build an ReadPropertyMultiple request
            iocb = IOCB(request)
            iocb.set_timeout(timeout)
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)
            self._log.debug("{:<20} {!r}".format("iocb", iocb))

        except ReadPropertyMultipleException as error:
            # construction error
            self._log.exception("exception: {!r}".format(error))

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, ReadPropertyMultipleACK):  # expecting an ACK
                self._log.debug("{:<20}".format("not an ack"))
                self._log.warning(
                    "Not an Ack. | APDU : {} / {}".format((apdu, type(apdu)))
                )
                return

            # loop through the results
            for result in apdu.listOfReadAccessResults:
                # here is the object identifier
                objectIdentifier = result.objectIdentifier

                self.log_subtitle(
                    "{!r} : {!r}".format(objectIdentifier[0], objectIdentifier[1]),
                    width=114,
                )
                self._log.debug(
                    "{:<20} {:<20} {:<30} {:<20}".format(
                        "propertyIdentifier", "propertyArrayIndex", "value", "datatype"
                    )
                )
                self._log.debug("-" * 114)
                dict_values[objectIdentifier] = []
                # now come the property values per object
                for element in result.listOfResults:
                    # get the property and array index
                    propertyIdentifier = element.propertyIdentifier
                    propertyArrayIndex = element.propertyArrayIndex

                    readResult = element.readResult

                    if propertyArrayIndex is not None:
                        _prop_id = "{}@idx:{}".format(
                            propertyIdentifier, propertyArrayIndex
                        )
                    else:
                        _prop_id = propertyIdentifier

                    if readResult.propertyAccessError is not None:
                        self._log.debug(
                            "Property Access Error for {}".format(
                                readResult.propertyAccessError
                            )
                        )
                        values.append(None)
                        dict_values[objectIdentifier].append((_prop_id, None))
                    else:
                        # here is the value
                        propertyValue = readResult.propertyValue

                        # find the datatype
                        datatype = get_datatype(
                            objectIdentifier[0], propertyIdentifier, vendor_id=vendor_id
                        )

                        if not datatype:
                            value = cast_datatype_from_tag(
                                propertyValue, objectIdentifier[0], propertyIdentifier
                            )
                        else:
                            # special case for array parts, others are managed by cast_out
                            if issubclass(datatype, Array) and (
                                propertyArrayIndex is not None
                            ):
                                if propertyArrayIndex == 0:
                                    value = propertyValue.cast_out(Unsigned)
                                else:
                                    value = propertyValue.cast_out(datatype.subtype)
                            elif propertyValue.is_application_class_null():
                                value = None
                            else:
                                value = propertyValue.cast_out(datatype)

                            self._log.debug(
                                "{!r:<20} {!r:<20} {!r:<30} {!r:<20}".format(
                                    propertyIdentifier,
                                    propertyArrayIndex,
                                    value,
                                    datatype,
                                )
                            )
                        if prop_id_required:
                            try:
                                int(propertyIdentifier)
                                prop_id = "@prop_{}".format(propertyIdentifier)
                                value = list(value.items())[0][1]
                            except ValueError:
                                prop_id = propertyIdentifier
                            values.append((value, prop_id))
                            dict_values[objectIdentifier].append(
                                (_prop_id, (value, prop_id))
                            )
                        else:
                            values.append(value)
                            dict_values[objectIdentifier].append((_prop_id, value))

            if request_dict is not None:
                return dict_values
            else:
                return values

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            self._log.warning("APDU Abort Reject Reason : {}".format(reason))
            self._log.debug("The Request was : {}".format(args))
            if reason == "unrecognizedService":
                raise UnrecognizedService()
            elif reason == "segmentationNotSupported":
                # value = self._split_the_read_request(args, arr_index)
                # return value
                self.segmentation_supported = False
                raise SegmentationNotSupported()
            elif reason == "unknownObject":
                self._log.warning("Unknown object {}".format(args))
                raise UnknownObjectError("Unknown object {}".format(args))
            elif reason == "unknownProperty":
                self._log.warning("Unknown property {}".format(args))

                values.append("")
                return values
            else:
                self._log.warning("No response from controller {}".format(reason))
                values.append("")
                return values

    def build_rp_request(self, args, arr_index=None, vendor_id=0, bacoid=None):
        addr, obj_type, obj_inst, prop_id = args[:4]
        vendor_id = vendor_id
        bacoid = bacoid

        if obj_type.isdigit():
            obj_type = int(obj_type)
        elif "@obj_" in obj_type:
            obj_type = int(obj_type.split("_")[1])
        elif not get_object_class(obj_type, vendor_id=vendor_id):
            raise ValueError("Unknown object type : {}".format(obj_type))

        obj_inst = int(obj_inst)

        if prop_id.isdigit():
            prop_id = int(prop_id)
        elif "@prop_" in prop_id:
            prop_id = int(prop_id.split("_")[1])

        # datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)

        # build a request
        request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id,
            propertyArrayIndex=arr_index,
        )
        request.pduDestination = Address(addr)

        if len(args) == 5:
            request.propertyArrayIndex = int(args[4])
        self._log.debug("{:<20} {!r}".format("REQUEST", request))
        return request

    def build_rpm_request(self, args, vendor_id=0):
        """
        Build request from args
        """
        self._log.debug(args)
        i = 0
        addr = args[i]
        i += 1
        vendor_id = vendor_id

        read_access_spec_list = []
        while i < len(args):
            obj_type = args[i]
            i += 1

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif "@obj_" in obj_type:
                obj_type = int(obj_type.split("_")[1])
            elif not get_object_class(obj_type, vendor_id=vendor_id):
                raise ValueError("Unknown object type : {}".format(obj_type))

            obj_inst = int(args[i])
            i += 1

            prop_reference_list = []
            while i < len(args):
                prop_id = args[i]
                if "@obj_" in prop_id:
                    break
                if prop_id not in PropertyIdentifier.enumerations:
                    try:
                        if "@prop_" in prop_id:
                            prop_id = int(prop_id.split("_")[1])
                            self._log.debug(
                                "Proprietary property : {} | {} -> Vendor : {}".format(
                                    obj_type, prop_id, vendor_id
                                )
                            )
                        else:
                            break
                    except:
                        break

                elif prop_id not in (
                    "all",
                    "required",
                    "optional",
                    "objectName",
                    "objectType",
                    "objectIdentifier",
                    "polarity",
                ):
                    datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)
                    if not datatype:
                        raise ValueError(
                            "invalid property for object type : {} | {}".format(
                                obj_type, prop_id
                            )
                        )
                i += 1

                # build a property reference
                prop_reference = PropertyReference(propertyIdentifier=prop_id)

                # check for an array index
                if (i < len(args)) and args[i].isdigit():
                    prop_reference.propertyArrayIndex = int(args[i])
                    i += 1

                prop_reference_list.append(prop_reference)

            if not prop_reference_list:
                raise ValueError("provide at least one property")

            # build a read access specification
            read_access_spec = ReadAccessSpecification(
                objectIdentifier=(obj_type, obj_inst),
                listOfPropertyReferences=prop_reference_list,
            )

            read_access_spec_list.append(read_access_spec)

        if not read_access_spec_list:
            raise RuntimeError("at least one read access specification required")

        # build the request
        request = ReadPropertyMultipleRequest(
            listOfReadAccessSpecs=read_access_spec_list
        )
        request.pduDestination = Address(addr)
        return request

    def build_rpm_request_from_dict(self, request_dict, vendor_id):
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
        vendor_id = 842
        addr = request_dict["address"]
        objects = request_dict["objects"]
        if "vendor_id" in request_dict.keys():
            vendor_id = int(request_dict["vendor_id"])

        read_access_spec_list = []

        for obj, list_of_properties in objects.items():
            obj_type, obj_instance = obj.split(":")
            obj_type = validate_object_type(obj_type, vendor_id=vendor_id)
            obj_instance = int(obj_instance)
            property_reference_list = build_property_reference_list(
                obj_type, list_of_properties
            )
            read_acces_spec = build_read_access_spec(
                obj_type, obj_instance, property_reference_list
            )
            read_access_spec_list.append(read_acces_spec)

        if not read_access_spec_list:
            raise RuntimeError("at least one read access specification required")

        # build the request
        request = ReadPropertyMultipleRequest(
            listOfReadAccessSpecs=read_access_spec_list
        )
        request.pduDestination = Address(addr)

        return request

    def build_rrange_request(
        self, args, range_params=None, arr_index=None, vendor_id=0, bacoid=None
    ):
        addr, obj_type, obj_inst, prop_id = args[:4]

        vendor_id = vendor_id
        bacoid = bacoid

        if obj_type.isdigit():
            obj_type = int(obj_type)
        elif not get_object_class(obj_type, vendor_id=vendor_id):
            raise ValueError("Unknown object type {}".format(obj_type))

        obj_inst = int(obj_inst)

        if prop_id.isdigit():
            prop_id = int(prop_id)
        datatype = get_datatype(obj_type, prop_id, vendor_id=vendor_id)
        if not datatype:
            raise ValueError("invalid property for object type")

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
                    referenceTime=DateTime(
                        date=Date(date).value, time=Time(time).value
                    ),
                    count=int(count),
                )
                request.range = Range(byTime=rbt)
            elif range_type == "x":
                # should be missing required parameter
                request.range = Range()
            else:
                raise ValueError("unknown range type: %r" % (range_type,))

        if len(args) == 5:
            request.propertyArrayIndex = int(args[4])
        self._log.debug("{:<20} {!r}".format("REQUEST", request))
        return request

    def readRange(
        self,
        args,
        range_params=None,
        arr_index=None,
        vendor_id=0,
        bacoid=None,
        timeout=10,
    ):
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

        args_split = args.split()

        self.log_title("Read range ", args_split)

        vendor_id = vendor_id
        bacoid = bacoid

        try:
            # build ReadProperty request
            request = self.build_rrange_request(
                args_split,
                range_params=range_params,
                arr_index=arr_index,
                vendor_id=vendor_id,
                bacoid=bacoid,
            )
            iocb = IOCB(request)
            iocb.set_timeout(timeout)
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)
            self._log.debug("{:<20} {!r}".format("iocb", iocb))

        except ReadRangeException as error:
            # construction error
            self._log.exception("exception: {!r}".format(error))

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, ReadRangeACK):  # expecting an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug(
                    "Not an ack. | APDU : {} / {}".format((apdu, type(apdu)))
                )
                return

            # find the datatype
            datatype = get_datatype(
                apdu.objectIdentifier[0], apdu.propertyIdentifier, vendor_id=vendor_id
            )
            if not datatype:
                # raise TypeError("unknown datatype")
                datatype = cast_datatype_from_tag(
                    apdu.propertyValue,
                    apdu.objectIdentifier[0],
                    apdu.propertyIdentifier,
                )

            try:
                value = apdu.itemData.cast_out(datatype)
            except TypeError as error:
                self._log.error(
                    "Problem casting value : {} | Datatype : {} | error : {}".format(
                        apdu.itemData, datatype, error
                    )
                )
                return apdu

            self._log.debug("{:<20} {:<20}".format("value", "datatype"))
            self._log.debug("{!r:<20} {!r:<20}".format(value, datatype))
            return value

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            if reason == "segmentationNotSupported":
                self._log.warning(
                    "Segmentation not supported... will read properties one by one..."
                )
                self._log.debug("The Request was : {}".format(args_split))
                value = self._split_the_read_request(args, arr_index)
                return value
            else:
                if reason == "unknownProperty":
                    if "priorityArray" in args:
                        self._log.debug("Unknown property {}".format(args))
                    else:
                        self._log.warning("Unknown property {}".format(args))
                    if "description" in args:
                        return ""
                    elif "inactiveText" in args:
                        return "Off"
                    elif "activeText" in args:
                        return "On"
                    else:
                        raise UnknownPropertyError("Unknown property {}".format(args))
                elif reason == "unknownObject":
                    self._log.warning("Unknown object {}".format(args))
                    raise UnknownObjectError("Unknown object {}".format(args))
                else:
                    # Other error... consider NoResponseFromController (65)
                    # even if the realy reason is another one
                    raise NoResponseFromController(
                        "APDU Abort Reason : {}".format(reason)
                    )

    def read_priority_array(self, addr, obj, obj_instance):
        pa = self.read("{} {} {} priorityArray".format(addr, obj, obj_instance))
        res = [pa]
        for each in range(1, 17):
            _pa = pa[each]
            for k, v in _pa.__dict__.items():
                if v != None:
                    res.append(v)
        return res


def find_reason(apdu):
    try:
        if apdu == TimeoutError:
            return "Timeout"
        elif apdu.pduType == RejectPDU.pduType:
            reasons = RejectReason.enumerations
        elif apdu.pduType == AbortPDU.pduType:
            reasons = AbortReason.enumerations
        else:
            if apdu.errorCode and apdu.errorClass:
                return "{}".format(apdu.errorCode)
            else:
                raise ValueError("Cannot find reason...")
        code = apdu.apduAbortRejectReason
        try:
            return [k for k, v in reasons.items() if v == code][0]
        except IndexError:
            return code
    except KeyError as err:
        return "KeyError: {} has no key {0!r}".format(type(apdu), err.args[0])


def cast_datatype_from_tag(propertyValue, obj_id, prop_id):
    try:
        tag_list = propertyValue.tagList.tagList
        if tag_list[0].tagClass == 0:
            tag = tag_list[0].tagNumber

            datatype = Tag._app_tag_class[tag]
        else:
            from bacpypes.constructeddata import ArrayOf

            subtype_tag = propertyValue.tagList.tagList[0].tagList[0].tagNumber
            datatype = ArrayOf(Tag._app_tag_class[subtype_tag])
        value = {"{}_{}".format(obj_id, prop_id): propertyValue.cast_out(datatype)}
    except:
        value = {"{}_{}".format(obj_id, prop_id): propertyValue}
    return value


def validate_object_type(obj_type, vendor_id=842):
    if obj_type.isdigit():
        obj_type = int(obj_type)
    elif "@obj_" in obj_type:
        obj_type = int(obj_type.split("_")[1])
    elif not get_object_class(obj_type, vendor_id=vendor_id):
        raise ValueError("Unknown object type : {}".format(obj_type))
    return obj_type


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
        elif validate_datatype(obj_type, prop_id) is not None:
            return prop_id
        else:
            raise ValueError(
                "invalid property for object type : {} | {}".format(obj_type, prop_id)
            )
    elif "@prop_" in prop_id:
        return int(prop_id.split("_")[1])
    # elif "@obj_" in prop_id:
    else:
        raise ValueError("{} is an invalid property for {}".format(prop_id, obj_type))


def validate_datatype(obj_type, prop_id, vendor_id=842):
    return get_datatype(obj_type, prop_id, vendor_id=vendor_id) if not None else False
