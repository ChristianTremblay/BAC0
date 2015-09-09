#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Change Fan status based on Fan Command
"""

from .TaskManager import Task
from ..core.devices.Device import Device

class BooleanMatch(Task):
    """
    Will fit fan status with fan command
    """
    def __init__(self, boolCommand, boolStatus, controller, delay = 2):
        Task.__init__(self, delay = 5)
        self.command = boolCommand
        self.status = boolStatus
        self.controller = controller
        if not type(controller) == Device:
            raise ValueError('controller bad type')
        
    def task(self):
        if self.controller.read(self.boolCommand) == 'active':
            self.controller.sim('%s %s' % (self.boolStatus, 'active'))
        else:
            self.controller.sim('%s %s' % (self.boolStatus, 'inactive'))
            
    def beforeStop(self):
        self.controller.release(self.boolStatus)
        