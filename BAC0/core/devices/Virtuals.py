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
        self.history_size = None
        self._df = None

    def __repr__(self):
        return "VIRTUAL POINT-- {} | Descr : {}".format(self.name, self.description)


@note_and_log
class VirtualPoint(VirtualPointProperties):
    """
    Virtual points could be used to show calculation result on Bokeh
    A function is passed at creation time and this function must return a pandas Serie
    """

    def __init__(
        self,
        name,
        initial_value=None,
        history_fn=None,
        description=None,
        units="No Units",
    ):
        if description is None:
            raise ValueError("Please provide description")
        if not _PANDAS:
            raise ImportError("Pandas required to use VirtualPoints")
        self.name = name
        self.properties = VirtualPointProperties()
        self.properties.name = name
        self.properties.description = description
        self.properties.units_state = units
        self._history_fn = history_fn

        self._history = namedtuple("_history", ["timestamp", "value"])
        self._history.timestamp = []
        self._history.value = []

        self._match_task = namedtuple("_match_task", ["task", "running"])
        self._match_task.task = None
        self._match_task.running = False

        self.fake_pv = None
        if initial_value:
            self._set(initial_value)

    def chart(self, remove=False):
        """
        Add point to the bacnet trending list
        """
        self._log.warning("Use bacnet.add_trend(point) instead")

    def _set(self, value):
        if self._history_fn is None:
            self.fake_pv = value
            self._trend(value)
        else:
            self._log.warning(
                "Point is configured as a function of other points. You can't set a new value"
            )

    def _trend(self, res):
        self._history.timestamp.append(datetime.now())
        self._history.value.append(res)
        if self.properties.history_size is None:
            return
        else:
            if self.properties.history_size < 1:
                self.properties.history_size = 1
            if len(self._history.timestamp) >= self.properties.history_size:
                try:
                    self._history.timestamp = self._history.timestamp[
                        -self.properties.history_size :
                    ]
                    self._history.value = self._history.value[
                        -self.properties.history_size :
                    ]
                    assert len(self._history.timestamp) == len(self._history.value)
                except Exception as e:
                    self._log.exception("Can't append to history")

    @property
    def value(self):
        """
        Retrieve value of the point
        """
        return self.lastValue

    @property
    def lastValue(self):
        """
        returns: last value read
        """
        if _PANDAS:
            return self.history.dropna().iloc[-1]
        else:
            return self._history.value[-1]

    @property
    def history(self):
        """
        returns : (pd.Series) containing timestamp and value of all readings
        """
        if self._history_fn is not None:
            return self._history_fn()
        else:
            if not _PANDAS:
                return dict(zip(self._history.timestamp, self._history.value))
            idx = self._history.timestamp.copy()
            his_table = pd.Series(index=idx, data=self._history.value[: len(idx)])
            del idx
            his_table.name = ("{}/{}").format(
                self.properties.device.properties.name, self.properties.name
            )
            his_table.units = self.properties.units_state
            his_table.states = "virtual"

            his_table.description = self.properties.description

            his_table.datatype = self.properties.type
            return his_table

    def match_value(self, value, *, delay=5):
        """
        This allow functions like :
            device['point'].match('value')

        A sensor will follow a calculation...
        """
        if self._match_task.task is None:
            self._match_task.task = Match_Value(value=value, point=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay > 0:
            self._match_task.task.stop()
            self._match_task.running = False
            time.sleep(1)

            self._match_task.task = Match_Value(value=value, point=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay == 0:
            self._match_task.task.stop()
            self._match_task.running = False

        else:
            raise RuntimeError("Stop task before redefining it")

    def __repr__(self):
        return "{}/{} : {:.2f} {}".format(
            self.properties.device.properties.name,
            self.properties.name,
            self.value,
            self.properties.units_state,
        )

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __lt__(self, other):
        return self.value < other

    def __le__(self, other):
        return self.value <= other

    def __eq__(self, other):
        return self.value == other

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other
