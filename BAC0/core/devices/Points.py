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
    def historyTable(self):
        """
        returns : (pd.Series) containing timestamp and value of all readings
        """
        his_table = pd.Series(self._history.value,
                              index=self._history.timestamp)
        return his_table

    def chart(self):
        """
        Simple shortcut to plot function
        """
        return self.historyTable.plot()


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

    def __repr__(self):
        return '%s : %s %s' % (self.properties.name, self.value, self.properties.units_state)


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

    def __repr__(self):
        # return '%s : %s' % (self.name, )
        return '%s : %s' % (self.properties.name, self.enumValue)
