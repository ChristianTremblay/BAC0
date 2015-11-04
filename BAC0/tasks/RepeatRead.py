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
from ..core.devices.Points import Point

class RepeatRead(Task):
    """
    Will fit fan status with fan command
    """

    def __init__(self, point, *, delay=10):
        """
        :param point: (BAC0.core.device.Points.Point) name of the point to read
        :param delay: (int) Delay between reads in seconds, defaults = 10sec
        
        A delay cannot be < 0.5sec (there are risks of overloading the device)

        :returns: Nothing
        """
        if delay < 0.5:
            delay = 0.5
        if isinstance(point,Point):
            Task.__init__(self, delay=delay)
            self.pointName = point.properties.name
            self.controller = point.properties.device
        else:
            raise ValueError('Should provide a point object')

    def task(self):
        self.controller.get(self.pointName)
