#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
ScheduleWrite.py - creation of ReinitializeDeviceRequest

"""
from ..io.Read import find_reason
from ..io.IOExceptions import NoResponseFromController
from ...core.utils.notes import note_and_log

# --- standard Python modules ---
import datetime as dt

# --- 3rd party modules ---
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.primitivedata import Integer, Date, Time, CharacterString
from bacpypes.basetypes import DateTime
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU
from bacpypes.iocb import IOCB
from bacpypes.core import deferred
from bacpypes.basetypes import (
    DateTime,
    DailySchedule,
    TimeValue,
    Time,
    CalendarEntry,
    DateRange,
)
from bacpypes.constructeddata import ArrayOf, Any
from BAC0.core.io.IOExceptions import NoResponseFromController, WritePropertyException

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real, Enumerated

from datetime import time as dt_time
from datetime import datetime as dt


@note_and_log
class Calendar:
    """
    Everything you need to write dates and date ranges to a calendar object.
    """

    DateList = ArrayOf(CalendarEntry)
    datelist_example = {
        "dates": [
            {"date": "2021/3/14", "recurring": False},
            {"date": "2021/3/10", "recurring": True},
        ],
        "dateRanges": [
            {"startDate": "2021/3/16", "endDate": "2021/3/21"},
            {"startDate": "2021/3/5", "endDate": "2021/3/7"},
        ],
    }

    def create_calendar(self, dict_calendar):
        """
        From a structured dict (see dateList_example), create a DateList
        an ArrayOf(CalendarEntry)
        """

        entries = []
        if "dates" in dict_calendar.keys():
            for date_entry in dict_calendar["dates"]:
                year, month, day = (int(x) for x in date_entry["date"].split("/"))
                if date_entry["recurring"]:
                    weekday = 255
                else:
                    weekday = dt.date(year, month, day).weekday() + 1
                    if weekday > 7:
                        weekday = 1
                _date = (year - 1900, month, day, weekday)
                entries.append(CalendarEntry(date=_date))

        if "dateRanges" in dict_calendar.keys():
            for date_range_entry in dict_calendar["dateRanges"]:
                year, month, day = (
                    int(x) for x in date_range_entry["startDate"].split("/")
                )
                weekday = dt.date(year, month, day).weekday() + 1
                if weekday > 7:
                    weekday = 1
                start_date = (year - 1900, month, day, weekday)

                year, month, day = (
                    int(x) for x in date_range_entry["endDate"].split("/")
                )
                weekday = dt.date(year, month, day).weekday() + 1
                if weekday > 7:
                    weekday = 1
                end_date = (year - 1900, month, day, weekday)

                date_range = DateRange(startDate=start_date, endDate=end_date)
                entries.append(CalendarEntry(dateRange=date_range))

        dateList = self.DateList(entries)
        return dateList

    def make_calendar_request(self, destination, object_instance, dateList):
        request = WritePropertyRequest(
            objectIdentifier=("calendar", object_instance),
            propertyIdentifier="dateList",
        )

        address = Address(destination)
        request.pduDestination = address
        request.propertyValue = Any()
        request.propertyValue.cast_in(dateList)
        return request

    def send_calendar_request(self, request, timeout=10):
        iocb = IOCB(request)
        iocb.set_timeout(timeout)
        deferred(self.this_application.request_io, iocb)

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug(
                    "Not an ack. | APDU : {} / {}".format((apdu, type(apdu)))
                )
                return

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController("APDU Abort Reason : {}".format(reason))

        self._log.info(
            "Calendar Write request sent to device : {}".format(request.pduDestination)
        )

    def write_calendar_dateList(self, destination, calendar_instance, dates):
        calendar = self.create_calendar(dates)
        request = self.make_calendar_request(
            destination=destination,
            object_instance=calendar_instance,
            dateList=calendar,
        )
        self.send_calendar_request(request)

    def read_calendar_dateList(self, address, calendar_instance):
        """
        This function will read the dateList property of given calendar object and
        pass it to decode_dateList() to convert it into a human readable dict.
        """

        try:
            dateList_object = self.read(
                "{} calendar {} dateList".format(address, calendar_instance)
            )
            dict_calendar = self.decode_dateList(dateList_object)
        except Exception as error:
            self._log.error("exception: {!r}".format(error))
            return {}

        return dict_calendar

    def decode_dateList(self, dateList_object):
        dict_calendar = {"dates": [], "dateRanges": []}
        for entry in dateList_object:
            entry_dict = {}
            if entry.date:
                if entry.date[3] == 255:
                    recurring = True
                else:
                    recurring = False
                entry_dict["date"] = "{}/{}/{}".format(
                    entry.date[0] + 1900, entry.date[1], entry.date[2]
                )
                entry_dict["recurring"] = recurring
                dict_calendar["dates"].append(entry_dict)
            elif entry.dateRange:
                entry_dict["startDate"] = "{}/{}/{}".format(
                    entry.dateRange.startDate[0] + 1900,
                    entry.dateRange.startDate[1],
                    entry.dateRange.startDate[2],
                )
                entry_dict["endDate"] = "{}/{}/{}".format(
                    entry.dateRange.endDate[0] + 1900,
                    entry.dateRange.endDate[1],
                    entry.dateRange.endDate[2],
                )
                dict_calendar["dateRanges"].append(entry_dict)

        return dict_calendar
