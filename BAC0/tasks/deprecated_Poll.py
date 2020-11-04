#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Poll.py - create a Polling task to repeatedly read a point.
"""

# --- standard Python modules ---
import weakref

# --- 3rd party modules ---
from bacpypes.core import deferred

# --- this application's modules ---
from .TaskManager import Task
from ..core.utils.notes import note_and_log

# ------------------------------------------------------------------------------


@note_and_log
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
        
        A delay cannot be < 1sec
        This task is meant for single points, so BAC0 will allow short delays.
        This way, a fast polling is available for some points in a device that 
        would not support segmentation.

        :returns: Nothing
        """
        if delay < 1:
            delay = 1
        if point.properties:
            self._point = point
            Task.__init__(self, name="rp_poll", delay=delay)
        else:
            raise ValueError("Provide a point object")

    def task(self):
        self._point.value


@note_and_log
class DevicePoll(Task):
    """
    Start a polling task to repeatedly read a list of points from a device using 
    ReadPropertyMultiple requests.
    """

    def __init__(self, device, delay=10, name="", prefix="basic_poll"):
        """
        :param device: (BAC0.core.devices.Device.Device) device to poll
        :param delay: (int) Delay between polls in seconds, defaults = 10sec
        
        A delay cannot be < 10sec 
        For delays under 10s, use DeviceFastPoll class.

        :returns: Nothing
        """
        self._device = weakref.ref(device)
        Task.__init__(self, name="{}_{}".format(prefix, name), delay=delay, daemon=True)
        self._counter = 0

    @property
    def device(self):
        return self._device()

    def task(self):
        try:
            self.device.read_multiple(
                list(self.device.points_name), points_per_request=25
            )
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
        except ValueError:
            self.device._log.error(
                "Something is wrong with polling...stopping. Try setting off segmentation"
            )
            self.stop()


@note_and_log
class DeviceNormalPoll(DevicePoll):
    """
    Start a normal polling task to repeatedly read a list of points from a device using 
    ReadPropertyMultiple requests.
    
    Normal polling will limit the polling speed to 10 second minimum

    """

    def __init__(self, device, delay=10, name=""):
        """
        :param device: (BAC0.core.devices.Device.Device) device to poll
        :param delay: (int) Delay between polls in seconds, defaults = 10sec
        
        :returns: Nothing
        """
        if delay < 10:
            delay = 10
        self._log.info(
            "Device defined for normal polling with a delay of {}sec".format(delay)
        )
        DevicePoll.__init__(
            self, device=device, name=name, delay=delay, prefix="rpm_normal_poll"
        )


@note_and_log
class DeviceFastPoll(DevicePoll):
    """
    Start a fast polling task to repeatedly read a list of points from a device using 
    ReadPropertyMultiple requests.
    Delay allowed will be 0 to 10 seconds
    Normal polling will limit the polling speed to 10 second minimum

    Warning : Fast polling must be used with care or network flooding may occur

    """

    def __init__(self, device, delay=1, name=""):
        """
        :param device: (BAC0.core.devices.Device.Device) device to poll
        :param delay: (int) Delay between polls in seconds, defaults = 1sec
        
        :returns: Nothing
        """
        if delay < 0:
            delay = 0.01
        elif delay > 10:
            delay = 10
        self._log.warning(
            "Device defined for fast polling with a delay of {}sec".format(delay)
        )
        DevicePoll.__init__(
            self, device=device, name=name, delay=delay, prefix="rpm_fast_poll"
        )
