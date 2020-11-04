#!/usr/bin/env python

"""
Johnson Controls Proprietary Objects for FX/FEC Line
"""
from bacpypes.primitivedata import (
    Real,
    Boolean,
    CharacterString,
    Enumerated,
    Unsigned,
    Atomic,
)
from bacpypes.object import (
    Object,
    DeviceObject,
    AnalogValueObject,
    AnalogInputObject,
    AnalogOutputObject,
    BinaryValueObject,
    Property,
    register_object_type,
)

#
#   Proprietary Objects and their attributes
#

JCIDeviceObject = {
    "name": "JCIDeviceObject",
    "vendor_id": 5,
    "objectType": "device",
    "bacpypes_type": DeviceObject,
    "properties": {
        "SupervisorOnline": {"obj_id": 3653, "primitive": Boolean, "mutable": True},
        "Model": {"obj_id": 1320, "primitive": CharacterString, "mutable": True},
        "ModelType": {"obj_id": 32527, "primitive": CharacterString, "mutable": True},
        "State": {"obj_id": 2390, "primitive": CharacterString, "mutable": False},
        "MemoryUsage": {"obj_id": 2581, "primitive": Real, "mutable": False},
        "ObjectMemoryUsage": {"obj_id": 2582, "primitive": Real, "mutable": False},
        "CPU": {"obj_id": 2583, "primitive": Real, "mutable": False},
        "FlashUsage": {"obj_id": 2584, "primitive": Real, "mutable": False},
        "JCISystemStatus": {"obj_id": 847, "primitive": Enumerated, "mutable": False},
        "SABusPerformance": {
            "obj_id": 12157,
            "primitive": Enumerated,
            "mutable": False,
        },
        "SABusTokenLoopTime": {
            "obj_id": 12158,
            "primitive": Unsigned,
            "mutable": False,
        },
        "SABusCOVRcvPerMinute": {
            "obj_id": 12159,
            "primitive": Unsigned,
            "mutable": False,
        },
        "SABusCOVWritesPerMinute": {
            "obj_id": 12160,
            "primitive": Unsigned,
            "mutable": False,
        },
        "CPU Idle": {"obj_id": 30082, "primitive": Real, "mutable": False},
        "alarm": {"obj_id": 673, "primitive": Boolean, "mutable": False},
        "end_of_line": {"obj_id": 603, "primitive": Boolean, "mutable": False},
        "objectStatus": {"obj_id": 512, "primitive": Enumerated, "mutable": False},
    },
}
# EOL ?
# MEMORY ?

JCIAnalogValueObject = {
    "name": "JCIAnalogValueObject",
    "vendor_id": 5,
    "objectType": "analogValue",
    "bacpypes_type": AnalogValueObject,
    "properties": {
        "FLOW-SP_EEPROM": {"obj_id": 3113, "primitive": Real, "mutable": True},
        "Offset": {"obj_id": 956, "primitive": Real, "mutable": True},
        "Offline": {"obj_id": 913, "primitive": Boolean, "mutable": False},
        "SABusAddr": {"obj_id": 3645, "primitive": Unsigned, "mutable": False},
        "PeerToPeer": {"obj_id": 748, "primitive": Atomic, "mutable": False},
        "P2P_ErrorStatus": {"obj_id": 746, "primitive": Enumerated, "mutable": False},
    },
}

JCIAnalogInputObject = {
    "name": "JCIAnalogInputObject",
    "vendor_id": 5,
    "objectType": "analogInput",
    "bacpypes_type": AnalogInputObject,
    "properties": {
        "Offset": {"obj_id": 956, "primitive": Real, "mutable": True},
        "Offline": {"obj_id": 913, "primitive": Boolean, "mutable": False},
        "SABusAddr": {"obj_id": 3645, "primitive": Unsigned, "mutable": False},
        "InputRangeLow": {"obj_id": 1293, "primitive": Real, "mutable": True},
        "InputRangeHigh": {"obj_id": 1294, "primitive": Real, "mutable": True},
        "OutputRangeLow": {"obj_id": 1295, "primitive": Real, "mutable": True},
        "OutputRangeHigh": {"obj_id": 1296, "primitive": Real, "mutable": True},
    },
}

JCIAnalogOutputObject = {
    "name": "JCIAnalogOutputObject",
    "vendor_id": 5,
    "objectType": "analogOutput",
    "bacpypes_type": AnalogOutputObject,
    "properties": {
        "Offline": {"obj_id": 913, "primitive": Boolean, "mutable": False},
        "SABusAddr": {"obj_id": 3645, "primitive": Unsigned, "mutable": False},
        "InputRangeLow": {"obj_id": 1293, "primitive": Real, "mutable": True},
        "InputRangeHigh": {"obj_id": 1294, "primitive": Real, "mutable": True},
        "OutputRangeLow": {"obj_id": 1295, "primitive": Real, "mutable": True},
        "OutputRangeHigh": {"obj_id": 1296, "primitive": Real, "mutable": True},
        "polarity": {"obj_id": "polarity", "primitive": Enumerated, "mutable": True},
        "stroketime": {"obj_id": 3478, "primitive": Real, "mutable": True},
    },
}


def tec_short_point_list():
    return [
        ("binaryInput", 30827),
        ("binaryInput", 30828),
        ("binaryOutput", 86908),
        ("binaryOutput", 86909),
        ("binaryOutput", 86910),
        ("binaryOutput", 86911),
        ("binaryOutput", 86912),
        ("binaryOutput", 87101),
        ("binaryOutput", 87102),
        ("multiStateValue", 29501),
        ("multiStateValue", 29500),
        ("multiStateValue", 29509),
        ("multiStateValue", 29517),
        ("multiStateValue", 29518),
        ("multiStateValue", 29519),
        ("multiStateValue", 29520),
        ("multiStateValue", 29524),
        ("multiStateValue", 29525),
        ("multiStateValue", 29527),
        ("multiStateValue", 29712),
        ("multiStateValue", 29700),
        ("multiStateValue", 29709),
        ("multiStateValue", 29708),
        ("analogValue", 29505),
        ("analogValue", 29502),
        ("analogValue", 29503),
        ("analogValue", 29504),
        ("analogValue", 29506),
        ("analogValue", 29507),
        ("analogValue", 29508),
        ("analogValue", 29515),
        ("analogValue", 29522),
        ("analogValue", 29529),
        ("analogValue", 29530),
        ("analogValue", 29532),
        ("analogValue", 29701),
        ("analogValue", 29703),
        ("analogValue", 29705),
        ("analogValue", 29706),
        ("analogValue", 29707),
        ("analogValue", 29714),
        ("analogValue", 29717),
        ("analogValue", 29725),
        ("analogValue", 29726),
        ("analogValue", 29727),
        ("analogOutput", 86905),
        ("analogOutput", 86914),
        ("analogOutput", 86915),
        ("multiStateValue", 6),
        ("trendLog", 101010),
    ]
