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
from collections import namedtuple


class Point():
    """
    This represents a point inside a device. This base class will be
    used to build NumericPoint, BooleanPoint and EnumPoints

    Each point implement a history feature. Each time the point is read,
    the value with timstampe is added to a
    history table. It's then possible to look what happened since the
    creation of the point.

    """

    def __init__(self, device=None,
                 pointType=None,
                 pointAddress=None,
                 pointName=None,
                 description=None,
                 presentValue=None,
                 units_state=None):
        self._history = namedtuple('_history',
                                   ['timestamp', 'value'])
        self.properties = namedtuple('properties',
                                     ['device', 'name', 'type',
                                      'address', 'description', 'units',
                                      'simulated', 'overridden'])

        self._history.timestamp = []
        self._history.value = []
        self._history.value.append(presentValue)
        self._history.timestamp.append(datetime.now())

        self.properties.device = device
        self.properties.name = pointName
        self.properties.type = pointType
        self.properties.address = pointAddress
        self.properties.description = description
        self.properties.units_state = units_state
        self.properties.simulated = False
        self.properties.overridden = False

    @property
    def value(self):
        """
        Retrieve value of the point
        """
        res = self.properties.device.read(self.properties.name)
        self._history.timestamp.append(datetime.now())
        self._history.value.append(res)
        return res

    @property
    def units(self):
        """
        Should return units
        """
        raise Exception('Must be overridden')

    @property
    def lastValue(self):
        """
        returns: last value read
        """
        return self._history.value[-1]

    @property
    def history(self):
        """
        returns : (pd.Series) containing timestamp and value of all readings
        """
        his_table = pd.Series(self._history.value,
                              index=self._history.timestamp)
        return his_table

    def chart(self, *args):
        """
        Simple shortcut to plot function
        """
        return self.history.plot(*args)

    def __getitem__(self, key):
        """
        Way to get points... presentValue, status, flags, etc...

        :param key: state
        :returns: list of enum states
        """
        if str(key).lower() in ['unit', 'units', 'state', 'states']:
            key = 'units_state'
        try:
            return getattr(self.properties,key)
        except AttributeError:
            raise ValueError('Wrong property')

    def write(self, value, *, prop='presentValue', priority=''):
        """
        Write to present value of a point

        :param value: (float) numeric value
        :param prop: (str) property to write. Default = presentValue
        :param priority: (int) priority to which write.

        """
        if priority != '':
            if isinstance(float(priority), float) \
                    and float(priority) >= 1 \
                    and float(priority) <= 16:
                priority = '- %s' % priority
            else:
                raise ValueError('Priority must be a number between 1 and 16')

        self.properties.device.network.write(
            '%s %s %s %s %s %s' %
            (self.properties.device.addr, self.properties.type, str(
                self.properties.address), prop, str(value), str(priority)))
        # Read after the write so history gets updated.
        self.value

    def default(self, value):
        self.write(value, prop='relinquishDefault')

    def sim(self, value):
        """
        Simulate a value
        Will write to out_of_service property (true)
        Will then write the presentValue so the controller will use that value
        The point name will be added to the list of simulated points
        (self.simPoints)

        :param value: (float) value to simulate

        """
        self.properties.device.network.sim(
            '%s %s %s presentValue %s' %
            (self.properties.device.addr, self.properties.type, str(
                self.properties.address), str(value)))
        self.properties.simulated = True

    def release(self):
        """
        Release points
        Will write to out_of_service property (false)
        The controller will take control back of the presentValue
        """
        self.properties.device.network.release(
            '%s %s %s' %
            (self.properties.device.addr, self.properties.type, str(
                self.properties.address)))
        self.properties.simulated = False

    def ovr(self, value):
        self.write(value, priority=8)
        self.properties.overridden = True

    def auto(self):
        self.write('null', priority=8)
        self.properties.overridden = False

    def _setitem(self, value):
        """
        Called by _set, will trigger right function depending on 
        point type to write to the value and make tests.
        This is default behaviour of the point  :
        AnalogValue are written to
        AnalogOutput are overridden
        """
        if 'Value' in self.properties.type:
            if str(value).lower() == 'auto':
                raise ValueError('Value was not simulated or overridden, cannot release to auto')
            # analog value must be written to
            self.write(value)
        elif 'Output' in self.properties.type:
            # analog output must be overridden
            if str(value).lower() == 'auto':
                self.auto()
            else:
                self.ovr(value)
        else:
            # input are left... must be simulated
            if str(value).lower() == 'auto':
                self.release()
            else:
                self.sim(value)

    def _set(self, value):
        """
        This function will check for datatype to write
        and call _setitem()
        Those functions allow __setitem__ to work from device
        device['point'] = value
        """
        raise Exception('Must be overridden')

class NumericPoint(Point):
    """
    Representation of a Numeric information
    """

    def __init__(self, device=None,
                 pointType=None,
                 pointAddress=None,
                 pointName=None,
                 description=None,
                 presentValue=None,
                 units_state=None):
        Point.__init__(self, device=device,
                       pointType=pointType,
                       pointAddress=pointAddress,
                       pointName=pointName,
                       description=description,
                       presentValue=presentValue,
                       units_state=units_state)

    @property
    def units(self):
        return self.properties.units_state

    def _set(self, value):
        try:    
            val = float(value)
            if isinstance(val, float):
                self._setitem(value)
        except:
            val = str(value)
            if (val.lower() == 'auto'):
                self._setitem(value)
            else:
                raise ValueError('Value must be numeric')

    def __repr__(self):
        return '%s : %.2f %s' % (self.properties.name, self.value, self.properties.units_state)


class BooleanPoint(Point):
    """
    Representation of a Boolean Information
    """

    def __init__(self, device=None,
                 pointType=None,
                 pointAddress=None,
                 pointName=None,
                 description=None,
                 presentValue=None,
                 units_state=None):
        Point.__init__(self, device=device,
                       pointType=pointType,
                       pointAddress=pointAddress,
                       pointName=pointName,
                       description=description,
                       presentValue=presentValue,
                       units_state=units_state)

    @property
    def value(self):
        res = self.properties.device.read(self.properties.name)
        self._history.timestamp.append(datetime.now())
        self._history.value.append(res)
        if res == 'inactive':
            self._key = 0
            self._boolKey = False
        else:
            self._key = 1
            self._boolKey = True
        return res

    @property
    def boolValue(self):
        """
        returns : (boolean) Value
        """
        if self.value == 'active':
            self._key = 1
            self._boolKey = True
        else:
            self._key = 0
            self._boolKey = False
        return self._boolKey

    @property
    def units(self):
        """
        """
        return None

    def _set(self, value):
        if value == True:
            self._setitem('active')
        elif value == False:
            self._setitem('inactive')
        elif str(value) in ['inactive','active'] or str(value).lower() == 'auto':
            self._setitem(value) 
        else:
            raise ValueError('Value must be boolean True, False or "active"/"inactive"')

    def __repr__(self):
        # return '%s : %s' % (self.name, self._units_state[self._key])
        return '%s : %s' % (self.properties.name, self.boolValue)


class EnumPoint(Point):
    """
    Representation of an Enumerated Information (multiState)
    """

    def __init__(self, device=None,
                 pointType=None,
                 pointAddress=None,
                 pointName=None,
                 description=None,
                 presentValue=None,
                 units_state=None):
        Point.__init__(self, device=device,
                       pointType=pointType,
                       pointAddress=pointAddress,
                       pointName=pointName,
                       description=description,
                       presentValue=presentValue,
                       units_state=units_state)

    @property
    def enumValue(self):
        """
        returns: (str) Enum state value
        """
        return self.properties.units_state[int(self.value) - 1]

    @property
    def units(self):
        return None
        
    def _set(self,value):
        if isinstance(value,int):
            self._setitem(value)
        elif str(value) in self.properties.units_state:
            self._setitem(self.properties.units_state.index(value)+1)
        elif str(value).lower() == 'auto':
            self._setitem('auto')            
        else:
            raise ValueError('Value must be integer or correct enum state : %s' % self.properties.units_state)

    def __repr__(self):
        # return '%s : %s' % (self.name, )
        return '%s : %s' % (self.properties.name, self.enumValue)
