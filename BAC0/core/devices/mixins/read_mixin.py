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

# --- 3rd party modules ---

# --- this application's modules ---
from ....tasks.Poll import DeviceNormalPoll, DeviceFastPoll
from ...io.IOExceptions import (
    ReadPropertyMultipleException,
    NoResponseFromController,
    SegmentationNotSupported,
    BufferOverflow,
)
from ..Points import NumericPoint, BooleanPoint, EnumPoint, StringPoint, OfflinePoint
from ..Trends import TrendLog

# ------------------------------------------------------------------------------


def retrieve_type(obj_list, point_type_key):
    for point_type, point_address in obj_list:
        if point_type_key in str(point_type):
            yield (point_type, point_address)


def to_float_if_possible(val):
    try:
        return float(val)
    except:
        return val


class ReadPropertyMultiple:
    """
    Handle ReadPropertyMultiple for a device
    """

    def _batches(self, request, points_per_request):
        """
        Generator for creating 'request batches'.  Each batch contains a maximum of "points_per_request" 
        points to read.
        :params: request a list of point_name as a list
        :params: (int) points_per_request
        :returns: (iter) list of point_name of size <= points_per_request
        """
        for i in range(0, len(request), points_per_request):
            yield request[i : i + points_per_request]

    def _rpm_request_by_name(self, point_list):
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
                " {} {} presentValue".format(
                    point.properties.type, point.properties.address
                )
            )
            rpm_param = "".join(str_list)
            requests.append(rpm_param)

        return (requests, points)

    def read_multiple(
        self,
        points_list,
        *,
        points_per_request=25,
        discover_request=(None, 6),
        force_single=False
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
            self._log.warning("Read property Multiple Not supported")
            self.read_single(
                points_list, points_per_request=1, discover_request=discover_request
            )
        else:
            if not self.properties.segmentation_supported:
                points_per_request = 1

            if discover_request[0]:
                values = []
                info_length = discover_request[1]
                big_request = discover_request[0]

                for request in self._batches(big_request, points_per_request):
                    try:
                        request = "{} {}".format(
                            self.properties.address, "".join(request)
                        )
                        self._log.debug("RPM_Request: {} ".format(request))
                        try:
                            val = self.properties.network.readMultiple(
                                request, vendor_id=self.properties.vendor_id
                            )
                        except SegmentationNotSupported:
                            raise

                        # print('val : ', val, len(val), type(val))
                        if val == None:
                            self.properties.segmentation_supported = False
                            raise SegmentationNotSupported

                    except KeyError as error:
                        raise Exception("Unknown point name : {}".format(error))

                    except SegmentationNotSupported as error:
                        self.properties.segmentation_supported = False
                        # self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)
                        self._log.warning("Segmentation not supported")
                        self._log.warning("Request too big...will reduce it")
                        if points_per_request == 1:
                            raise
                        self.read_multiple(
                            points_list,
                            points_per_request=1,
                            discover_request=discover_request,
                        )

                    else:
                        for points_info in self._batches(val, info_length):
                            values.append(points_info)
                return values

            else:
                big_request = self._rpm_request_by_name(points_list)
                i = 0
                for request in self._batches(big_request[0], points_per_request):
                    try:
                        request = "{} {}".format(
                            self.properties.address, "".join(request)
                        )
                        val = self.properties.network.readMultiple(
                            request, vendor_id=self.properties.vendor_id
                        )

                    except SegmentationNotSupported as error:
                        self.properties.segmentation_supported = False
                        self.read_multiple(
                            points_list,
                            points_per_request=1,
                            discover_request=discover_request,
                        )

                    except KeyError as error:
                        raise Exception("Unknown point name : {}".format(error))

                    else:
                        points_values = zip(big_request[1][i : i + len(val)], val)
                        i += len(val)
                        for each in points_values:
                            each[0]._trend(each[1])

    def read_single(
        self, points_list, *, points_per_request=1, discover_request=(None, 4)
    ):
        if discover_request[0]:
            values = []
            info_length = discover_request[1]
            big_request = discover_request[0]

            for request in self._batches(big_request, points_per_request):
                try:
                    request = "{} {}".format(self.properties.address, "".join(request))
                    val = self.properties.network.read(
                        request, vendor_id=self.properties.vendor_id
                    )

                except KeyError as error:
                    raise Exception("Unknown point name : {}".format(error))

                # Save each value to history of each point
                for points_info in self._batches(val, info_length):
                    values.append(points_info)

            return values

        else:
            big_request = self._rpm_request_by_name(points_list)
            i = 0
            for request in self._batches(big_request[0], points_per_request):
                try:
                    request = "{} {}".format(self.properties.address, "".join(request))
                    val = self.properties.network.read(
                        request, vendor_id=self.properties.vendor_id
                    )
                    points_values = zip(big_request[1][i : i + len(val)], val)
                    i += len(val)
                    for each in points_values:
                        each[0]._trend(each[1])

                except KeyError as error:
                    raise Exception("Unknown point name : {}".format(error))

    def _discoverPoints(self, custom_object_list=None):
        if custom_object_list:
            objList = custom_object_list
        else:
            try:
                objList = self.properties.network.read(
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
                number_of_objects = self.properties.network.read(
                    "{} device {} objectList".format(
                        self.properties.address, self.properties.device_id
                    ),
                    arr_index=0,
                    vendor_id=self.properties.vendor_id,
                )

                for i in range(1, number_of_objects + 1):
                    objList.append(
                        self.properties.network.read(
                            "{} device {} objectList".format(
                                self.properties.address, self.properties.device_id
                            ),
                            arr_index=i,
                            vendor_id=self.properties.vendor_id,
                        )
                    )

        points = []
        trendlogs = {}

        def _process_new_objects(
            obj_cls=NumericPoint, obj_type="analog", objList=None, points_per_request=5
        ):
            """
            Template to generate BAC0 points instances from information coming from the network.
            """
            request = []
            new_points = []
            if obj_type == "analog":
                prop_list = "objectName presentValue units description"
            elif obj_type == "binary":
                prop_list = (
                    "objectName presentValue inactiveText activeText description"
                )
            elif obj_type == "multi":
                prop_list = "objectName presentValue stateText description"
            elif obj_type == "characterstringValue":
                prop_list = "objectName presentValue"
            else:
                raise ValueError("Unsupported objectType")

            list_of_obj = retrieve_type(objList, obj_type)
            for points, address in list_of_obj:
                request.append("{} {} {} ".format(points, address, prop_list))

            def _find_propid_index(key):
                _prop_list = prop_list.split(" ")
                for i, each in enumerate(_prop_list):
                    if key == each:
                        return i
                raise KeyError("{} not part of property list".format(key))

            try:
                points_info = self.read_multiple(
                    "",
                    discover_request=(request, len(prop_list.split(" "))),
                    points_per_request=points_per_request,
                )
            except SegmentationNotSupported:
                raise
            # Process responses and create point
            i = 0
            for each in retrieve_type(objList, obj_type):
                point_type = str(each[0])
                point_address = str(each[1])
                point_infos = points_info[i]
                i += 1

                pointName = point_infos[_find_propid_index("objectName")]
                presentValue = point_infos[_find_propid_index("presentValue")]
                if obj_type == "analog":
                    presentValue = float(presentValue)
                elif obj_type == "multi":
                    presentValue = int(presentValue)
                try:
                    point_description = point_infos[_find_propid_index("description")]
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

        points.extend(
            _process_new_objects(
                obj_cls=NumericPoint, obj_type="analog", objList=objList
            )
        )
        points.extend(
            _process_new_objects(
                obj_cls=BooleanPoint, obj_type="binary", objList=objList
            )
        )
        points.extend(
            _process_new_objects(obj_cls=EnumPoint, obj_type="multi", objList=objList)
        )
        points.extend(
            _process_new_objects(
                obj_cls=StringPoint, obj_type="characterstringValue", objList=objList
            )
        )

        # TrendLogs
        for each in retrieve_type(objList, "trendLog"):
            point_address = str(each[1])
            tl = TrendLog(point_address, self, read_log_on_creation=False)
            if tl.properties.log_device_object_property is None:
                continue
            ldop_type, ldop_addr = (
                tl.properties.log_device_object_property.objectIdentifier
            )
            ldop_prop = tl.properties.log_device_object_property.propertyIdentifier
            trendlogs["{}_{}_{}".format(ldop_type, ldop_addr, ldop_prop)] = (
                tl.properties.object_name,
                tl,
            )

        self._log.debug("RPM Mixin : %s | %s | %s", objList, points, trendlogs)
        self._log.info("Ready!")
        return (objList, points, trendlogs)

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
        if delay < 10:
            self.properties.fast_polling = True
            _poll_cls = DeviceFastPoll
        else:
            self.properties.fast_polling = False
            _poll_cls = DeviceNormalPoll

        if str(command).lower() not in ["stop", "start", "0", "False"]:
            self._log.error(
                'Bad argument for function. Needs "stop", "start", "0" or "False" or provide keyword arg (command or delay)'
            )
            return

        if (
            str(command).lower() == "stop"
            or command == False
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
                self._log.info("Polling stopped")

        elif self._polling_task.task is None:
            self._polling_task.task = _poll_cls(
                self, delay=delay, name=self.properties.name
            )
            self._polling_task.task.start()
            self._polling_task.running = True
            self._log.info(
                "Polling started, values read every {} seconds".format(delay)
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
            self._log.info(
                "Polling started, every values read each {} seconds".format(delay)
            )

        else:
            raise RuntimeError("Stop polling before redefining it")


class ReadProperty:
    """
    Handle ReadProperty for a device
    """

    def _batches(self, request, points_per_request):
        """
        Generator for creating 'request batches'.  Each batch contains a maximum of "points_per_request"
        points to read.
        :params: request a list of point_name as a list
        :params: (int) points_per_request
        :returns: (iter) list of point_name of size <= points_per_request
        """
        for i in range(0, len(request), points_per_request):
            yield request[i : i + points_per_request]

    def _rpm_request_by_name(self, point_list):
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

            str_list.append(" " + point.properties.type)
            str_list.append(" " + str(point.properties.address))
            str_list.append(" presentValue")
            rpm_param = "".join(str_list)
            requests.append(rpm_param)

        return (requests, points)

    def read_multiple(
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
            for (i, req) in enumerate(requests):
                val = self.read_single(
                    req, points_per_request=1, discover_request=discover_request
                )
                if val is not None and val != "":
                    points[i]._trend(val)
        else:
            self.read_single(
                points_list, points_per_request=1, discover_request=discover_request
            )

    def read_single(self, request, *, points_per_request=1, discover_request=(None, 4)):
        try:
            request = "{} {}".format(self.properties.address, "".join(request))
            return self.properties.network.read(
                request, vendor_id=self.properties.vendor_id
            )
        except KeyError as error:
            raise Exception("Unknown point name: {}".format(error))

        except NoResponseFromController as error:
            return ""

    def _discoverPoints(self, custom_object_list=None):
        if custom_object_list:
            objList = custom_object_list
        else:
            try:
                objList = self.properties.network.read(
                    "{} device {} objectList".format(
                        self.properties.address, self.properties.device_id
                    ),
                    vendor_id=self.properties.vendor_id,
                )

            except SegmentationNotSupported:
                objList = []
                number_of_objects = self.properties.network.read(
                    "{} device {} objectList".format(
                        self.properties.address, self.properties.device_id
                    ),
                    arr_index=0,
                    vendor_id=self.properties.vendor_id,
                )

                for i in range(1, number_of_objects + 1):
                    objList.append(
                        self.properties.network.read(
                            "{} device {} objectList".format(
                                self.properties.address, self.properties.device_id
                            ),
                            arr_index=i,
                            vendor_id=self.properties.vendor_id,
                        )
                    )

        points = []
        trendlogs = {}

        def _process_new_objects(obj_cls=NumericPoint, obj_type="analog", objList=None):
            _newpoints = []
            for each in retrieve_type(objList, obj_type):
                point_type = str(each[0])
                point_address = str(each[1])

                if obj_type == "analog":
                    units_state = self.read_single(
                        "{} {} units ".format(point_type, point_address)
                    )
                elif obj_type == "multi":
                    units_state = self.read_single(
                        "{} {} stateText ".format(point_type, point_address)
                    )
                elif obj_type == "binary":
                    units_state = (
                        (
                            self.read_single(
                                "{} {} inactiveText ".format(point_type, point_address)
                            )
                        ),
                        (
                            self.read_single(
                                "{} {} activeText ".format(point_type, point_address)
                            )
                        ),
                    )
                else:
                    units_state = None

                presentValue = self.read_single(
                    "{} {} presentValue ".format(point_type, point_address)
                )
                if obj_type == "analog":
                    presentValue = float(presentValue)

                _newpoints.append(
                    obj_cls(
                        pointType=point_type,
                        pointAddress=point_address,
                        pointName=self.read_single(
                            "{} {} objectName ".format(point_type, point_address)
                        ),
                        description=self.read_single(
                            "{} {} description ".format(point_type, point_address)
                        ),
                        presentValue=presentValue,
                        units_state=units_state,
                        device=self,
                    )
                )
            return _newpoints

        points.extend(_process_new_objects(NumericPoint, "analog", objList))
        points.extend(_process_new_objects(BooleanPoint, "binary", objList))
        points.extend(_process_new_objects(EnumPoint, "multi", objList))
        points.extend(
            _process_new_objects(StringPoint, "characterstringValue", objList)
        )

        for each in retrieve_type(objList, "trendLog"):
            point_address = str(each[1])
            try:
                tl = TrendLog(point_address, self)
            except Exception:
                self._log.error("Problem creating {}".format(each))
                continue
            ldop_type, ldop_addr = (
                tl.properties.log_device_object_property.objectIdentifier
            )
            ldop_prop = tl.properties.log_device_object_property.propertyIdentifier
            trendlogs["{}_{}_{}".format(ldop_type, ldop_addr, ldop_prop)] = (
                tl.properties.object_name,
                tl,
            )

        self._log.info("Ready!")
        return (objList, points, trendlogs)

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
            or command == False
            or command == 0
            or delay == 0
        ):

            if isinstance(self._polling_task.task, DeviceNormalPoll):
                self._polling_task.task.stop()
                while self._polling_task.task.is_alive():
                    pass

                self._polling_task.task = None
                self._polling_task.running = False
                self._log.info("Polling stopped")

        elif self._polling_task.task is None:
            self._polling_task.task = DeviceNormalPoll(
                self, delay=delay, name=self.properties.name
            )
            self._polling_task.task.start()
            self._polling_task.running = True
            self._log.info(
                "Polling started, values read every {} seconds".format(delay)
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
            self._log.info(
                "Polling started, every values read each {} seconds".format(delay)
            )

        else:
            raise RuntimeError("Stop polling before redefining it")
