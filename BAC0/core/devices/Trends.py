#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#

# --- standard Python modules ---
# --- 3rd party modules ---

from collections import namedtuple
from typing import Any, Dict, List, Optional, Tuple, Union

from bacpypes3.primitivedata import Date, Time

# --- this application's modules ---
from ..utils.notes import note_and_log
from ..utils.lookfordependency import pandas_if_available

_PANDAS, pd, _, _ = pandas_if_available()


# ------------------------------------------------------------------------------

HistoryComponent = namedtuple("HistoryComponent", "index logdatum status choice")


class TrendLogProperties(object):
    """
    A container for trend properties
    """

    def __init__(self):
        self.device: Optional[Any] = None
        self.oid: Optional[Any] = None
        self.object_name: Optional[str] = None
        self.description: str = ""
        self.log_device_object_property: Optional[Any] = None
        self.buffer_size: int = 0
        self.record_count: int = 0
        self.total_record_count: int = 0
        self.log_interval: int = 0
        self.statusFlags: Optional[Any] = None
        self.status_flags: Dict[str, bool] = {
            "in_alarm": False,
            "fault": False,
            "overridden": False,
            "out_of_service": False,
        }
        self._history_components: List[HistoryComponent] = []
        self._df: Optional[pd.DataFrame] = None
        self.type: str = "TrendLog"
        self.units_state: str = "None"

    def __repr__(self):
        return "{} | Descr : {} | Record count : {}".format(
            self.object_name, self.description, self.record_count
        )

    @property
    def name(self) -> Optional[str]:
        return self.object_name


def TrendLog(*args: Tuple, **kwargs: Dict) -> "_TrendLog":
    trend = _TrendLog(*args, **kwargs)
    # update_properties_task = Task(trend.update_properties())
    # update_properties_task.start()
    # while not update_properties_task.done:
    #    pass
    # if "read_log_on_creation" in args:
    #    trend.read_log_buffer_task = Task(trend.read_log_buffer())

    return trend


@note_and_log
class _TrendLog(TrendLogProperties):
    """
    BAC0 simplification of TrendLog Object
    """

    def __init__(
        self,
        OID: Any,
        device: Optional[Any] = None,
        read_log_on_creation: bool = True,
        multiple_request: Optional[Any] = None,
    ):
        self.properties: TrendLogProperties = TrendLogProperties()
        self.properties.device = device
        self.properties.oid = OID
        self.update_properties_task: Optional[Any] = None
        self._last_index: int = 0
        if read_log_on_creation:
            self.read_log_buffer_task: Optional[Any] = None

    @staticmethod
    def read_logDatum(logDatum: Any) -> Tuple[str, Any]:
        for k, v in logDatum.__dict__.items():
            if v is None:
                continue
            else:
                return (k, v)

    async def update_properties(self) -> None:
        try:
            (
                self.properties.object_name,
                self.properties.description,
                self.properties.record_count,
                self.properties.buffer_size,
                self.properties.total_record_count,
                self.properties.statusFlags,
                self.properties.log_interval,
            ) = await self.properties.device.properties.network.readMultiple(
                "{addr} trendLog {oid} objectName description recordCount bufferSize totalRecordCount statusFlags logInterval".format(
                    addr=self.properties.device.properties.address,
                    oid=str(self.properties.oid),
                )
            )
            self.properties.description = str(self.properties.description)
        except Exception as error:
            raise Exception(f"Problem reading trendLog informations: {error}")

    async def _total_record_count(self) -> int:
        self.properties.total_record_count = (
            await self.properties.device.properties.network.read(
                "{addr} trendLog {oid} totalRecordCount".format(
                    addr=self.properties.device.properties.address,
                    oid=str(self.properties.oid),
                )
            )
        )
        return self.properties.total_record_count

    async def read_log_buffer(self) -> None:
        RECORDS = 10
        log_buffer = set()
        _actual_index = await self._total_record_count()
        start = max(_actual_index - self.properties.record_count + 1, self._last_index)
        _count = max(_actual_index - start, 0)
        steps = int(_count / RECORDS) + int(1 if (_count % RECORDS) > 0 else 0)

        self.log(f"Reading log : {start} {_count} {steps}", level="debug")

        _from = start
        for each in range(steps):
            range_params = ("s", _from, Date("1979-01-01"), Time("00:00"), RECORDS)
            _chunk = await self.properties.device.properties.network.readRange(
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

    def create_dataframe(self, log_buffer: set) -> None:
        for each in log_buffer:
            year, month, day, dow = each.timestamp.date
            year = year + 1900
            hours, minutes, seconds, ms = each.timestamp.time
            seconds = 0 if seconds == 255 else seconds
            ms = 0 if ms == 255 else ms
            _index = pd.to_datetime(
                f"{year}-{month}-{day} {hours}:{minutes}:{seconds}.{ms}",
                format="%Y-%m-%d %H:%M:%S.%f",
            )
            _choice, _logDatum = self.read_logDatum(each.logDatum)
            _status = each.statusFlags
            self._log.debug(f"{_index}, {_logDatum}, {_status}, {_choice}")
            his_component = HistoryComponent(_index, _logDatum, _status, _choice)
            if his_component not in self.properties._history_components:
                self.properties._history_components.append(his_component)

        if _PANDAS:
            df = pd.DataFrame(
                {
                    "index": [
                        each.index for each in self.properties._history_components
                    ],
                    self.properties.object_name: [
                        each.logdatum for each in self.properties._history_components
                    ],
                    "status": [
                        each.status for each in self.properties._history_components
                    ],
                    "choice": [
                        each.choice for each in self.properties._history_components
                    ],
                }
            )
            df = df.set_index("index")
            # df["choice"] = _choice
            # df[self.properties.object_name] = df['logDatum']

            self.properties._df = df
        else:
            # self.properties._history_components = (self.index, self.logdatum, self.status)
            self._log.warning(
                "Pandas not installed. Treating histories as simple list."
            )

    @property
    async def history(self) -> Union[Dict, Any]:
        await self.read_log_buffer()

        if not _PANDAS or self.properties._df is None:
            return dict(
                zip(
                    [each.index for each in self.properties._history_components],
                    [each.logDatum for each in self.properties._history_components],
                )
            )

        try:
            if not self.properties.log_device_object_property:
                self.properties.log_device_object_property = (
                    await self.properties.device.properties.network.read(
                        "{addr} trendLog {oid} logDeviceObjectProperty".format(
                            addr=self.properties.device.properties.address,
                            oid=str(self.properties.oid),
                        )
                    )
                )
            (
                objectType,
                objectAddress,
            ) = self.properties.log_device_object_property.objectIdentifier
            logged_point = self.properties.device.find_point(objectType, objectAddress)
        except (Exception, ValueError):
            logged_point = None

        serie = self.properties._df[self.properties.object_name].copy()
        serie.units = logged_point.properties.units_state if logged_point else "n/a"
        serie.name = ("{}/{}").format(
            self.properties.device.properties.name, self.properties.object_name
        )
        if not logged_point:
            serie.states = "unknown"
            serie.datatype = None
        else:
            if logged_point.properties.name in self.properties.device.binary_states:
                serie.states = "binary"
            elif logged_point.properties.name in self.properties.device.multi_states:
                serie.states = "multistates"
            else:
                serie.states = "analog"
            serie.datatype = objectType
        serie.description = self.properties.description

        return serie.sort_index()

    def chart(self, remove: bool = False) -> None:
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
