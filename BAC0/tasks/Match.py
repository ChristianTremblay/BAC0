#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Match.py - verify a point's status matches its commanded value.

Example:
    Is a fan commanded to 'On' actually 'running'?
'''

#--- standard Python modules ---
#--- 3rd party modules ---

#--- this application's modules ---
from .TaskManager import Task

#------------------------------------------------------------------------------

class Match(Task):
    """
    Match two properties of a BACnet Object (i.e. a point status with its command).
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
    Verify a point's Present_Value equals the given value after a delay of X seconds.
    Thus giving the BACnet controller (and connected equipment) time to respond to the
    command.
    
        Match_Value(On, <AI:1>, 5)
        
    i.e. Does Fan value = On after 5 seconds. 
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
        if  value != self.point.value:
            self.point._set(value)        


    def stop(self):
        self.point._set('auto')
        self.exitFlag = True
