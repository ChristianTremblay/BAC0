#!/usr/bin/env python

"""
Johnson Controls Proprietary Objects for FX/FEC Line
"""
from bacpypes.primitivedata import Boolean, CharacterString
from bacpypes.object import (
    DeviceObject,
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
        "Model": {"obj_id": 1320, "primitive": CharacterString, "mutable": False},
    },
}


def tec_short_point_list():
    lst = [
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
    ]
    return lst
