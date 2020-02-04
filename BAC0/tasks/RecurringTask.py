#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
RecurringTask.py - execute a recurring task 
"""

from .TaskManager import Task
from ..core.utils.notes import note_and_log


@note_and_log
class RecurringTask(Task):
    """
    Start a recurring task (a function passed)
    """

    def __init__(self, fnc, delay=60, name="recurring"):
        """
        :param point: (BAC0.core.device.Points.Point) name of the point to read
        :param delay: (int) Delay between reads in seconds, defaults = 10sec
        
        A delay cannot be < 5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        if hasattr(fnc, "__call__"):
            self.func = fnc
            Task.__init__(self, name=name, delay=delay)
        else:
            raise ValueError("You must pass a function to this...")

    def task(self):
        self.func()
