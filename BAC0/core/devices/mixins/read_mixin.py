#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
read_mixin.py - Add ReadProperty and ReadPropertyMultiple to a device 
'''
#--- standard Python modules ---

#--- 3rd party modules ---

#--- this application's modules ---
from ....tasks.Poll import DevicePoll
from ...io.IOExceptions import ReadPropertyMultipleException, NoResponseFromController, SegmentationNotSupported
from ..Points import NumericPoint, BooleanPoint, EnumPoint, OfflinePoint
from ..Trends import TrendLog

#------------------------------------------------------------------------------

def retrieve_type(obj_list, point_type_key):
    for point_type, point_address in obj_list:
        if point_type_key in str(point_type):
            yield (point_type, point_address)


class ReadPropertyMultiple():
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
            yield request[i:i + points_per_request]


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

            str_list.append(' ' + point.properties.type)
            str_list.append(' ' + str(point.properties.address))
            str_list.append(' presentValue')
            rpm_param = (''.join(str_list))
            requests.append(rpm_param)

        return (requests, points)


    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6), force_single=False):
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
        if not self.properties.pss['readPropertyMultiple'] or force_single:
            self._log.warning('Read property Multiple Not supported')
            self.read_single(points_list,points_per_request=1, discover_request=discover_request)
        else:
            if not self.properties.segmentation_supported:
                points_per_request = 1

            if discover_request[0]:
                values = []
                info_length = discover_request[1]
                big_request = discover_request[0]

                for request in self._batches(big_request, points_per_request):
                    try:
                        request = ('{} {}'.format(self.properties.address, ''.join(request)))
                        self._log.debug('RPM_Request: %s ' % request)
                        val = self.properties.network.readMultiple(request)

                        #print('val : ', val, len(val), type(val))
                        if val == None:
                            self.properties.segmentation_supported = False
                            raise SegmentationNotSupported

                    except KeyError as error:
                        raise Exception('Unknown point name : %s' % error)

                    except SegmentationNotSupported as error:
                        self.properties.segmentation_supported = False
                        #self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)
                        self._log.warning('Segmentation not supported')
                        self._log.warning('Request too big...will reduce it')
                        if points_per_request == 1:
                            raise
                        self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)

                    else:
                        for points_info in self._batches(val, info_length):
                            values.append(points_info)
                return values

            else:
                big_request = self._rpm_request_by_name(points_list)
                i = 0
                for request in self._batches(big_request[0], points_per_request):
                    try:
                        request = ('{} {}'.format(self.properties.address, ''.join(request)))
                        val = self.properties.network.readMultiple(request)

                    except SegmentationNotSupported as error:
                        self.properties.segmentation_supported = False
                        self.read_multiple(points_list,points_per_request=1, discover_request=discover_request)

                    except KeyError as error:
                        raise Exception('Unknown point name : %s' % error)

                    else:
                        points_values = zip(big_request[1][i:i + len(val)], val)
                        i += len(val)
                        for each in points_values:
                            each[0]._trend(each[1])


    def read_single(self, points_list, *, points_per_request=1, discover_request=(None, 4)):
        if discover_request[0]:
            values = []
            info_length = discover_request[1]
            big_request = discover_request[0]

            for request in self._batches(big_request, points_per_request):
                try:
                    request = ('{} {}'.format(self.properties.address, ''.join(request)))
                    val = self.properties.network.read(request)

                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)

                # Save each value to history of each point
                for points_info in self._batches(val, info_length):
                    values.append(points_info)

            return values

        else:
            big_request = self._rpm_request_by_name(points_list)
            i = 0
            for request in self._batches(big_request[0], points_per_request):
                try:
                    request = ('{} {}'.format(self.properties.address, ''.join(request)))
                    val = self.properties.network.read(request)
                    points_values = zip(big_request[1][i:i + len(val)], val)
                    i += len(val)
                    for each in points_values:
                        each[0]._trend(each[1])

                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)


    def _discoverPoints(self, custom_object_list = None):
        if custom_object_list:
            objList = custom_object_list
        else:
            try :
                    objList = self.properties.network.read(
                    '{} device {} objectList'.format(self.properties.address, self.properties.device_id))

            except NoResponseFromController:
                self.log.error('No object list available. Please provide a custom list using the object_list parameter')
                objList = []

            except SegmentationNotSupported:
                objList = []
                number_of_objects = self.properties.network.read(
                    '{} device {} objectList'.format(self.properties.address, self.properties.device_id), arr_index = 0)

                for i in range(1,number_of_objects+1):
                    objList.append(self.properties.network.read(
                        '{} device {} objectList'.format(self.properties.address, self.properties.device_id), arr_index = i))

        points = []
        trendlogs = {}


        # Numeric
        analog_request = []
        list_of_analog = retrieve_type(objList, 'analog')
        for analog_points, address in list_of_analog:
            analog_request.append('{} {} objectName presentValue units description '.format(analog_points, address))

        try:
            analog_points_info = self.read_multiple('', discover_request=(analog_request, 4), points_per_request=5)
            self._log.debug(analog_points_info)
        except SegmentationNotSupported:
            raise

        i = 0
        for each in retrieve_type(objList, 'analog'):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = analog_points_info[i]

            if len(point_infos) == 4:
                point_units_state = point_infos[2]
                point_description = point_infos[3]

            elif len(point_infos) == 3:
                #we probably get only objectName, presentValue and units
                point_units_state = point_infos[2]
                point_description = ""

            elif len(point_infos) == 2:
                point_units_state = ""
                point_description = ""

            else:
                #raise ValueError('Not enough values returned', each, point_infos)
                # SHOULD SWITCH TO SEGMENTATION_SUPPORTED = FALSE HERE
                self._log.warning('Cannot add {} / {} | {}'.format(point_type, point_address, len(point_infos)))
                continue

            i += 1
            try:
                points.append(
                    NumericPoint(
                        pointType=point_type,   pointAddress=point_address, pointName=point_infos[0],
                        description=point_description,  presentValue=float(point_infos[1]), units_state=point_units_state,
                        device=self, history_size=self.properties.history_size))
            except IndexError:
                self._log.warning('There has been a problem defining analog points. It is sometimes due to busy network. Please retry the device creation')
                raise

        multistate_request = []
        list_of_multistate = retrieve_type(objList, 'multi')
        for multistate_points, address in list_of_multistate:
            multistate_request.append('{} {} objectName presentValue stateText description '.format(multistate_points, address))

        try:
            multistate_points_info= self.read_multiple('', discover_request=(multistate_request, 4), points_per_request=5)
        except SegmentationNotSupported:
            raise

        i = 0
        for each in retrieve_type(objList, 'multi'):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = multistate_points_info[i]
            i += 1

            try:
                points.append(
                    EnumPoint(
                        pointType=point_type,       pointAddress=point_address,     pointName=point_infos[0],
                        description=point_infos[3], presentValue=point_infos[1],    units_state=point_infos[2],
                        device=self, history_size=self.properties.history_size))
            except IndexError:
                self._log.warning('There has been a problem defining multistate points. It is sometimes due to busy network. Please retry the device creation')
                raise

        binary_request = []
        list_of_binary = retrieve_type(objList, 'binary')
        for binary_points, address in list_of_binary:
            binary_request.append('{} {} objectName presentValue inactiveText activeText description '.format(binary_points, address))

        try:
            binary_points_info= self.read_multiple('', discover_request=(binary_request, 5), points_per_request=5)
        except SegmentationNotSupported:
            raise

        i = 0
        for each in retrieve_type(objList, 'binary'):
            point_type = str(each[0])
            point_address = str(each[1])
            point_infos = binary_points_info[i]

            if len(point_infos) == 3:
                #we probably get only objectName, presentValue and description
                point_units_state = ('OFF', 'ON')
                point_description = point_infos[2]

            elif len(point_infos) == 5:
                point_units_state = (point_infos[2], point_infos[3])
                point_description = point_infos[4]

                if point_description is None:
                    point_description = ""

            elif len(point_infos) == 2:
                point_units_state = ('OFF', 'ON')
                point_description = ""

            else:
                #raise ValueError('Not enough values returned', each, point_infos)
                # SHOULD SWITCH TO SEGMENTATION_SUPPORTED = FALSE HERE
                self._log.warning('Cannot add {} / {}'.format(point_type, point_address))
                continue

            i += 1
            try:
                points.append(
                    BooleanPoint(
                        pointType=point_type,           pointAddress=point_address,     pointName=point_infos[0],
                        description=point_description,  presentValue=point_infos[1],    units_state=point_units_state,
                        device=self, history_size=self.properties.history_size))
            except IndexError:
                self._log.warning('There has been a problem defining binary points. It is sometimes due to busy network. Please retry the device creation')
                raise

        #trenLogs_request = []
        #list_of_trendLogs = retrieve_type(objList, 'trendLog')
        #for binary_points, address in list_of_trendLogs:
        #    trendLogs_request.append('{} {}')
        for each in retrieve_type(objList, 'trendLog'):
            point_address = str(each[1])
            tl = TrendLog(point_address, self, read_log_on_creation=False)
            ldop_type,ldop_addr = tl.properties.log_device_object_property.objectIdentifier
            ldop_prop = tl.properties.log_device_object_property.propertyIdentifier
            trendlogs['{}_{}_{}'.format(ldop_type, ldop_addr, ldop_prop)]=(tl.properties.object_name, tl)

            
        self._log.info('Ready!')
        return (objList, points, trendlogs)


    def poll(self, command='start', *, delay=10):
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
        if str(command).lower() == 'stop' \
                or command == False \
                or command == 0 \
                or delay == 0:

            if isinstance(self._polling_task.task, DevicePoll):
                self._polling_task.task.stop()
                while self._polling_task.task.is_alive():
                    pass

                self._polling_task.task = None
                self._polling_task.running = False
                self._log.info('Polling stopped')

        elif self._polling_task.task is None:
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            self._log.info('Polling started, values read every {} seconds'.format(delay))

        elif self._polling_task.running:
            self._polling_task.task.stop()
            while self._polling_task.task.is_alive():
                pass
            self._polling_task.running = False
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            self._log.info('Polling started, every values read each %s seconds' % delay)

        else:
            raise RuntimeError('Stop polling before redefining it')


class ReadProperty():
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
            yield request[i:i + points_per_request]


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

            str_list.append(' ' + point.properties.type)
            str_list.append(' ' + str(point.properties.address))
            str_list.append(' presentValue')
            rpm_param = (''.join(str_list))
            requests.append(rpm_param)

        return (requests, points)


    def read_multiple(self, points_list, *, points_per_request=1, discover_request=(None, 6)):
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
        #print('PSS : %s' % self.properties.pss['readPropertyMultiple'])
        if isinstance(points_list, list):
            for each in points_list:
                self.read_single(each,points_per_request=1, discover_request=discover_request)
        else:
            self.read_single(points_list,points_per_request=1, discover_request=discover_request)

    def read_single(self, request, *, points_per_request=1, discover_request=(None, 4)):
        try:
            request = ('{} {}'.format(self.properties.address, ''.join(request)))
            return self.properties.network.read(request)
        except KeyError as error:
            raise Exception('Unknown point name: %s' % error)

        except NoResponseFromController as error:
            return ''


    def _discoverPoints(self, custom_object_list = None):
        if custom_object_list:
            objList = custom_object_list
        else:
            try : 
                objList = self.properties.network.read('{} device {} objectList'.format(
                              self.properties.address, self.properties.device_id))

            except SegmentationNotSupported:
                objList = []
                number_of_objects = self.properties.network.read(
                    '{} device {} objectList'.format(self.properties.address, self.properties.device_id), arr_index = 0)

                for i in range(1,number_of_objects+1):
                    objList.append(self.properties.network.read(
                    '{} device {} objectList'.format(self.properties.address, self.properties.device_id), arr_index = i))

        points = []
        trendlogs = {}


        # Numeric
        for each in retrieve_type(objList, 'analog'):
            point_type = str(each[0])
            point_address = str(each[1])

            points.append(
                NumericPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=self.read_single('{} {} objectName '.format(point_type, point_address)),
                    description=self.read_single('{} {} description '.format(point_type, point_address)),
                    presentValue=float(
                        self.read_single('{} {} presentValue '.format(point_type, point_address))),
                    units_state=self.read_single('{} {} units '.format(point_type, point_address)),
                    device=self))

        for each in retrieve_type(objList, 'multi'):
            point_type = str(each[0])
            point_address = str(each[1])

            points.append(
                EnumPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=self.read_single('{} {} objectName '.format(point_type, point_address)),
                    description=self.read_single('{} {} description '.format(point_type, point_address)),

                    presentValue=(self.read_single('{} {} presentValue '.format(point_type, point_address)),),
                    units_state=self.read_single('{} {} stateText '.format(point_type, point_address)),
                    device=self))

        for each in retrieve_type(objList, 'binary'):
            point_type = str(each[0])
            point_address = str(each[1])

            points.append(
                BooleanPoint(
                    pointType=point_type,
                    pointAddress=point_address,
                    pointName=self.read_single('{} {} objectName '.format(point_type, point_address)),
                    description=self.read_single('{} {} description '.format(point_type, point_address)),

                    presentValue=(self.read_single('{} {} presentValue '.format(point_type, point_address)),),
                    units_state=(
                                (self.read_single('{} {} inactiveText '.format(point_type, point_address))),
                                (self.read_single('{} {} activeText '.format(point_type, point_address)))
                                 ), 
                    device=self))

        for each in retrieve_type(objList, 'trendLog'):
            point_address = str(each[1])
            tl = trendLogs(point_address, self)
            ldop_type, ldop_addr = tl.properties.log_device_object_property.objectIdentifier
            ldop_prop = tl.propertires.log_device_object_property.propertyIdentifier
            trendlogs['{}_{}_{}'.format(ldop_type, ldop_addr, ldop_prop)] = (tl.properties.object_name,tl)
            
        self._log.info('Ready!')
        return (objList, points, trendlogs)


    def poll(self, command='start', *, delay=120):
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
        if delay > 120:
            self._log.warning('Segmentation not supported, forcing delay to 120 seconds (or higher)')
            delay = 120
        #for each in self.points:
        #    each.value
        #self._log.info('Complete')
        if str(command).lower() == 'stop' \
                or command == False \
                or command == 0 \
                or delay == 0:

            if isinstance(self._polling_task.task, DevicePoll):
                self._polling_task.task.stop()
                while self._polling_task.task.is_alive():
                    pass

                self._polling_task.task = None
                self._polling_task.running = False
                self._log.info('Polling stopped')

        elif self._polling_task.task is None:
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            self._log.info('Polling started, values read every {} seconds'.format(delay))

        elif self._polling_task.running:
            self._polling_task.task.stop()
            while self._polling_task.task.is_alive():
                pass
            self._polling_task.running = False
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            self._log.info('Polling started, every values read each %s seconds' % delay)

        else:
            raise RuntimeError('Stop polling before redefining it')
