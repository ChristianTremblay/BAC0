import pytest
import bacpypes
import BAC0

from bacpypes.primitivedata import Real, CharacterString
from BAC0.core.devices.local.object import ObjectFactory
from bacpypes.object import (
    AnalogValueObject,
    CharacterStringValueObject,
    AnalogInputObject,
)


def build():
    bacnet = BAC0.lite(deviceId=3056235)

    new_obj = ObjectFactory(
        AnalogValueObject,
        0,
        "av0",
        properties={"units": "degreesCelsius"},
        presentValue=1,
        description="Analog Value 0",
    )
    ObjectFactory(
        AnalogValueObject,
        1,
        "av1",
        properties={"units": "degreesCelsius"},
        presentValue=12,
        description="Analog Value 1",
        is_commandable=True,
    )
    ObjectFactory(
        CharacterStringValueObject,
        0,
        "cs0",
        presentValue="Default value",
        description="String Value 0",
    )
    ObjectFactory(
        CharacterStringValueObject,
        1,
        "cs1",
        presentValue="Default value",
        description="Writable String Value 1",
        is_commandable=True,
    )

    new_obj.add_objects_to_application(bacnet.this_application)
    return bacnet


def test_creation():
    bacnet = build()
    while True:
        pass
