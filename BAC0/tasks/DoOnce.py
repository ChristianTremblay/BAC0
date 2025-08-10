#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
DoOnce.py - execute a task once
"""

import asyncio

from ..core.utils.notes import note_and_log
from .TaskManager import OneShotTask


@note_and_log
class DoOnce(OneShotTask):
    """
    Execute a function once, optionally awaiting it if it's a coroutine.

    Example::

        device['point_name'].poll(delay=60)
    """

    def __init__(self, fn: callable, args: str = None):
        """
        :param point: (BAC0.core.device.Points.Point) name of the point to read
        :param delay: (int) Delay between reads in seconds, defaults = 10sec

        A delay cannot be < 5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        super().__init__(fn, args)

    async def task(self):
        if asyncio.iscoroutinefunction(self.fn):
            self._log.debug(f"Running {self.name} with args {self.args}")
            await self.fn(self.args)
        else:
            self.fn(self.args)
