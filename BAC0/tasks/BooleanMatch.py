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


class BooleanMatch(Task):
    """
    Will fit fan status with fan command
    """

    def __init__(self, boolCommand, boolStatus, controller, delay=5):
        Task.__init__(self, delay=delay)
        self.command = boolCommand
        self.status = boolStatus
        self.controller = controller

    def task(self):
        if self.controller.read(self.command) == 'active':
            self.controller.sim('%s %s' % (self.status, 'active'))
        else:
            self.controller.sim('%s %s' % (self.status, 'inactive'))

    def beforeStop(self):
        self.controller.release(self.status)
