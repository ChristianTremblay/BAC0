import bacpypes
import pytest

import BAC0
from BAC0.core.devices.local.factory import (
    analog_input,
    analog_output,
    analog_value,
    binary_input,
    binary_output,
    binary_value,
    character_string,
    date_value,
    datetime_value,
    humidity_input,
    humidity_value,
    multistate_input,
    multistate_output,
    multistate_value,
    temperature_input,
    temperature_value,
    make_state_text
)




def build():
    bacnet = BAC0.Async(deviceId=3056235)
    # Add 10 AI with automatic names
    for each in range(10):
        _new_objects = analog_input()

    # Add 10 BI with names from a list
    names_list = ["A", "B", "C"]
    for i, each in enumerate(range(3)):
        _new_objects = binary_input(name=names_list[i])

    # Multistates objects
    _new_object = multistate_value(description="A Simple On Off Value")

    states = make_state_text(["Normal", "Alarm", "Super Emergency"])
    _new_object = multistate_value(
        description="An Alarm Value",
        properties={"stateText": states},
        name="BIG-ALARM",
        is_commandable=True,
    )

    # Add to BAC0
    _new_objects.add_objects_to_application(bacnet)
    return bacnet


bacnet = build()
while True:
    pass
