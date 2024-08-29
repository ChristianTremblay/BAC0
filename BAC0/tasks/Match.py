#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Match.py - verify a point's status matches its commanded value.

Example:
    Is a fan commanded to 'On' actually 'running'?
"""

# --- standard Python modules ---
# --- 3rd party modules ---

import asyncio

from ..core.utils.notes import note_and_log
from ..core.io.IOExceptions import NotReadyError

# --- this application's modules ---
from .TaskManager import Task

# ------------------------------------------------------------------------------


@note_and_log
class Match(Task):
    """
    Match two properties of a BACnet Object (i.e. a point status with its command).
    """

    def __init__(self, status=None, command=None, delay=5, name=None):
        self._log.debug(
            f"Creating Match task for {command} and {status}. Delay : {delay}"
        )
        if not name:
            name = "Match on " + status.properties.name
        self.command = command
        self.status = status
        Task.__init__(self, delay=delay, name=name)

    async def task(self):
        if (
            self.status.properties.network.initialized is False
            or self.status.properties.network.initialized is None
            or self.status is None
        ):
            raise NotReadyError(f"{self.status} is not ready")
        if (
            self.command.properties.network.initialized is False
            or self.command.properties.network.initialized is None
            or self.command is None
        ):
            raise NotReadyError(f"{self.command} is not ready")
        try:
            if self.status.history[-1] != self.command.history[-1]:
                _val = (
                    self.command.history[-1].split(":")[1]
                    if ":" in self.command.history[-1]
                    else self.command.history[-1]
                )
                self.log(f"Match value is {_val}", level="debug")
                await self.status._setitem(_val.replace(" ", ""))
        except (NotReadyError, TypeError) as error:
            self.log(
                f"Problem executing match value task {self.status.name} -> {self.command.name} : {error}",
                level="warning",
            )
        except Exception as error:
            self._log.error(
                f"Something wrong matching {self.command.properties.name} and {self.status.properties.name}... try again next time...\nError:{error}"
            )
            await asyncio.sleep(1)

    async def stop(self):
        await self.status._setitem("auto")
        super().stop()


@note_and_log
class Match_Value(Task):
    """
    Verify a point's Present_Value equals the given value after a delay of X seconds.
    Thus giving the BACnet controller (and connected equipment) time to respond to the
    command.

        Match_Value(On, <AI:1>, 5)

    i.e. Does Fan value = On after 5 seconds.
    """

    def __init__(
        self, value=None, point=None, delay=5, name=None, use_last_value=False
    ):
        self.log(f"Creating MatchValue task for {value} and {point}", level="debug")
        # if not isinstance(value, (float, int, str, bool)) or not hasattr(self.value, "__call__"):
        #    raise ValueError("Value must be a float, int, str or bool OR must be a callable function that returns one of these types.")
        self.value = value
        self.point = point
        self.use_last_value = use_last_value
        if not name:
            name = "Match_Value on " + point.properties.name
        Task.__init__(self, delay=delay, name=name)

    async def task(self):
        if (
            self.point.properties.device.initialized is False
            or self.point.properties.device.initialized is None
            or self.point is None
        ):
            raise NotReadyError(f"{self.point} is not ready")
        try:
            if self.use_last_value:
                _point = self.point.lastValue
            else:
                _point = await self.point.value
            value = self.value() if hasattr(self.value, "__call__") else self.value
            if value != _point:
                await self.point._set(value=value)
        except (NotReadyError, TypeError) as error:
            self.log(
                f"Problem executing match value task on {self.point.name} -> {value}: {error}",
                level="warning",
            )
            await asyncio.sleep(1)
        except Exception as error:
            self.log(
                f"Something is wrong matching {self.value} and {self.point.properties.name}... try again next time {error}",
                level="error",
            )
            await asyncio.sleep(1)

    async def _before_stop(self):
        try:
            await self.point._set("auto")
        except (ValueError, TypeError):
            self.log(
                "Could not set {} to auto. If this is a network input, it is normal as we didn't have to override or simulate".format(
                    self.point
                ),
                level="warning",
            )

    async def stop(self):
        await self._before_stop()
        super().stop()
