#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Definition of points so operations will be easier on read result
"""
class Point():
    """
    Basic point
    """
    def __init__(self, val, units_state):
        self.value = val
        self.status = ''
        self.units_state = units_state
    def value(self):
        return self.value
        
class NumericPoint(Point):
    def __init__(self,val, units_state):
        Point.__init__(self,val, units_state)
        
    def value(self):
        return self.value
        
    def units(self):
        return self.units_state
        
    def __repr__(self):
        return '%s %s' % (self.value, self.units_state)

class BooleanPoint(Point):
    def __init__(self,val, units_state):
        Point.__init__(self,val, units_state)
        if val == 'inactive':
            self._key = 0
            self._boolKey = False
        else:
            self._key = 1
            self._boolKey = True
        
    def value(self):
        return self._boolKey
        
    def units(self):
        return None
        
    def __repr__(self):
        return '%s %s' % (self.value, self.units_state[self._key])
        
class EnumPoint(Point):
    def __init__(self,val, units_state):
        Point.__init__(self,val, units_state)
        
    def value(self):
        return self.value
        
    def units(self):
        return None
        
    def __repr__(self):
        return '%s' % (self.units_state[self.value-1])