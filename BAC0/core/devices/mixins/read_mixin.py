#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
read_mixin.py - Add ReadProperty and ReadPropertyMultiple to a device
"""
# --- standard Python modules ---
import typing as t

# --- this application's modules ---
from ....tasks.Poll import DeviceFastPoll, DeviceNormalPoll
from ...io.IOExceptions import (
    BufferOverflow,
    NoResponseFromController,
    SegmentationNotSupported,
)
from ..Points import BooleanPoint, DateTimePoint, EnumPoint, NumericPoint, StringPoint
from ..Trends import TrendLog

# --- 3rd party modules ---


# from ...functions.Schedule import Schedule

# ------------------------------------------------------------------------------


# Requests processing
def retrieve_type(obj_list, point_type_key):
    for point_type, point_address in obj_list:
        if point_type_key in str(point_type):
            yield (point_type, point_address)


def to_float_if_possible(val):
    try:
        return float(val)
    except ValueError:
        return val


def batch_requests(request, points_per_request):
    """
    Generator for creating 'request batches'.  Each batch contains a maximum of "points_per_request"
    points to read.
    :params: request a list of point_name as a list
    :params: (int) points_per_request
    :returns: (iter) list of point_name of size <= points_per_request
    """
    for i in range(0, len(request), points_per_request):
        yield request[i : i + points_per_request]


class TrendLogCreationException(Exception):
    pass


async def create_trendlogs(objList, device):
    trendlogs = {}
    for each in retrieve_type(objList, "trendLog"):
        point_address = str(each[1])
        try:
            # tl = await ATrendLog(point_address, device, read_log_on_creation=False)
            tl = TrendLog(point_address, device)
            await tl.update_properties()
            if tl.properties.log_device_object_property is None:
                ldop_type = "trendLog"
                ldop_addr = point_address
                ldop_prop = "log"
            else:
                (
                    ldop_type,
                    ldop_addr,
                ) = tl.properties.log_device_object_property.objectIdentifier
                ldop_prop = tl.properties.log_device_object_property.propertyIdentifier
            trendlogs[f"{ldop_type}_{ldop_addr}_{ldop_prop}"] = (
                tl.properties.object_name,
                tl,
            )
        except TrendLogCreationException:
            device._log.error(f"Problem creating {each}")
            continue
    return trendlogs


# def create_schedules(objList, device):
#    schedules = {}
#    for each in retrieve_type(objList, "schedule"):
#        point_address = str(each[1])
#        try:
#            tl = Schedule(point_address, device, read_log_on_creation=False)
#            if tl.properties.log_device_object_property is None:
#                raise TrendLogCreationException
#            (
#                ldop_type,
#                ldop_addr,
#            ) = tl.properties.log_device_object_property.objectIdentifier
#            ldop_prop = tl.properties.log_device_object_property.propertyIdentifier
#            trendlogs["{}_{}_{}".format(ldop_type, ldop_addr, ldop_prop)] = (
#                tl.properties.object_name,
#                tl,
#            )
#        except TrendLogCreationException:
#            device._log.error("Problem creating {}".format(each))
#            continue
#    return schedules


class ReadUtilsMixin:
    """
    Handle ReadPropertyMultiple for a device
    """

    def _rpm_request_by_name(self, point_list, property_identifier="presentValue"):
        """
        :param point_list: a list of point
        :returns: (tuple) read request for each points, points
        """
        points = []
        requests = []
        for each in point_list:
            str_list = []
            point = self._findPoint(each, force_read=False)
            points.append(point)

            str_list.append(
                f" {point.properties.type} {point.properties.address} {property_identifier}"
            )
            rpm_param = "".join(str_list)
            requests.append(rpm_param)

        return (requests, points)


class DiscoveryUtilsMixin:
    """
    Those functions are used in the process of discovering points in a device
    """

    async def read_objects_list(self, custom_object_list=None):
        if custom_object_list:
            objList = custom_object_list
        else:
            try:
                objList = await self.properties.network.read(
                    "{} device {} objectList".format(
                        self.properties.address, self.properties.device_id
                    ),
                    vendor_id=self.properties.vendor_id,
                )

            except NoResponseFromController:
                self._log.error(
                    "No object list available. Please provide a custom list using the object_list parameter"
                )
                objList = []

            except (SegmentationNotSupported, BufferOverflow):
                objList = []
                number_of_objects = await self.properties.network.read(
                    "{} device {} objectList".format(
                        self.properties.address, self.properties.device_id
                    ),
                    arr_index=0,
                    vendor_id=self.properties.vendor_id,
                )

                for i in range(1, number_of_objects + 1):
                    objList.append(
                        await self.properties.network.read(
                            "{} device {} objectList".format(
                                self.properties.address, self.properties.device_id
                            ),
                            arr_index=i,
                            vendor_id=self.properties.vendor_id,
                        )
                    )
        return objList

    async def _discoverPoints(self, custom_object_list=None):
        objList = await self.read_objects_list(custom_object_list=custom_object_list)

        points = []
        trendlogs = {}

        points.extend(
            await self._process_new_objects(
                obj_cls=NumericPoint, obj_type="analog", objList=objList
            )
        )
        points.extend(
            await self._process_new_objects(
                obj_cls=BooleanPoint, obj_type="binary", objList=objList
            )
        )
        points.extend(
            await self._process_new_objects(
                obj_cls=EnumPoint, obj_type="multi", objList=objList
            )
        )
        points.extend(
            await self._process_new_objects(
                obj_cls=NumericPoint, obj_type="loop", objList=objList
            )
        )
        points.extend(
            await self._process_new_objects(
                obj_cls=StringPoint, obj_type="characterstringValue", objList=objList
            )
        )
        points.extend(
            await self._process_new_objects(
                obj_cls=DateTimePoint, obj_type="datetime-value", objList=objList
            )
        )
        # TrendLogs
        trendlogs = await create_trendlogs(objList, self)

        self.log("Points and trendlogs (if any) created", level="info")
        return (objList, points, trendlogs)

    async def rp_discovered_values(self, discover_request, points_per_request):
        values = []
        info_length = discover_request[1]
        big_request = discover_request[0]
        self.log(f"Discover : {big_request}", level="debug")
        self.log(f"Length : {info_length}", level="debug")

        for request in batch_requests(big_request, points_per_request):
            try:
                request = f"{self.properties.address} {''.join(request)}"
                self.log(f"RP_Request: {request} ", level="debug")
                val = await self.properties.network.read(
                    request, vendor_id=self.properties.vendor_id
                )

            except KeyError as error:
                raise Exception(f"Unknown point name : {error}")

            # Save each value to history of each point
            for points_info in batch_requests(val, info_length):
                values.append(points_info)

        return values


class RPMObjectsProcessing:
    async def _process_new_objects(
        self, obj_cls=None, obj_type: str = "", objList=None, points_per_request=5
    ):
        """
        Template to generate BAC0 points instances from information coming from the network.
        """
        request = []
        new_points = []
        if obj_type == "analog":
            prop_list = "objectName presentValue units description"
        elif obj_type == "binary":
            prop_list = "objectName presentValue inactiveText activeText description"
        elif obj_type == "multi":
            prop_list = "objectName presentValue stateText description"
        elif obj_type == "loop":
            prop_list = "objectName presentValue description"
        elif obj_type == "characterstringValue":
            prop_list = "objectName presentValue"
        elif obj_type == "datetime-value":
            prop_list = "objectName presentValue"
        else:
            raise ValueError("Unsupported objectType")

        for points, address in retrieve_type(objList, obj_type):
            request.append(f"{points} {address} {prop_list} ")

        def _find_propid_index(key):
            self.log(f"Prop List : {prop_list}", level="debug")
            _prop_list = prop_list.split(" ")
            for i, each in enumerate(_prop_list):
                if key == each:
                    return i
            raise KeyError(f"{key} not part of property list")

        try:
            self.log(f"Request : {request}", level="debug")
            points_info = await self.read_multiple(
                "",
                discover_request=(request, len(prop_list.split(" "))),
                points_per_request=points_per_request,
            )
            self.log(f"Points Info : {points_info}", level="debug")
        except SegmentationNotSupported:
            raise
        # Process responses and create point
        i = 0
        for each in retrieve_type(objList, obj_type):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = points_info[i]
            i += 1
            self._log.debug(
                f"Retrieved Type {point_type} {point_address} {point_infos}"
            )
            pointName = point_infos[_find_propid_index("objectName")]
            presentValue = point_infos[_find_propid_index("presentValue")]
            self._log.debug(
                f"Reading {pointName} gave {presentValue} of type {obj_type}"
            )
            if presentValue is not None:
                if obj_type == "analog" or obj_type == "loop":
                    presentValue = float(presentValue)
                elif obj_type == "multi":
                    presentValue = int(presentValue)
            try:
                point_description = str(point_infos[_find_propid_index("description")])
            except KeyError:
                point_description = ""
            try:
                point_units_state = point_infos[_find_propid_index("units")]
            except KeyError:
                try:
                    point_units_state = point_infos[_find_propid_index("stateText")]
                except KeyError:
                    try:
                        _inactive = point_infos[_find_propid_index("inactiveText")]
                        _active = point_infos[_find_propid_index("activeText")]
                        point_units_state = (_inactive, _active)
                    except KeyError:
                        if obj_type == "binary":
                            point_units_state = ("OFF", "ON")
                        elif obj_type == "multi":
                            point_units_state = [""]
                        else:
                            point_units_state = None

            try:
                new_points.append(
                    obj_cls(
                        pointType=point_type,
                        pointAddress=point_address,
                        pointName=pointName,
                        description=point_description,
                        presentValue=presentValue,
                        units_state=point_units_state,
                        device=self,
                        history_size=self.properties.history_size,
                    )
                )
            except IndexError:
                self._log.warning(
                    "There has been a problem defining {} points. It is sometimes due to busy network. Please retry the device creation".format(
                        obj_type
                    )
                )
                raise
        return new_points


class RPObjectsProcessing:
    async def _process_new_objects(
        self, obj_cls=NumericPoint, obj_type: str = "analog", objList=None
    ):
        _newpoints = []
        for each in retrieve_type(objList, obj_type):
            point_type = str(each[0])
            point_address = str(each[1])

            if obj_type == "analog":
                units_state = await self.read_single(
                    f"{point_type} {point_address} units "
                )
            elif obj_type == "multi":
                units_state = await self.read_single(
                    f"{point_type} {point_address} stateText "
                )
            elif obj_type == "loop":
                units_state = await self.read_single(
                    f"{point_type} {point_address} units "
                )
            elif obj_type == "binary":
                units_state = (
                    (
                        await self.read_single(
                            f"{point_type} {point_address} inactiveText "
                        )
                    ),
                    (
                        await self.read_single(
                            f"{point_type} {point_address} activeText "
                        )
                    ),
                )
            else:
                units_state = None

            presentValue = await self.read_single(
                f"{point_type} {point_address} presentValue "
            )
            if (obj_type == "analog" or obj_type == "loop") and presentValue:
                presentValue = float(presentValue)

            _newpoints.append(
                obj_cls(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=await self.read_single(
                        f"{point_type} {point_address} objectName "
                    ),
                    description=await self.read_single(
                        f"{point_type} {point_address} description "
                    ),
                    presentValue=presentValue,
                    units_state=units_state,
                    device=self,
                )
            )
        return _newpoints


class ReadPropertyMultiple(ReadUtilsMixin, DiscoveryUtilsMixin, RPMObjectsProcessing):
    async def read_multiple(
        self,
        points_list,
        *,
        points_per_request=25,
        discover_request=(None, 6),
        force_single=False,
        property_identifier="presentValue",
    ):
        """
        Read points from a device using a ReadPropertyMultiple request.
        [ReadProperty requests are very slow in comparison].

        :param points_list: (list) a list of all point_name as str
        :param points_per_request: (int) number of points in the request

        Requesting many points results big requests that need segmentation.  Aim to request
        just the 'right amount' so segmentation can be avoided.  Determining the 'right amount'
        is often trial-&-error.

        :Example:

        device.read_multiple(['point1', 'point2', 'point3'], points_per_request = 10)
        """
        if not self.properties.pss["readPropertyMultiple"] or force_single:
            self.log("Read property Multiple Not supported", level="warning")
            await self.read_single(
                points_list, points_per_request=1, discover_request=discover_request
            )
        else:
            if not self.properties.segmentation_supported:
                points_per_request = 1

            if discover_request[0]:
                values = []
                info_length = discover_request[1]
                big_request = discover_request[0]
                self.log(f"Discover : {big_request}", level="debug")
                self.log(f"Length : {info_length}", level="debug")

                for request in batch_requests(big_request, points_per_request):
                    try:
                        self.properties.address
                        request = f"{self.properties.address} {''.join(request)}"
                        self.log(f"RPM_Request: {request} ", level="debug")
                        try:
                            val = await self.properties.network.readMultiple(
                                request, vendor_id=self.properties.vendor_id
                            )
                        except SegmentationNotSupported:
                            raise
                        except ValueError as error:
                            # high limit ?
                            self._log.warning(
                                f"Got a value error of {error} for request : {request}"
                            )
                            self._log.warning(
                                "We will use single point reading to create device and turn off segmentation support"
                            )
                            self.properties.segmentation_supported = False
                            await self.read_multiple(
                                points_list,
                                points_per_request=1,
                                discover_request=discover_request,
                            )
                            break

                        # print('val : ', val, len(val), type(val))
                        if val is None:
                            self.properties.segmentation_supported = False
                            raise SegmentationNotSupported

                    except KeyError as error:
                        raise Exception(f"Unknown point name : {error}")

                    except SegmentationNotSupported:
                        self.properties.segmentation_supported = False
                        self._log.warning(
                            "Looks like segmentation is not supported. Turning that off."
                        )
                        # self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)
                        self.log("Segmentation not supported", level="warning")
                        self.log("Request too big...will reduce it", level="warning")
                        if points_per_request == 1:
                            raise
                        await self.read_multiple(
                            points_list,
                            points_per_request=1,
                            discover_request=discover_request,
                        )

                    else:
                        for points_info in batch_requests(val, info_length):
                            values.append(points_info)
                return values

            else:
                self.log("Read Multiple", level="debug")
                big_request = self._rpm_request_by_name(
                    points_list, property_identifier=property_identifier
                )
                i = 0
                for request in batch_requests(big_request[0], points_per_request):
                    try:
                        request = f"{self.properties.address} {''.join(request)}"
                        self.log(request, level="debug")
                        val = await self.properties.network.readMultiple(
                            request, vendor_id=self.properties.vendor_id
                        )

                    except SegmentationNotSupported:
                        self.properties.segmentation_supported = False
                        await self.read_multiple(
                            points_list,
                            points_per_request=1,
                            discover_request=discover_request,
                        )

                    except KeyError as error:
                        raise Exception(f"Unknown point name : {error}")

                    else:
                        points_values = zip(big_request[1][i : i + len(val)], val)
                        i += len(val)
                        for each in points_values:
                            each[0]._trend(each[1])

    async def read_single(
        self, points_list, *, points_per_request=1, discover_request=(None, 4)
    ):
        if discover_request[0]:
            return await self.rp_discovered_values(
                discover_request, points_per_request=points_per_request
            )

        else:
            big_request = self._rpm_request_by_name(points_list)
            i = 0
            for request in batch_requests(big_request[0], points_per_request):
                try:
                    request = f"{self.properties.address} {''.join(request)}"
                    val = await self.properties.network.read(
                        request, vendor_id=self.properties.vendor_id
                    )
                    points_values = zip(big_request[1][i : i + len(val)], val)
                    i += len(val)
                    for each in points_values:
                        each[0]._trend(each[1])

                except KeyError as error:
                    raise Exception(f"Unknown point name : {error}")

    def poll(self, command="start", *, delay=10):
        """
        Poll a point every x seconds (delay=x sec)
        Can be stopped by using point.poll('stop') or .poll(0) or .poll(False)
        or by setting a delay = 0

        :param command: (str) start or stop polling
        :param delay: (int) time delay between polls in seconds
        :type command: str
        :type delay: int

        :Example:

        device.poll()
        device.poll('stop')
        device.poll(delay = 5)
        """
        _poll_cls: t.Union[t.Type[DeviceFastPoll], t.Type[DeviceNormalPoll]]
        if delay < 10:
            self.properties.fast_polling = True
            _poll_cls = DeviceFastPoll
        else:
            self.properties.fast_polling = False
            _poll_cls = DeviceNormalPoll

        if str(command).lower() not in ["stop", "start", "0", "False"]:
            self.log(
                'Bad argument for function. Needs "stop", "start", "0" or "False" or provide keyword arg (command or delay)',
                level="error",
            )
            return

        if (
            str(command).lower() == "stop"
            or command == False  # noqa E712
            or command == 0
            or delay == 0
        ):
            if isinstance(self._polling_task.task, DeviceNormalPoll) or isinstance(
                self._polling_task.task, DeviceFastPoll
            ):
                self._polling_task.task.stop()
                while self._polling_task.task.is_alive():
                    pass

                self._polling_task.task = None
                self._polling_task.running = False
                self.log(f"{self.properties.name} | Polling stopped", level="info")

        elif self._polling_task.task is None:
            self._polling_task.task = _poll_cls(
                self, delay=delay, name=self.properties.name
            )
            self._polling_task.task.start()
            self._polling_task.running = True
            self.log(
                f"Polling started, values read every {delay} seconds", level="info"
            )

        elif self._polling_task.running:
            self._polling_task.task.stop()
            while self._polling_task.task.is_alive():
                pass
            self._polling_task.running = False
            self._polling_task.task = _poll_cls(
                self, delay=delay, name=self.properties.name
            )
            self._polling_task.task.start()
            self._polling_task.running = True
            self.log(
                f"Polling started, every values read each {delay} seconds", level="info"
            )

        else:
            raise RuntimeError("Stop polling before redefining it")


class ReadProperty(ReadUtilsMixin, DiscoveryUtilsMixin, RPObjectsProcessing):
    async def read_multiple(
        self, points_list, *, points_per_request=1, discover_request=(None, 6)
    ):
        """
        Functions to read points from a device using the ReadPropertyMultiple request.
        Using readProperty request can be very slow to read a lot of data.

        :param points_list: (list) a list of all point_name as str
        :param points_per_request: (int) number of points in the request

        Using too many points will create big requests needing segmentation.
        It's better to use just enough request so the message will not require
        segmentation.

        :Example:

        device.read_multiple(['point1', 'point2', 'point3'], points_per_request = 10)
        """
        if isinstance(points_list, list):
            (requests, points) = self._rpm_request_by_name(points_list)
            for i, req in enumerate(requests):
                val = await self.read_single(
                    req, points_per_request=1, discover_request=discover_request
                )
                if val is not None and val != "":
                    points[i]._trend(val)
        else:
            await self.read_single(
                points_list, points_per_request=1, discover_request=discover_request
            )

    async def read_single(
        self, request, *, points_per_request=1, discover_request=(None, 4)
    ):
        try:
            request = f"{self.properties.address} {''.join(request)}"
            self.log(f"RP_Request: {request} ", level="debug")
            return await self.properties.network.read(
                request, vendor_id=self.properties.vendor_id
            )
        except KeyError as error:
            raise Exception(f"Unknown point name: {error}")

        except NoResponseFromController:
            return ""

    def poll(self, command="start", *, delay=120):
        """
        Poll a point every x seconds (delay=x sec)
        Can be stopped by using point.poll('stop') or .poll(0) or .poll(False)
        or by setting a delay = 0

        :param command: (str) start or stop polling
        :param delay: (int) time delay between polls in seconds
        :type command: str
        :type delay: int

        :Example:

        device.poll()
        device.poll('stop')
        device.poll(delay = 5)
        """
        if delay < 10:
            self._log.warning(
                "Device do not support RPM, fast polling not available, limiting delay to 10sec."
            )
            self.properties.fast_polling = False
            delay = 10

        if (
            str(command).lower() == "stop"
            or command is False
            or command == 0
            or delay == 0
        ):
            if isinstance(self._polling_task.task, DeviceNormalPoll):
                self._polling_task.task.stop()
                while self._polling_task.task.is_alive():
                    pass

                self._polling_task.task = None
                self._polling_task.running = False
                self.log("Polling stopped", level="info")

        elif self._polling_task.task is None:
            self._polling_task.task = DeviceNormalPoll(
                self, delay=delay, name=self.properties.name
            )
            self._polling_task.task.start()
            self._polling_task.running = True
            self.log(
                f"Polling started, values read every {delay} seconds", level="info"
            )

        elif self._polling_task.running:
            self._polling_task.task.stop()
            while self._polling_task.task.is_alive():
                pass
            self._polling_task.running = False
            self._polling_task.task = DeviceNormalPoll(
                self, delay=delay, name=self.properties.name
            )
            self._polling_task.task.start()
            self._polling_task.running = True
            self.log(
                f"Polling started, every values read each {delay} seconds", level="info"
            )

        else:
            raise RuntimeError("Stop polling before redefining it")
