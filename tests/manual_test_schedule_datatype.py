from datetime import datetime as dt
from datetime import time as dt_time

from bacpypes.basetypes import DailySchedule, DateTime, Time, TimeValue
from bacpypes.constructeddata import ArrayOf
from bacpypes.primitivedata import Atomic, Enumerated, Integer, Null, Real, Unsigned

sched = [
    {
        "daySchedule": [
            {"time": dt_time(3, 0), "value": 1},
            {"time": dt_time(19, 0), "value": 0},
        ]
    },
    {
        "daySchedule": [
            {"time": dt_time(4, 0), "value": 1},
            {"time": dt_time(19, 0), "value": 0},
        ]
    },
    {
        "daySchedule": [
            {"time": dt_time(4, 0), "value": 1},
            {"time": dt_time(19, 0), "value": 0},
        ]
    },
    {
        "daySchedule": [
            {"time": dt_time(4, 0), "value": 1},
            {"time": dt_time(19, 0), "value": 0},
        ]
    },
    {
        "daySchedule": [
            {"time": dt_time(4, 0), "value": 1},
            {"time": dt_time(19, 0), "value": 0},
        ]
    },
    {"daySchedule": []},
    {"daySchedule": []},
]


class ArrayOfDailySchedule(ArrayOf(DailySchedule)):
    def __init__(self, schedule_as_a_dict):
        self.value = self.dict_to_weeklyschedule(schedule_as_a_dict)

    def dict_to_timevalue(self, val):
        return TimeValue(time=self.to_time_tuple(val["time"]), value=(val["value"]))

    def dict_to_dailyschedule(self, val):
        return DailySchedule(
            daySchedule=[self.dict_to_timevalue(x) for x in val["daySchedule"]]
        )

    def dict_to_weeklyschedule(self, val):
        return ArrayOf(DailySchedule)([self.dict_to_dailyschedule(x) for x in val])

    def to_time_tuple(self, val):
        try:
            if isinstance(val, dt_time):
                return Time(
                    hour=val.hour,
                    minute=val.minute,
                    second=val.second,
                    hundredth=val.microsecond,
                ).value
            elif isinstance(val, str):
                return self.to_time_tuple(dt.datetime.strptime(val, "%H:%M:%S").time())
            else:
                raise Exception("Unsupported time format encountered!")
        except Exception as e:
            raise Exception("Error during parsing time format to bacnet!")
