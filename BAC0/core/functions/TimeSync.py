#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
TimeSync.py - creation of time synch requests

"""

import datetime as dt
from datetime import datetime

# --- standard Python modules ---

import pytz
from bacpypes3.apdu import TimeSynchronizationRequest, UTCTimeSynchronizationRequest
from bacpypes3.app import Application
from bacpypes3.basetypes import DateTime

# --- 3rd party modules ---
from bacpypes3.pdu import Address, GlobalBroadcast, LocalBroadcast
from bacpypes3.primitivedata import Date, Time

from BAC0.core.app.asyncApp import BAC0Application

from ...core.utils.notes import note_and_log
from ..io.IOExceptions import ApplicationNotStarted


def _build_datetime(UTC=False):
    if UTC:
        _d = dt.datetime.utcnow().date()
        _t = dt.datetime.utcnow().time()
        _date = Date((_d.year - 1900, _d.month, _d.day, _d.isoweekday()))
        _time = Time(
            (
                _t.hour,
                _t.minute,
                _t.second,
                int(_t.microsecond / 10000),
            )
        )
    else:
        _date = Date().now()
        _time = Time().now()
    return DateTime(date=_date, time=_time)


@note_and_log
class TimeSync:
    """
    Mixin to support Time Synchronisation from BAC0 to other devices
    """

    def time_sync(
        self, destination: str = None, datetime: DateTime = None, UTC: bool = False
    ) -> None:
        """
        Take local time and send it to devices. User can also provide
        a datetime value (constructed following bacpypes.basetypes.Datetime
        format).

        To create a DateTime ::

            from bacpypes.basetypes import DateTime
            from bacpypes.primitivedata import Date, Time

            # Create date and time
            _date = Date('2019-08-05')
            _time = Time('16:45')

            # Create Datetime
            _datetime = DateTime(date=_date.value, time=_time.value)

            # Pass this to the function
            bacnet.time_sync(datetime=_datetime)


        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        if not datetime:
            _datetime = _build_datetime(UTC=UTC)
        elif isinstance(datetime, DateTime):
            _datetime = datetime
        else:
            raise ValueError(
                "Please provide valid DateTime in bacpypes.basetypes.DateTime format"
            )

        # build a request
        if UTC:
            request = UTCTimeSynchronizationRequest(time=_datetime)
        else:
            request = TimeSynchronizationRequest(time=_datetime)

        if destination:
            if destination.lower() == "global":
                request.pduDestination = GlobalBroadcast()
            elif destination.lower() == "local":
                request.pduDestination = LocalBroadcast()
            else:
                try:
                    request.pduDestination = Address(destination)
                except (TypeError, ValueError):
                    self.log(
                        "Destination unrecognized ({destination}), setting local broadcast",
                        level="warning",
                    )
                    request.pduDestination = LocalBroadcast()
        else:
            request.pduDestination = LocalBroadcast()

        self.log(f"{'- request:':>12} {request}", level="debug")

        _app.request(request)

        year, month, day, dow = _datetime.date
        year = year + 1900
        hour, minutes, sec, msec = _datetime.time
        d = dt.datetime(year, month, day, hour, minutes, sec, msec)
        self.log(f"Time Sync Request sent to network : {d.isoformat()}", level="info")


class TimeHandler(object):
    """
    This class will deal with Time / Timezone related features
    To deal with DateTime Value correctly we need to be aware
    of timezone.
    """

    def __init__(self, tz: str = "America/Montreal") -> None:
        self.set_timezone(tz)

    def set_timezone(self, tz: str) -> None:
        self.timezone = pytz.timezone(tz)

    @property
    def now(self) -> datetime:
        return dt.datetime.now()

    def local_time(self):
        return self.now.time()

    def local_date(self) -> datetime.date:
        return self.now.date()

    def utcOffset(self) -> float:
        "Returns UTC offset in minutes"
        return round(self.now.astimezone().utcoffset().total_seconds() / 60)  # type: ignore[union-attr]

    def is_dst(self) -> bool:
        return self.timezone.dst(self.now) != dt.timedelta(0)

    def __repr__(self):
        return f"{self.__dict__}"
