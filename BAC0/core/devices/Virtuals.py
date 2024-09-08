#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Points.py - Definition of points so operations on Read results are more convenient.
"""

import asyncio
import hashlib
from collections import namedtuple


# --- standard Python modules ---
from datetime import datetime

from bacpypes3.basetypes import EngineeringUnits

from ...tasks.Match import Match_Value

# --- this application's modules ---
from ..utils.notes import note_and_log
from ..utils.lookfordependency import pandas_if_available

_PANDAS, pd, _, _ = pandas_if_available()
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
        return f"{self.asdict}"

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
        self.device = None
        self.name = None
        self.type = "analog-virtual"
        self.address = None
        self.description = ""
        self.units_state = ""
        self.simulated = False
        self.overridden = False
        self.priority_array = None
        self.history_size = None
        self.bacnet_properties = {}
        self.status_flags = None
        self._df = None

    def __repr__(self):
        return f"{self.asdict}"

    @property
    def asdict(self):
        return self.__dict__


@note_and_log
class VirtualPoint:
    """
    Virtual points could be used to show calculation result on Bokeh
    A function is passed at creation time and this function must return a pandas Serie

    I chose to create those points without using BACnet classes because Virtual
    points are meant to be used on BAC0.device and creating fake BACnet objects
    could lead to potential confusion.
    """

    def __init__(
        self,
        name,
        device=None,
        object_type="analogVirtual",
        initial_value=None,
        history_fn=None,
        description=None,
        units="No Units",
        tags=[],
    ):
        self.properties = VirtualPointProperties()
        self.properties.type = object_type
        self.properties.device = VirtualDevice() if device is None else device
        if description is None:
            raise ValueError("Please provide description")
        if not _PANDAS:
            raise ImportError("Pandas required to use VirtualPoints")
        self.name = name
        self.properties.name = name
        self.properties.address = int(hashlib.sha256(name.encode()).hexdigest(), 16) % (
            10**8
        )
        # 8 digits address based on the name. this way I don't have to keep track of numbers and if the same name is used, we should get something similar and the InfluxDB trend will mark the point as the same.
        self.properties.description = description
        self.properties.units_state = (
            EngineeringUnits(units) if object_type == "analogVirtual" else units
        )
        self.tags = tags
        self._history_fn = history_fn

        self._history = namedtuple("_history", ["timestamp", "value"])
        self._history.timestamp = []
        self._history.value = []

        self._match_task = namedtuple("_match_task", ["task", "running"])
        self._match_task.task = None
        self._match_task.running = False

        self.fake_pv = None
        if initial_value:
            self.fake_pv = float(initial_value)
            self._trend(float(initial_value))

    def chart(self, remove=False):
        """
        Add point to the bacnet trending list
        """
        self.log("Use bacnet.add_trend(point) instead", level="warning")

    async def _set(self, value):
        if value == "auto":
            pass
        elif self._history_fn is None:
            self.fake_pv = float(value)
            self._trend(float(value))
        else:
            self._log.warning(
                "Point is configured as a function of other points. You can't set a new value"
            )

    def _trend(self, res):
        self._history.timestamp.append(datetime.now().astimezone())
        self._history.value.append(res)
        if self.properties.device.properties.network.database:
            self.properties.device.properties.network.database.prepare_point([self])

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
                except Exception:
                    self._log.exception("Can't append to history")

    @property
    def lastTimestamp(self):
        """
        returns: last timestamp read
        """
        if _PANDAS:
            last_val = self.history.dropna()
            last_val_clean = None if len(last_val) == 0 else last_val.index[-1]
            return last_val_clean
        else:
            return self._history.timestamp[-1]

    @property
    async def value(self):
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

    def match_value(self, value, *, delay=5, use_last_value=False):
        asyncio.create_task(
            self._match_value(value=value, delay=delay, use_last_value=use_last_value)
        )

    async def _match_value(self, value, *, delay=5, use_last_value=False):
        """
        This allow functions like :
            device['point'].match('value')

        A sensor will follow a calculation...
        """
        if self._match_task.task is None or not self._match_task.running:
            self._match_task.task = Match_Value(
                value=value, point=self, delay=delay, use_last_value=use_last_value
            )
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay > 0:
            await self._match_task.task.stop()
            self._match_task.running = False
            await asyncio.sleep(1)

            self._match_task.task = Match_Value(
                value=value, point=self, delay=delay, use_last_value=use_last_value
            )
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay == 0:
            await self._match_task.task.stop()
            self._match_task.running = False

        else:
            raise RuntimeError("Stop task before redefining it")

    def tag(self, tag_id, tag_value, lst=None):
        """
        Add tag to point. Those tags can be used to make queries,
        add information, etc.
        They will be included if InfluxDB is used.
        """
        if lst is None:
            self.tag.append((tag_id, tag_value))
        else:
            for each in lst:
                tag_id, tag_value = each
                self.tag.append((tag_id, tag_value))

    def __repr__(self):
        return "{}/{} : {:.2f} {}".format(
            self.properties.device.properties.name,
            self.properties.name,
            float(self.lastValue),
            self.properties.units_state,
        )

    @property
    def asdict(self):
        return self.__dict__

    def __add__(self, other):
        return self.lastValue + other

    __radd__ = __add__

    def __sub__(self, other):
        return self.lastValue - other

    def __rsub__(self, other):
        return other - self.lastValue

    def __mul__(self, other):
        return self.lastValue * other

    __rmul__ = __mul__

    def __truediv__(self, other):
        return self.lastValue / other

    def __rtruediv__(self, other):
        return other / self.lastValue

    def __lt__(self, other):
        return self.lastValue < other

    def __le__(self, other):
        return self.lastValue <= other

    def __eq__(self, other):
        return self.lastValue == other

    def __gt__(self, other):
        return self.lastValue > other

    def __ge__(self, other):
        return self.lastValue >= other
