#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
DoOnce.py - execute a task once
"""

from .TaskManager import OneShotTask
from ..core.utils.notes import note_and_log


@note_and_log
class DoOnce(OneShotTask):
    """
    Start a polling task which is in fact a recurring read of the point.
    ex.
        device['point_name'].poll(delay=60)
    """

    def __init__(self, fnc):
        """
        :param point: (BAC0.core.device.Points.Point) name of the point to read
        :param delay: (int) Delay between reads in seconds, defaults = 10sec
        
        A delay cannot be < 5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        if hasattr(fnc, "__call__"):
            self.func = fnc
            OneShotTask.__init__(self)
        else:
            raise ValueError("You must pass a function to this...")

    def task(self):
        self.func()
