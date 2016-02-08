# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 20:45:24 2016

@author: CTremblay
"""

from ....tasks.Poll import DevicePoll
from ...io.IOExceptions import ReadPropertyMultipleException


class Read():
    """
    This is a Mixin that will handle ReadProperty and ReadPropertyMultiple
    for a device
    """
    def _batches(self, request, points_per_request):
        """
        Generator that creates request batches.
        Each batch will contain a maximum of
        "points_per_request" points to read.
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

    def read_multiple(self, points_list, *, points_per_request=25, discover_request=(None, 6)):
        """
        Functions to read points from a device using the read property
        multiple request.
        Using readProperty request can be very slow to read a lot of data.

        :param points_list: (list) a list of all point_name as str
        :param points_per_request: (int) number of points in the request

        Using too many points will create big requests needing segmentation.
        It's better to use just enough request so the message will not require
        segmentation.

        :Example:

        device.read_multiple(['point1', 'point2', 'point3'], points_per_request = 10)
        """
        if not self.properties.pss['readPropertyMultiple']:
            raise ReadPropertyMultipleException('Not supported on device')
        if discover_request[0]:
            values = []
            info_length = discover_request[1]
            big_request = discover_request[0]
            # print(big_request)
            for request in self._batches(big_request,
                                         points_per_request):
                try:

                    request = ('%s %s' %
                               (self.properties.address, ''.join(request)))

                    val = self.properties.network.readMultiple(request)
                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)
                # Save each value to history of each point
                for points_info in self._batches(val, info_length):
                    values.append(points_info)
            return values
        else:
            big_request = self._rpm_request_by_name(points_list)
            i = 0
            for request in self._batches(big_request[0],
                                         points_per_request):
                try:
                    request = ('%s %s' %
                               (self.properties.address, ''.join(request)))
                    val = self.properties.network.readMultiple(request)
                    points_values = zip(big_request[1][i:i + len(val)], val)
                    i += len(val)
                    for each in points_values:
                        each[0]._trend(each[1])
                except KeyError as error:
                    raise Exception('Unknown point name : %s' % error)
                # Save each value to history of each point

    def poll(self, command='start', *, delay=10):
        """
        Enable polling of a variable. Will be read every x seconds (delay=x sec)
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
                print('Polling stopped')
        elif self._polling_task.task is None:
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            print('Polling started, every values read each %s seconds' % delay)
        elif self._polling_task.running:
            self._polling_task.task.stop()
            while self._polling_task.task.is_alive():
                pass
            self._polling_task.running = False
            self._polling_task.task = DevicePoll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True
            print('Polling started, every values read each %s seconds' % delay)
        else:
            raise RuntimeError('Stop polling before redefining it')
