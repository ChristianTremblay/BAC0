#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Repeat read function every delay
"""

from .TaskManager import Task
#from ..core.devices.Points import Point


class Poll(Task):
    """
    Will fit fan status with fan command
    """

    def __init__(self, points, delay=60):
        """
        :param pointName: (str) name of the point to read
        :param controller: (BAC0.core.devices.Device) Device to read from
        :param delay: (int) Delay between reads in seconds, defaults = 10sec

        :returns: Nothing. Use task.value to read the last value read
        """
        Task.__init__(self, delay)
        self.points = points

    def task(self):
        for point in self.points:
            point.value
