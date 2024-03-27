#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Poll.py - create a Polling task to repeatedly read a point.
"""

import typing as t

# --- standard Python modules ---
import weakref

from ..core.utils.notes import note_and_log

# --- this application's modules ---
from .TaskManager import Task

if t.TYPE_CHECKING:
    from ..core.devices.Device import RPDeviceConnected, RPMDeviceConnected


# ------------------------------------------------------------------------------
class MultiplePollingFailures(Exception):
    pass


@note_and_log
class SimplePoll(Task):
    """
    Start a polling task to repeatedly read a point's Present_Value.
    ex.
        device['point_name'].poll(delay=60)
    """

    def __init__(self, point, *, delay: int = 10) -> None:
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

    async def task(self):
        await self._point.value


@note_and_log
class DevicePoll(Task):
    """
    Start a polling task to repeatedly read a list of points from a device using
    ReadPropertyMultiple requests.
    """

    def __init__(
        self,
        device: t.Union["RPMDeviceConnected", "RPDeviceConnected"],
        delay: int = 10,
        name: str = "",
        prefix: str = "basic_poll",
    ) -> None:
        """
        :param device: (BAC0.core.devices.Device.Device) device to poll
        :param delay: (int) Delay between polls in seconds, defaults = 10sec

        A delay cannot be < 10sec
        For delays under 10s, use DeviceFastPoll class.

        :returns: Nothing
        """
        self.failures = 0
        self.MAX_FAILURES = 3
        self._device = weakref.ref(device)
        Task.__init__(self, name=f"{prefix}_{name}", delay=delay)
        self._counter = 0

    @property
    def device(self) -> t.Union["RPMDeviceConnected", "RPDeviceConnected", None]:
        return self._device()

    async def task(self) -> None:
        if self.device.properties.ping_failures > 0:
            self.device._log.warning(
                "{} ({}) | Ping failed, skipping polling for now. Resending a ping to speed up things".format(
                    self.device.properties.name, self.device.properties.address
                )
            )
            await self.device.ping()
            return
        try:
            if self.failures >= self.MAX_FAILURES:
                raise MultiplePollingFailures(
                    "{} ({}) | Polling failed numerous times in a row... let see what we can do".format(
                        self.device.properties.name, self.device.properties.address
                    )
                )
            await self.device.read_multiple(
                list(self.device.pollable_points_name), points_per_request=25
            )
            self._counter += 1
            if self._counter == self.device.properties.auto_save:
                self.device.save(resampling=self.device.properties.save_resampling)
                if self.device.properties.clear_history_on_save:
                    self.device.clear_histories()
                self._counter = 0
            self.failures = 0
        except AttributeError as e:
            # This error can be seen when defining a controller on a busy network...
            # When creation fail, polling is created and fail the first time...
            # So kill the task
            self.device._log.error(
                "{} ({}) | Something is wrong while creating the polling task.\nError: {} | Type : {}".format(
                    self.device.properties.name,
                    self.device.properties.address,
                    e,
                    type(e),
                )
            )
            # self.stop()
            self.failures += 1
        except ValueError as e:
            self.failures += 1
            self.device._log.error(
                "{} ({}) | Polling results contains a wrong value. Probably a communication error. Will skip this result and wait for the next cycle.\nError: {} | Type : {}".format(
                    self.device.properties.name,
                    self.device.properties.address,
                    e,
                    type(e),
                )
            )
            pass

        except MultiplePollingFailures as e:
            self.device._log.warning(
                "{} ({}) | Trying to ping device then we'll reset the number of failures and get back with polling\nError: {}| Type : {}".format(
                    self.device.properties.name,
                    self.device.properties.address,
                    e,
                    type(e),
                )
            )
            if await self.device.ping():
                self.failures = 0


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
        self._log.info(f"Device defined for normal polling with a delay of {delay}sec")
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
        self._log.warning(f"Device defined for fast polling with a delay of {delay}sec")
        DevicePoll.__init__(
            self, device=device, name=name, delay=delay, prefix="rpm_fast_poll"
        )
