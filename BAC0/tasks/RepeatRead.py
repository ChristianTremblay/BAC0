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
from ..core.devices.Device import Device

import pandas as pd
from datetime import datetime

class RepeatRead(Task):
    """
    Will fit fan status with fan command
    """
    def __init__(self,pointName, controller, delay = 10):
        """
        :param pointName: (str) name of the point to read
        :param controller: (BAC0.core.devices.Device) Device to read from
        :param delay: (int) Delay between reads in seconds, defaults = 10sec
        
        :returns: Nothing. Use task.value to read the last value read        
        """
        Task.__init__(self, delay = delay)
        self.pointName = pointName
        self.controller = controller
        self.values = []
        self.index = []
        if not type(controller) == Device:
            raise ValueError('controller bad type')
        
    def task(self):
        res = self.controller.read(self.pointName)
        self.index.append(datetime.now())
        self.values.append(res.value())
             
    def getValues(self):
        ts = pd.Series(self.values, index=self.index)
        return ts
        
    def getValue(self):
        return self.getValues()[-1]
        