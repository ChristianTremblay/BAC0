#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Definition of points so operations will be easier on read result
"""

import pandas as pd
from datetime import datetime

class Point():
    """
    This represents a point inside a device. This base class will be used to build NumericPoint, BooleanPoint and EnumPoints

    Each point implement a history feature. Each time the point is read, the value with timstampe is added to a
    history table. It's then possible to look what happened since the creation of the point.
        
    """
    def __init__(self, device = None, pointType = None, pointAddress=None, pointName = None, description = None, presentValue = None, units_state = None): 
        #self._value = presentValue
        #self._status = ''
        self._units_state = units_state
        self._history = []
        self._history.append(presentValue)
        self._historyIndex = []
        self._historyIndex.append(datetime.now())
        
        self.simulated = False
        self.overridden = False
        
        self.device = device
        self.name = pointName
        self.pointType = pointType
        self.pointAddr = pointAddress
        self.description = description
        
    @property     
    def value(self):
        """
        Retrieve value of the point
        """
        res = self.device.read(self.name)
        self._historyIndex.append(datetime.now())
        self._history.append(res)
        return res

    # Is this truly necessary ????
    @value.setter
    def value(self,value):
        raise AttributeError('Must be set from network request')
    
    
    @property         
    def units(self):
        raise Exception('Must be overridden')
        
    @property
    def lastValue(self):
        return self._history[-1]
            
    def showHistoryTable(self):
        ts = pd.Series(self._history, index=self._historyIndex)
        return ts
        
    def chart(self):
        return self.showHistoryTable().plot()

        
class NumericPoint(Point):
    """
    Representation of a Numeric information
    """
    def __init__(self, device = None, pointType = None, pointAddress=None, pointName = None, description = None, presentValue = None, units_state = None):
        Point.__init__(self, device = device, pointType = pointType, pointAddress=pointAddress, pointName = pointName, description = description, presentValue = presentValue, units_state = units_state)
    
    @property         
    def units(self):
        return self._units_state
        
    def __repr__(self):
        return '%s : %s %s' % (self.name, self.value, self._units_state)

class BooleanPoint(Point):
    """
    Representation of a Boolean Information
    """
    def __init__(self, device = None, pointType = None, pointAddress=None, pointName = None, description = None, presentValue = None, units_state = None):
        Point.__init__(self, device = device, pointType = pointType, pointAddress=pointAddress, pointName = pointName, description = description, presentValue = presentValue, units_state = units_state)

    @property     
    def value(self):
        res = self.device.read(self.name)
        self._historyIndex.append(datetime.now())
        self._history.append(res)
        if res == 'inactive':
            self._key = 0
            self._boolKey = False
        else:
            self._key = 1
            self._boolKey = True        
        return res

    @property
    def boolValue(self):
        if self.value == 'active':
            self._key = 1
            self._boolKey = True
        else:
            self._key = 0
            self._boolKey = False
        return self._boolKey
                    
    
    @property     
    def units(self):
        return None
        
    def __repr__(self):
        #return '%s : %s' % (self.name, self._units_state[self._key])
        return '%s : %s' % (self.name, self.boolValue)
        
class EnumPoint(Point):
    """
    Representation of an Enumerated Information (multiState)
    """
    def __init__(self, device = None, pointType = None, pointAddress=None, pointName = None, description = None, presentValue = None, units_state = None):
        Point.__init__(self, device = device, pointType = pointType, pointAddress=pointAddress, pointName = pointName, description = description, presentValue = presentValue, units_state = units_state)
    
    @property
    def enumValue(self):
        return self._units_state[int(self.value)-1]

    @property     
    def units(self):
        return None
        
    def __repr__(self):
        #return '%s : %s' % (self.name, )
        return '%s : %s' % (self.name, self.enumValue)