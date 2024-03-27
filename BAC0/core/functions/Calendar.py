#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
# --- standard Python modules ---
import datetime
import typing as t

from bacpypes3.apdu import WritePropertyRequest
from bacpypes3.app import Application
from bacpypes3.basetypes import CalendarEntry, DateRange
from bacpypes3.constructeddata import Any, ArrayOf

# --- 3rd party modules ---
from bacpypes3.pdu import Address

from ...core.app.asyncApp import BAC0Application
from ...core.utils.notes import note_and_log


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
                    weekday = datetime.date(year, month, day).weekday() + 1
                    if weekday > 7:
                        weekday = 1
                _date = (year - 1900, month, day, weekday)
                entries.append(CalendarEntry(date=_date))

        if "dateRanges" in dict_calendar.keys():
            for date_range_entry in dict_calendar["dateRanges"]:
                year, month, day = (
                    int(x) for x in date_range_entry["startDate"].split("/")
                )
                weekday = datetime.date(year, month, day).weekday() + 1
                if weekday > 7:
                    weekday = 1
                start_date = (year - 1900, month, day, weekday)

                year, month, day = (
                    int(x) for x in date_range_entry["endDate"].split("/")
                )
                weekday = datetime.date(year, month, day).weekday() + 1
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
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        self.log(f"{'- request:':>12} {request}", level="debug")

        _app.request(request)

        self._log.info(
            f"Calendar Write request sent to device : {request.pduDestination}"
        )

    def write_calendar_dateList(self, destination, calendar_instance, dates):
        calendar = self.create_calendar(dates)
        request = self.make_calendar_request(
            destination=destination,
            object_instance=calendar_instance,
            dateList=calendar,
        )
        self.send_calendar_request(request)

    async def read_calendar_dateList(self, address, calendar_instance):
        """
        This function will read the dateList property of given calendar object and
        pass it to decode_dateList() to convert it into a human readable dict.
        """

        try:
            dateList_object = await self.read(
                f"{address} calendar {calendar_instance} dateList"
            )
            dict_calendar = self.decode_dateList(dateList_object)
        except Exception as error:
            self.log(f"exception: {error!r}", level="error")
            return {}

        return dict_calendar

    def decode_dateList(self, dateList_object) -> t.Dict[str, t.List[t.Dict]]:
        dict_calendar = {"dates": [], "dateRanges": []}
        for entry in dateList_object:
            entry_dict: t.Dict[str, t.Union[str, bool]] = {}
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
