#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Points.py - Definition of points so operations on Read results are more convenient.
"""

# --- standard Python modules ---
from datetime import datetime
from collections import namedtuple
import time

# --- 3rd party modules ---
try:
    import pandas as pd
    from pandas.io import sql

    try:
        from pandas import Timestamp
    except ImportError:
        from pandas.lib import Timestamp
    _PANDAS = True
except ImportError:
    _PANDAS = False

from bacpypes.object import TrendLogObject

# --- this application's modules ---
from ...tasks.Poll import SimplePoll as Poll
from ...tasks.Match import Match, Match_Value
from ..io.IOExceptions import NoResponseFromController, UnknownPropertyError
from ..utils.notes import note_and_log


# ------------------------------------------------------------------------------



class VirtualDeviceProperties(object):
    """
    This serves as a container for device properties
    """

    def __init__(self):
        self.name = "Virtual Device"
        self.address = "local"
        self.device_id = None
        self.network = None
        self.pollDelay = None
        self.objects_list = None
        self.pss = None
        self.multistates = None
        self.db_name = None
        self.segmentation_supported = True
        self.history_size = None
        self.bacnet_properties = None

    def __repr__(self):
        return "{}".format(self.asdict)

    @property
    def asdict(self):
        return self.__dict__

class VirtualDevice(object):
    def __init__(self):
        self.properties = VirtualDeviceProperties()

class VirtualPointProperties(object):
    """
    A container for VirtualPoint properties
    """

    def __init__(self):
        self.name = None
        self.device = VirtualDevice()
        self.description = ""
        self.units_state = ""
        self.type = "virtual"
        self._df = None

    def __repr__(self):
        return "{} | Descr : {}".format(self.name, self.description)


@note_and_log
class VirtualPoint(VirtualPointProperties):
    """
    Virtual points could be used to show calculation result on Bokeh
    A function is passed at creation time and this function must return a pandas Serie
    """

    def __init__(self, name, fn, description=None, units="No Units"):
        if description is None:
            raise ValueError("Please provide description")
        if not _PANDAS:
            raise ImportError("Pandas required to use VirtualPoints")
        self.name = name
        self.properties = VirtualPointProperties()
        self.properties.name = name
        self.properties.description = description
        self.properties.units_state = units
        self._history = fn

    @property
    def history(self):
        _result = self._history()
        if not isinstance(_result, pd.Series):
            raise ValueError("Function of virtual point must return a Series")
        else:
            return _result

    def chart(self, remove=False):
        """
        Add point to the bacnet trending list
        """
        self._log.warning('Use bacnet.add_trend() instead')

    def __repr__(self):
        return self.properties.__repr__()
