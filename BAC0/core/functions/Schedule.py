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

    schedule_example_multistate = {
        "states": {"Occupied": 1, "UnOccupied": 2, "Standby": 3, "Not Set": 4},
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
    schedule_example_binary = {
        "states": {"inactive": 0, "active": 1},
        "week": {
            "monday": [("1:00", "active"), ("16:00", "inactive")],
            "tuesday": [("2:00", "active"), ("16:00", "inactive")],
            "wednesday": [("3:00", "active"), ("16:00", "inactive")],
            "thursday": [("4:00", "active"), ("16:00", "inactive")],
            "friday": [("5:00", "active"), ("16:00", "inactive")],
            "saturday": [("6:00", "active"), ("16:00", "inactive")],
            "sunday": [("7:00", "active"), ("16:00", "inactive")],
        },
    }
    schedule_example_analog = {
        "states": "analog",
        "week": {
            "monday": [("1:00", 22), ("18:00", 19)],
            "tuesday": [("2:00", 22), ("18:00", 19)],
            "wednesday": [("3:00", 22), ("18:00", 19)],
            "thursday": [("4:00", 22), ("18:00", 19)],
            "friday": [("5:00", 22), ("18:00", 19)],
            "saturday": [("6:00", 22), ("18:00", 19)],
            "sunday": [("7:00", 22), ("18:00", 19)],
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

        def _set_value(v):
            try:
                if dict_schedule["states"].lower() == "analog":
                    return Real(v)
            except AttributeError:
                if dict_schedule["states"] == ["inactive", "active"]:
                    return Integer(dict_schedule["states"][v])
                else:
                    return Integer(dict_schedule["states"][v] - 1)

        daily_schedules = []
        for day in Schedule.days:
            list_of_events = dict_schedule["week"][day]
            _daily_schedule = [
                TimeValue(time=event[0], value=_set_value(event[1]))
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
            _schedule, object_references, reliability, priority, presentValue = self.readMultiple(
                "{} schedule {} weeklySchedule listOfObjectPropertyReferences reliability priorityForWriting presentValue".format(
                    address, schedule_instance
                )
            )

        except Exception:
            # Rwad Multiple not supported... try single prop read
            def _read(prop):
                return self.read(
                    "{} schedule {} {}".format(address, schedule_instance, prop)
                )

            try:
                _schedule = _read("weeklySchedule")
                object_references = _read("listOfObjectPropertyReferences")
                reliability = _read("reliability")
                priority = _read("priorityForWriting")
                presentValue = _read("presentValue")

            except Exception:
                raise ()

        schedule = {}
        _state_text = None
        offset_MV = 0 if len(object_references) == 0 else 1

        try:
            first_obj_id = object_references[0]
            obj_type, obj_instance = first_obj_id.objectIdentifier
            if obj_type == "binaryValue":
                _state_text = ["inactive", "active"]
            elif "multi" in obj_type:
                _state_text = self.read(
                    "{} {} {} stateText".format(address, obj_type, obj_instance)
                )
            elif "analog" in obj_type:
                _state_text = "analog"

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
        except Exception as error:
            self._log.error("Error {}".format(error))
            # Not used in device, not linked...
            _state_text = range(255)
            schedule["object_references"] = []
            schedule["references_names"] = []

        schedule["states"] = {}
        if _state_text == ["inactive", "active"]:
            for i, each in enumerate(_state_text):
                schedule["states"][each] = i
            presentValue = "{} ({})".format(
                list(schedule["states"].keys())[int(presentValue.value)],
                presentValue.value,
            )
        elif _state_text != "analog":
            for i, each in enumerate(_state_text):
                schedule["states"][each] = i + offset_MV
            try:
                presentValue = "{} ({})".format(
                    list(schedule["states"].keys())[
                        int(presentValue.value) - offset_MV
                    ],
                    presentValue.value,
                )
            except TypeError:
                presentValue = presentValue.value
        else:
            schedule["states"] = _state_text
            presentValue = "{}".format(presentValue.value)
        schedule["reliability"] = reliability
        schedule["priority"] = priority
        schedule["presentValue"] = presentValue
        schedule["week"] = self.decode_weeklySchedule(_schedule, _state_text, offset_MV)

        return schedule

    def decode_weeklySchedule(self, weeklySchedule, states, offset_MV):
        week = {}
        for i, day in enumerate(Schedule.days):
            week[day] = self.decode_dailySchedule(weeklySchedule[i], states, offset_MV)
        return week

    def decode_dailySchedule(self, dailySchedule, states, offset_MV):
        events = []
        for each in dailySchedule.daySchedule:
            hour, minute, second, hundreth = each.time
            _time = dt_time(hour, minute, second, hundreth).strftime("%H:%M")
            try:
                if states == ["inactive", "active"]:
                    _value = states[int(each.value.value)]
                elif states == "analog":
                    _value = float(each.value.value)
                else:
                    _value = states[int(each.value.value) - offset_MV]
                events.append((_time, _value))
            except IndexError:
                events.append((_time, "??? ({})".format(each.value.value)))
        return events
