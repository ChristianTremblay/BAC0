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
from bacpypes.primitivedata import Integer, Date, Time, CharacterString
from bacpypes.basetypes import DateTime
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU
from bacpypes.iocb import IOCB
from bacpypes.core import deferred
from bacpypes.basetypes import DateTime, DailySchedule, TimeValue, Time
from bacpypes.constructeddata import ArrayOf, Any

from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real, Enumerated

from datetime import time as dt_time
from datetime import datetime as dt


@note_and_log
class Schedule:
    """
    Everything you need to write to a schedule
    """

    WeeklySchedule = ArrayOf(DailySchedule)
    schedules = {}
    days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    schedule_example = {
        "states": {"UnOccupied": 1, "Occupied": 2},
        "week": {
            "monday": [("1:00", "Occupied"), ("17:00", "UnOccupied")],
            "tuesday": [("2:00", "Occupied"), ("17:00", "UnOccupied")],
            "wednesday": [("3:00", "Occupied"), ("17:00", "UnOccupied")],
            "thursday": [("4:00", "Occupied"), ("17:00", "UnOccupied")],
            "friday": [("5:00", "Occupied"), ("17:00", "UnOccupied")],
            "saturday": [("6:00", "Occupied"), ("17:00", "UnOccupied")],
            "sunday": [("7:00", "Occupied"), ("17:00", "UnOccupied")],
        },
    }

    def create_weeklySchedule(self, dict_schedule, object_reference=None):
        """
        From a structured dict (see schedule_example), create a WeeklySchedule
        an ArrayOf(DailySchedule)
        """
        object_reference = object_reference
        ds = dict_schedule
        if object_reference is not None:
            self.schedules[object_reference] = ds

        daily_schedules = []
        for day in Schedule.days:
            list_of_events = dict_schedule["week"][day]
            _daily_schedule = [
                TimeValue(
                    time=event[0], value=Integer(dict_schedule["states"][event[1]])
                )
                for event in list_of_events
            ]
            daily_schedules.append(DailySchedule(daySchedule=_daily_schedule))
        return Schedule.WeeklySchedule(daily_schedules)

    def make_weeklySchedule_request(self, destination, object_instance, weeklySchedule):
        request = WritePropertyRequest(
            objectIdentifier=("schedule", object_instance),
            propertyIdentifier="weeklySchedule",
        )

        address = Address(destination)
        request.pduDestination = address
        request.propertyValue = Any()
        request.propertyValue.cast_in(weeklySchedule)
        request.priority = 15
        return request

    def send_weeklyschedule_request(self, request):
        iocb = IOCB(request)
        iocb.set_timeout(10)
        deferred(self.this_application.request_io, iocb)

        iocb.wait()

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
            "Schedule Write request sent to device : {}".format(request.pduDestination)
        )

    def write_weeklySchedule(self, destination, schedule_instance, schedule):
        weeklyschedule = self.create_weeklySchedule(schedule)
        request = self.make_weeklySchedule_request(
            destination=destination,
            object_instance=schedule_instance,
            weeklySchedule=weeklyschedule,
        )
        self.send_weeklyschedule_request(request)

    def read_weeklySchedule(self, address, schedule_instance):
        """
        This function will turn the weeklySchedule received into a 
        human readable dict. 
        This dict can then be modified and used to write back to controller
        using bacnet.write_weeklySchedule
        """
        try:
            _schedule, object_references = self.readMultiple(
                "{} schedule {} weeklySchedule listOfObjectPropertyReferences".format(
                    address, schedule_instance
                )
            )

        except Exception:
            try:
                _schedule = self.read(
                    "{} schedule {} weeklySchedule".format(address, schedule_instance)
                )
                object_references = self.read(
                    "{} schedule {} listOfObjectPropertyReferences".format(
                        address, schedule_instance
                    )
                )
            except Exception:
                raise ()

        schedule = {}

        try:
            first_obj_id = object_references[0]
            obj_type, obj_instance = first_obj_id.objectIdentifier
            _state_text = self.read(
                "{} {} {} stateText".format(address, obj_type, obj_instance)
            )
            schedule["object_references"] = [
                objectId.objectIdentifier for objectId in object_references
            ]
            schedule["references_names"] = [
                self.read(
                    "{} {} {} objectName".format(
                        address, each.objectIdentifier[0], each.objectIdentifier[1]
                    )
                )
                for each in object_references
            ]
        except Exception:
            # Not used in device, not linked...
            _state_text = range(255)
            schedule["object_references"] = []
            schedule["references_names"] = []

        schedule["states"] = {}
        for i, each in enumerate(_state_text):
            schedule["states"][each] = i + 1
        schedule["states"]
        schedule["week"] = self.decode_weeklySchedule(_schedule, _state_text)

        return schedule

    def decode_weeklySchedule(self, weeklySchedule, states):
        week = {}
        for i, day in enumerate(Schedule.days):
            week[day] = self.decode_dailySchedule(weeklySchedule[i], states)
        return week

    def decode_dailySchedule(self, dailySchedule, states):
        events = []
        for each in dailySchedule.daySchedule:
            hour, minute, second, hundreth = each.time
            _time = dt_time(hour, minute, second, hundreth).strftime("%H:%M")
            _value = states[int(each.value.value) - 1]
            events.append((_time, _value))
        return events