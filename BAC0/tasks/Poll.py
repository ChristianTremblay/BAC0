#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Poll.py - create a Polling task to repeatedly read a point.
'''

#--- standard Python modules ---
import weakref

#--- 3rd party modules ---
from bacpypes.core import deferred

#--- this application's modules ---
from .TaskManager import Task

#------------------------------------------------------------------------------

class SimplePoll(Task):
    """
    Start a polling task to repeatedly read a point's Present_Value.
    ex.
        device['point_name'].poll(delay=60)
    """

    def __init__(self, point, *, delay=10):
        """
        :param point: (BAC0.core.device.Points.Point) name of the point to read
        :param delay: (int) Delay between reads in seconds, defaults = 10sec
        
        A delay cannot be < 5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        if delay < 5:
            delay = 5
        if point.properties:
            self._point = point
            Task.__init__(self, name='rp_poll', delay=delay)
        else:
            raise ValueError('Provide a point object')

    def task(self):
        self._point.value


class DevicePoll(Task):
    """
    Start a polling task to repeatedly read a list of points from a device using 
    ReadPropertyMultiple requests.
    """

    def __init__(self, device, delay=10):
        """
        :param device: (BAC0.core.devices.Device.Device) device to poll
        :param delay: (int) Delay between polls in seconds, defaults = 10sec
        
        A delay cannot be < 5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        if delay < 5:
            delay = 5
        self._device = weakref.ref(device)
        Task.__init__(self, name='rpm_poll', delay=delay, daemon = True)
        self._counter = 0

    @property
    def device(self):
        return self._device()

    def task(self):
        try:
            self.device.read_multiple(list(self.device.points_name), points_per_request=25)
            self._counter += 1
            if self._counter == self.device.properties.auto_save:
                self.device.save()
                if self.device.properties.clear_history_on_save:
                    self.device.clear_histories()
                self._counter = 0
        except AttributeError:
            # This error can be seen when defining a controller on a busy network...
            # When creation fail, polling is created and fail the first time...
            # So kill the task
            self.stop()
