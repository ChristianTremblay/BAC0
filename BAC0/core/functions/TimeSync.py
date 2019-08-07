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
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.primitivedata import Date, Time
from bacpypes.basetypes import DateTime
from bacpypes.apdu import TimeSynchronizationRequest
from bacpypes.iocb import IOCB
from bacpypes.core import deferred


@note_and_log
class TimeSync:
    """
    Mixin to support Time Synchronisation from BAC0 to other devices
    """

    def time_sync(self, *args, datetime=None):
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
            _datetime = DateTime(date=_date, time=_time)

            # Pass this to the function
            bacnet.time_sync(datetime=_datetime)


        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        if args:
            args = args[0].split()
        msg = args if args else "everyone"

        self._log.debug("time sync {!r}".format(msg))

        if not datetime:
            _date = Date().now().value
            _time = Time().now().value
            _datetime = DateTime(date=_date, time=_time)
        elif isinstance(datetime, DateTime):
            _datetime = datetime
        else:
            raise ValueError(
                "Please provide valid DateTime in bacpypes.basetypes.DateTime format"
            )

        # build a request
        request = TimeSynchronizationRequest(time=_datetime)
        if len(args) == 1:
            request.pduDestination = Address(args[0])
            del args[0]
        else:
            request.pduDestination = GlobalBroadcast()

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
