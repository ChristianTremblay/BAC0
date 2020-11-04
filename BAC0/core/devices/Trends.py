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
from itertools import islice


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
from bacpypes.primitivedata import Date, Time

# --- this application's modules ---
from ...tasks.Poll import SimplePoll as Poll
from ...tasks.Match import Match, Match_Value
from ..io.IOExceptions import NoResponseFromController, UnknownPropertyError
from ..utils.notes import note_and_log


# ------------------------------------------------------------------------------


class TrendLogProperties(object):
    """
    A container for trend properties
    """

    def __init__(self):
        self.device = None
        self.oid = None
        self.object_name = None
        self.description = ""
        self.log_device_object_property = None
        self.buffer_size = 0
        self.record_count = 0
        self.total_record_count = 0
        self.log_interval = 0
        self.description = None
        self.statusFlags = None
        self.status_flags = {
            "in_alarm": False,
            "fault": False,
            "overridden": False,
            "out_of_service": False,
        }
        self._history_components = {"index": [], "logdatum": [], "status": []}
        self._df = None
        self.type = "TrendLog"
        self.units_state = "None"

    def __repr__(self):
        return "{} | Descr : {} | Record count : {}".format(
            self.object_name, self.description, self.record_count
        )

    @property
    def name(self):
        return self.object_name


@note_and_log
class TrendLog(TrendLogProperties):
    """
    BAC0 simplification of TrendLog Object
    """

    def __init__(
        self, OID, device=None, read_log_on_creation=True, multiple_request=None
    ):
        self.properties = TrendLogProperties()
        self.properties.device = device
        self.properties.oid = OID
        self.update_properties()

        if read_log_on_creation:
            self.read_log_buffer()
        self._last_index = 0

    def update_properties(self):
        try:
            self.properties.object_name, self.properties.description, self.properties.record_count, self.properties.buffer_size, self.properties.total_record_count, self.properties.log_device_object_property, self.properties.statusFlags, self.properties.log_interval = self.properties.device.properties.network.readMultiple(
                "{addr} trendLog {oid} objectName description recordCount bufferSize totalRecordCount logDeviceObjectProperty statusFlags logInterval".format(
                    addr=self.properties.device.properties.address,
                    oid=str(self.properties.oid),
                )
            )
        except Exception as error:
            raise Exception("Problem reading trendLog informations: {}".format(error))

    def _total_record_count(self):
        self.properties.total_record_count = self.properties.device.properties.network.read(
            "{addr} trendLog {oid} totalRecordCount".format(
                addr=self.properties.device.properties.address,
                oid=str(self.properties.oid),
            )
        )
        return self.properties.total_record_count

    def read_log_buffer(self):
        RECORDS = 10
        log_buffer = set()
        _actual_index = self._total_record_count()
        start = max(_actual_index - self.properties.record_count, self._last_index) + 1
        _count = _actual_index - start
        steps = int(_count / 10) + int(_count % 10)

        self._log.debug("Reading log : {} {} {}".format(start, _count, steps))

        _from = start
        for each in range(steps):
            range_params = ("s", _from, Date("1979-01-01"), Time("00:00"), RECORDS)
            _chunk = self.properties.device.properties.network.readRange(
                "{} trendLog {} logBuffer".format(
                    self.properties.device.properties.address, str(self.properties.oid)
                ),
                range_params=range_params,
            )
            _from += len(_chunk)
            for chunk in _chunk:
                log_buffer.add(chunk)

        self._last_index = _from
        self.create_dataframe(log_buffer)

    def create_dataframe(self, log_buffer):
        for each in log_buffer:
            year, month, day, dow = each.timestamp.date
            year = year + 1900
            hours, minutes, seconds, ms = each.timestamp.time
            self.properties._history_components["index"].append(
                pd.to_datetime(
                    "{}-{}-{} {}:{}:{}.{}".format(
                        year, month, day, hours, minutes, seconds, ms
                    ),
                    format="%Y-%m-%d %H:%M:%S.%f",
                )
            )
            self.properties._history_components["logdatum"].append(
                each.logDatum.dict_contents()
            )
            self.properties._history_components["status"].append(each.statusFlags)

        if _PANDAS:
            df = pd.DataFrame(
                {
                    "index": self.properties._history_components["index"],
                    "logdatum": self.properties._history_components["logdatum"],
                    "status": self.properties._history_components["status"],
                }
            )
            df = df.set_index("index")
            df["choice"] = df["logdatum"].apply(lambda x: list(x.keys())[0])
            df[self.properties.object_name] = df["logdatum"].apply(
                lambda x: list(x.values())[0]
            )

            self.properties._df = df
        else:
            # self.properties._history_components = (self.index, self.logdatum, self.status)
            self._log.warning(
                "Pandas not installed. Treating histories as simple list."
            )

    @property
    def history(self):
        self.read_log_buffer()
        if not _PANDAS:
            return dict(
                zip(
                    self.properties._history_components["index"],
                    self.properties._history_components["logdatum"],
                )
            )
        objectType, objectAddress = (
            self.properties.log_device_object_property.objectIdentifier
        )
        try:
            logged_point = self.properties.device.find_point(objectType, objectAddress)
        except ValueError:
            logged_point = None
        serie = self.properties._df[self.properties.object_name].copy()
        serie.units = logged_point.properties.units_state if logged_point else "n/a"
        serie.name = ("{}/{}").format(
            self.properties.device.properties.name, self.properties.object_name
        )
        if not logged_point:
            serie.states = "unknown"
        else:
            if logged_point.properties.name in self.properties.device.binary_states:
                serie.states = "binary"
            elif logged_point.properties.name in self.properties.device.multi_states:
                serie.states = "multistates"
            else:
                serie.states = "analog"
        serie.description = self.properties.description
        serie.datatype = objectType
        return serie.sort_index()

    def chart(self, remove=False):
        """
        Add point to the bacnet trending list
        """
        if not _PANDAS:
            self._log.error(
                "Pandas must be installed to use live chart feature. See documentation how how to run BAC0 in complete mode"
            )
        else:
            if remove:
                self.properties.device.properties.network.remove_trend(self)
            else:
                self.properties.device.properties.network.add_trend(self)

    def __repr__(self):
        return self.properties.__repr__()
