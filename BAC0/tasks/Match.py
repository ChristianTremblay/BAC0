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
            "Creating Match task for {} and {}. Delay : {}".format(
                command, status, delay
            )
        )
        if not name:
            name = "Match on " + status.properties.name
        self.command = command
        self.status = status
        Task.__init__(self, delay=delay, name=name)

    async def task(self):
        try:
            if self.status.history[-1] != self.command.history[-1]:
                _val = (
                    self.command.history[-1].split(":")[1]
                    if ":" in self.command.history[-1]
                    else self.command.history[-1]
                )
                self._log.debug(f"Match value is {_val}")
                await self.status._setitem(_val.replace(" ", ""))
        except Exception:
            self._log.error(
                "Something wrong matching {} and {}... try again next time...".format(
                    self.command, self.status
                )
            )

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
        self._log.debug("Creating MatchValue task for {} and {}".format(value, point))
        #if not isinstance(value, (float, int, str, bool)) or not hasattr(self.value, "__call__"):
        #    raise ValueError("Value must be a float, int, str or bool OR must be a callable function that returns one of these types.")
        self.value = value
        self.point = point
        self.use_last_value = use_last_value
        if not name:
            name = "Match_Value on " + point.properties.name
        Task.__init__(self, delay=delay, name=name)

    async def task(self):
        try:
            if self.use_last_value:
                _point = self.point.lastValue
            else:
                _point = await self.point.value
            value = (
                self.value() if hasattr(self.value, "__call__") else self.value
            )
            if value != _point:
                await self.point._set(value)
        except Exception as error:
            self._log.error(
                f"Something is wrong matching {self.value} and {self.point}... try again next time {error}"
            )

    async def _before_stop(self):
        try:
            await self.point._set("auto")
        except ValueError:
            self._log.warning(
                "Could not set {} to auto. If this is a network input, it is normal as we didn't have to override or simulate".format(self.point)
            )

    async def stop(self):
        await self._before_stop()
        super().stop()
