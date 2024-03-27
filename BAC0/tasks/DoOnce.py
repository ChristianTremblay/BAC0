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
    Start a polling task which is in fact a recurring read of the point.
    ex.
        device['point_name'].poll(delay=60)
    """

    def __init__(self, fnc, name="do_once"):
        """
        :param point: (BAC0.core.device.Points.Point) name of the point to read
        :param delay: (int) Delay between reads in seconds, defaults = 10sec

        A delay cannot be < 5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        self.name = name
        self.fnc_args = None
        if isinstance(fnc, tuple):
            self.func, self.fnc_args = fnc
        elif hasattr(fnc, "__call__"):
            self.func = fnc
            OneShotTask.__init__(self)
        else:
            raise ValueError("You must pass a function to this...")

    async def task(self):
        if self.fnc_args:
            if asyncio.iscoroutinefunction(self.func):
                self._log.debug(
                    f"Running {self.func.__name__} with args {self.fnc_args}"
                )
                await self.func(self.fnc_args)
            else:
                self.func(self.fnc_args)
        else:
            if asyncio.iscoroutinefunction(self.func):
                self.log(f"Running {self.func.__name__}", level="debug")
                await self.func()
            else:
                self.func()
