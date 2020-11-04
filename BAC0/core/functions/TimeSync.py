#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
TimeSync.py - creation of time synch requests

"""
from ...core.io.Read import find_reason
from ..io.IOExceptions import (
    SegmentationNotSupported,
    ReadPropertyException,
    ReadPropertyMultipleException,
    NoResponseFromController,
    ApplicationNotStarted,
)
from ...core.utils.notes import note_and_log

# --- standard Python modules ---
import datetime as dt

# --- 3rd party modules ---
from bacpypes.pdu import Address, GlobalBroadcast, LocalBroadcast
from bacpypes.primitivedata import Date, Time
from bacpypes.basetypes import DateTime
from bacpypes.apdu import TimeSynchronizationRequest, UTCTimeSynchronizationRequest
from bacpypes.iocb import IOCB
from bacpypes.core import deferred


def _build_datetime(UTC=False):
    if UTC:
        _d = dt.datetime.utcnow().date()
        _t = dt.datetime.utcnow().time()
        _date = Date(
            year=_d.year - 1900, month=_d.month, day=_d.day, day_of_week=_d.isoweekday()
        ).value
        _time = Time(
            hour=_t.hour,
            minute=_t.minute,
            second=_t.second,
            hundredth=int(_t.microsecond / 10000),
        ).value
    else:
        _date = Date().now().value
        _time = Time().now().value
    return DateTime(date=_date, time=_time)


@note_and_log
class TimeSync:
    """
    Mixin to support Time Synchronisation from BAC0 to other devices
    """

    def time_sync(self, destination=None, datetime=None, UTC=False):
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
                    self._log.warning(
                        "Destination unrecognized ({}), setting local broadcast".format(
                            destination
                        )
                    )
                    request.pduDestination = LocalBroadcast()
        else:
            request.pduDestination = LocalBroadcast()

        self._log.debug("{:>12} {}".format("- request:", request))

        iocb = IOCB(request)  # make an IOCB

        # pass to the BACnet stack
        deferred(self.this_application.request_io, iocb)

        # Unconfirmed request...so wait until complete
        iocb.wait()  # Wait for BACnet response
        year, month, day, dow = _datetime.date
        year = year + 1900
        hour, minutes, sec, msec = _datetime.time
        d = dt.datetime(year, month, day, hour, minutes, sec, msec)
        self._log.info("Time Sync Request sent to network : {}".format(d.isoformat()))
