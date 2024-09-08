from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from bacpypes3.basetypes import (
    Date,
    DateTime,
    EventState,
    LoggingType,
    LogRecord,
    LogRecordLogDatum,
    Reliability,
    StatusFlags,
    Time,
)
from bacpypes3.constructeddata import ListOf
from bacpypes3.primitivedata import Unsigned
from ...utils.lookfordependency import pandas_if_available

PANDAS, _, _, _ = pandas_if_available()


Record = namedtuple(
    "Record", "timestamp value statusFlags sequencenumber interval trendFlag logEvent"
)


class LocalTrendLog(object):
    """
    Local trendLogs require a databse between values read on the field
    and values used to create thje local trendLogs object.

    I will use the existing SQL code I have to store the local values

    """

    def __init__(self, obj: Any, datatype: str):
        self.obj = obj
        self.data: List[Record] = []
        self.bufferSize: int = 250
        self.statusFlags = StatusFlags([0, 0, 0, 0])
        self.datatype = datatype

    @staticmethod
    def to_float(val: Union[int, float, str]) -> Optional[float]:
        try:
            return float(val)
        except ValueError:
            return None

    @staticmethod
    def decompose_datetime(dt: datetime) -> Tuple[int, int, int, int, int]:
        y = dt.year
        M = dt.month
        d = dt.day
        h = dt.hour
        m = dt.minute
        s = dt.second
        ms = dt.microsecond
        wk = dt.weekday()
        return (y, M, d, wk, h, m, s, ms)

    def to_bacpypes_datetime(self, dt: datetime) -> DateTime:
        _y, _M, _d, wk, _h, _m, _s, _ms = self.decompose_datetime(dt)
        try:
            result = DateTime(date=Date((_y, _M, _d, wk)), time=Time((_h, _m, _s, _ms)))
        except TypeError:
            raise TypeError(f"Error with {dt} {_y=}, {_M=}, {_d=}, {_h=}, {_m=}")
        return result

    def to_logDatum(self, value: Union[int, float, str]) -> Dict[str, Any]:
        _klass = getattr(LogRecordLogDatum, self.datatype)
        return {self.datatype: _klass(value)}

    def to_bacpypes_logrecord(self, record: Record) -> LogRecord:
        """
        For now, only support real... make it work first
        """
        _timestamp = record.timestamp.astimezone()
        _dt = self.to_bacpypes_datetime(_timestamp)
        record_value = self.to_logDatum(record.value)

        return LogRecord(
            timestamp=_dt,
            logDatum=LogRecordLogDatum(**record_value),
            statusFlags=record.statusFlags,
        )

    def add_data(
        self,
        timestamp: datetime,
        value: Union[int, float, str],
        flags: StatusFlags = StatusFlags([0, 0, 0, 0]),
        interval: Optional[int] = None,
        update_after: bool = True,
    ) -> None:
        """
        each object will contain a dict of values that will be
        turned into log_record.
        """
        if not self.data or self.data[-1] == (2**32) - 1:
            sequencenumber = 1
        else:
            sequencenumber = self.data[-1].sequencenumber + 1
        _rec = Record(
            timestamp,
            value,
            flags,
            sequencenumber,
            interval,
            trendFlag=None,
            logEvent=None,
        )
        if _rec.timestamp not in [each.timestamp for each in self.data]:
            self.data.append(_rec)

        # limit to 250 values
        self.data = self.data[-self.bufferSize :]
        if update_after:
            self.update_properties()

    def update_properties(self) -> None:
        """
        Meant to update trendLog properties like logBuffer,
        startTime, stopTime, recordCount, totalRecordCount, statusFlags, etc...
        """
        # startTime = self.data[0].timestamp
        # stopTime = self.data[-1].timestamp
        if not getattr(self.obj, "enable"):
            if getattr(self.obj, "recordCount") == 0:
                self.data = []  # empty it
            else:
                return  # disable....

        count = len(self.data)
        SequenceOfLogRecord = ListOf(LogRecord)()
        for each in self.data:
            logRecord = self.to_bacpypes_logrecord(each)
            SequenceOfLogRecord.append(logRecord)
        _props = {
            # "startTime": startTime,
            # "stopTime": stopTime,
            "logBuffer": SequenceOfLogRecord,
            "recordCount": Unsigned(count),
            "bufferSize": Unsigned(self.bufferSize),
            "enable": True,
            "stopWhenFull": False,
            "statusFlags": self.statusFlags,
            "totalRecordCount": Unsigned(self.data[-1].sequencenumber),
            "logInterval": Unsigned(self.data[-1].interval),
            "loggingType": LoggingType(0),
            "eventState": EventState(0),
            "reliability": Reliability(0),
        }
        for k, v in _props.items():
            setattr(self.obj, k, v)
