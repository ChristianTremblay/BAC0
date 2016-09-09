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


class Match(Task):
    """
    Will match 2 points (ex. a status with a command)
    """

    def __init__(self, command = None, status = None, delay=5):        
        self.command = command
        self.status = status
        Task.__init__(self, delay=delay, daemon = True)

    def task(self):
        if  self.status.history[-1] != self.command.history[-1]:
            self.status._setitem(self.command.history[-1])        
        
    def stop(self):
        self.status._setitem('auto')
        self.exitFlag = True

class Match_Value(Task):
    """
    Will match 2 points (ex. a status with a command)
    """

    def __init__(self, value = None, point = None, delay=5):        
        self.value = value
        self.point = point
        Task.__init__(self, delay=delay, daemon = True)

    def task(self):
        if hasattr(self.value, '__call__'):
            value = self.value()
        else:
            value = self.value
        if  value != self.point:
            self.point._setitem(value)        
        
    def stop(self):
        self.status._setitem('auto')
        self.exitFlag = True