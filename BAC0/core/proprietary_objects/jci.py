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
    Date,
    Time,
    #    Signed,
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
#   https://cgproducts.johnsoncontrols.com/MET_PDF/12013102.pdf
#

JCIDeviceObject = {
    "name": "JCIDeviceObject",
    "vendor_id": 5,
    "objectType": "device",
    "bacpypes_type": DeviceObject,
    "properties": {
        "ALARM_STATE": {"obj_id": 1006, "datatype": Enumerated, "mutable": False},
        "ARCHIVE_DATE": {"obj_id": 849, "datatype": Date, "mutable": False},
        "ARCHIVE_STATUS": {"obj_id": 1187, "datatype": Unsigned, "mutable": False},
        "ARCHIVE_TIME": {"obj_id": 850, "datatype": Time, "mutable": False},
        "CPU_USAGE": {"obj_id": 2583, "datatype": Real, "mutable": False},
        "ENABLED": {"obj_id": 673, "datatype": Boolean, "mutable": True},
        "ENABLED": {"obj_id": 673, "datatype": Boolean, "mutable": True},
        "EXECUTION_PRIORITY": {
            "obj_id": 2197,
            "datatype": Enumerated,
            "mutable": True,
        },  # 0-3
        "EXTENDED_PROTO_VERSION": {
            "obj_id": 2291,
            "datatype": Unsigned,
            "mutable": False,
        },
        "FLASH_USAGE": {"obj_id": 2584, "datatype": Real, "mutable": False},
        "ITEM_REFERENCE": {
            "obj_id": 32527,
            "datatype": CharacterString,
            "mutable": False,
        },
        "JCI_STATUS": {"obj_id": 847, "datatype": Enumerated, "mutable": False},
        "MEMORY_USAGE": {"obj_id": 2581, "datatype": Real, "mutable": False},
        "OBJECT_CATEGORY": {
            "obj_id": 908,
            "datatype": Enumerated,
            "mutable": True,
        },  # 0-249
        "OBJECT_MEMORY_USAGE": {"obj_id": 2582, "datatype": Real, "mutable": False},
        "STATUS": {"obj_id": 512, "datatype": Enumerated, "mutable": False},
        "BACNET_BROADCAST_RECEIVE_RATE": {
            "obj_id": 745,
            "datatype": Unsigned,
            "mutable": False,
        },
        "DEFAULT_BASE_UNITS": {
            "obj_id": 2206,
            "datatype": Enumerated,
            "mutable": False,
        },
        "ESTIMATED_FLASH_AVAILABLE": {
            "obj_id": 2395,
            "datatype": Real,
            "mutable": False,
        },
        "LAST_IDLE_SAMPLE": {"obj_id": 30082, "datatype": Real, "mutable": False},
        "MAX_MESSAGE_BUFFER": {
            "obj_id": 848,
            "datatype": Unsigned,
            "mutable": True,
        },  # 98-65535
        "USER_NAME": {"obj_id": 2390, "datatype": CharacterString, "mutable": False},
        "PCODE": {"obj_id": 1320, "datatype": CharacterString, "mutable": False},
        # "SAB_DEVICE_STATUS_LIST": {"obj_id": 4513, "datatype": Complex, "mutable": False},
        "SAB_DEVICE_STATUS_LIST_CHANGED ": {
            "obj_id": 4514,
            "datatype": Unsigned,
            "mutable": False,
        },
        "EVENTS_LOST ": {"obj_id": 1479, "datatype": Unsigned, "mutable": False},
        # "STANDARD_TIME_OFFSET ": {"obj_id": 1017, "datatype": Signed, "mutable": False}, # -900-900
        # "DAYLIGHT_SAVING_TIME_OFFSET ": {"obj_id": 1093, "datatype": Signed, "mutable": False}, # -900-900
        # "STANDARD_TIME_START ": {"obj_id": 988, "datatype": Complex, "mutable": True},
        # "DAYLIGHT_SAVING_TIME_START ": {"obj_id": 1040, "datatype": Complex, "mutable": True},
        "ACCEPT_BACNET_TIME_SYNC": {
            "obj_id": 4970,
            "datatype": Boolean,
            "mutable": False,
        },
        # "LAST_BACNET_TIME_SYNC_RECEIVED ": {"obj_id": 5728, "datatype": Complex, "mutable": False},
        "SUPERVISORY_DEVICE_ONLINE": {
            "obj_id": 3653,
            "datatype": Boolean,
            "mutable": True,
        },
        "SUPERVISORY_OFFLINE_TIMEOUT": {
            "obj_id": 6002,
            "datatype": Unsigned,
            "mutable": True,
        },  # 1-255
        "NEXT_AVAILABLE_OID": {
            "obj_id": 787,
            "datatype": Unsigned,
            "mutable": True,
        },  # 30,000,001-41,799,991
        "HAS_UNBOUND_REFERENCES": {
            "obj_id": 767,
            "datatype": Boolean,
            "mutable": False,
        },
        "SURROGATE_CACHE_CNT": {"obj_id": 571, "datatype": Unsigned, "mutable": False},
        "SURROGATE_CACHE_MAX": {"obj_id": 639, "datatype": Unsigned, "mutable": False},
        # "ASSET_VERSIONS": {"obj_id": 4960, "datatype": Complex, "mutable": False},
        "LOAD_BALANCER_LEVEL": {
            "obj_id": 4722,
            "datatype": Enumerated,
            "mutable": False,
        },
        "TIMER_DB_SIZE": {"obj_id": 733, "datatype": Unsigned, "mutable": False},
        "TIMER_USED": {"obj_id": 734, "datatype": Unsigned, "mutable": False},
        "TIMER_PEAK": {"obj_id": 735, "datatype": Unsigned, "mutable": False},
        "TIMER_MESSAGES_ABORTED": {
            "obj_id": 4959,
            "datatype": Unsigned,
            "mutable": False,
        },
        "BACNET_OID_ALLOCATED": {
            "obj_id": 1291,
            "datatype": Unsigned,
            "mutable": False,
        },
        "BACNET_OID_USED": {"obj_id": 1292, "datatype": Unsigned, "mutable": False},
        "SIGN_PRI_DB_SIZE": {"obj_id": 730, "datatype": Unsigned, "mutable": False},
        "SIGN_PRI_USED": {"obj_id": 731, "datatype": Unsigned, "mutable": False},
        "SIGN_PRI_PEAK": {"obj_id": 732, "datatype": Unsigned, "mutable": False},
        "BACNET_ENCODE_TYPE": {
            "obj_id": 32578,
            "datatype": Enumerated,
            "mutable": True,
        },  # 0-3
        "ROUTING_MODE": {
            "obj_id": 4307,
            "datatype": Enumerated,
            "mutable": True,
        },  # 0-2
        "BACNET_INTEGRATED_OBJECTS": {
            "obj_id": 4302,
            "datatype": Enumerated,
            "mutable": False,
        },
        "BACNET_COMPATIBLE": {"obj_id": 4581, "datatype": Boolean, "mutable": False},
        "SEND_I_AM_RATE": {
            "obj_id": 579,
            "datatype": Unsigned,
            "mutable": True,
        },  # 60-86,400
        "DEFAULT_TIME_ZONE": {
            "obj_id": 32583,
            "datatype": Enumerated,
            "mutable": True,
        },  # #-1,101
        "TIME_ZONE": {
            "obj_id": 1403,
            "datatype": Enumerated,
            "mutable": True,
        },  # #-1,101
        "LOCAL_TIME_ZONE": {"obj_id": 1404, "datatype": Enumerated, "mutable": False},
        "FC_MULTICAST_RESPONDER": {
            "obj_id": 3390,
            "datatype": Unsigned,
            "mutable": True,
        },
        "FC_WAIT_BEFORE_POLLING": {
            "obj_id": 3391,
            "datatype": Unsigned,
            "mutable": True,
        },
        "SUPERVISOR_MAC_ADDRESS": {
            "obj_id": 3652,
            "datatype": Unsigned,
            "mutable": False,
        },
        "LIBRARY_PART_ID": {
            "obj_id": 3295,
            "datatype": CharacterString,
            "mutable": False,
        },
        "APPLICATION_CLASS_SET_VERSION": {
            "obj_id": 4128,
            "datatype": Unsigned,
            "mutable": False,
        },
        "DEVICE_MODEL_CLASS_SET_VERSION": {
            "obj_id": 4129,
            "datatype": Unsigned,
            "mutable": False,
        },
        "COV_MIN_SEND_TIME": {
            "obj_id": 3929,
            "datatype": Unsigned,
            "mutable": True,
        },  # 10-255
        "COV_TRANSMITS_PER_MINUTE": {
            "obj_id": 651,
            "datatype": Unsigned,
            "mutable": False,
        },
        "CONTROL_SEQUENCE_IN_TEST": {
            "obj_id": 3651,
            "datatype": Unsigned,
            "mutable": True,
        },
        "END_OF_LINE": {"obj_id": 603, "datatype": Boolean, "mutable": False},
        "DEVICE_ADDRESS": {"obj_id": 876, "datatype": Unsigned, "mutable": False},
        "FC_BUS_COMMUNICATION_MODE": {
            "obj_id": 4400,
            "datatype": Enumerated,
            "mutable": False,
        },
        "SYSTEM_TYPE": {"obj_id": 3900, "datatype": Unsigned, "mutable": False},
        "SYSTEM_CONFIGURATION": {
            "obj_id": 3899,
            "datatype": Unsigned,
            "mutable": False,
        },
        "SABusPerformance": {
            "obj_id": 12157,
            "datatype": Enumerated,
            "mutable": False,
        },
        "SABusTokenLoopTime": {
            "obj_id": 12158,
            "datatype": Unsigned,
            "mutable": False,
        },
        "SABusCOVRcvPerMinute": {
            "obj_id": 12159,
            "datatype": Unsigned,
            "mutable": False,
        },
        "SABusCOVWritesPerMinute": {
            "obj_id": 12160,
            "datatype": Unsigned,
            "mutable": False,
        },
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
        "FLOW-SP_EEPROM": {"obj_id": 3113, "datatype": Real, "mutable": True},
        "Offset": {"obj_id": 956, "datatype": Real, "mutable": True},
        "Offline": {"obj_id": 913, "datatype": Boolean, "mutable": False},
        "SABusAddr": {"obj_id": 3645, "datatype": Unsigned, "mutable": False},
        "PeerToPeer": {"obj_id": 748, "datatype": Atomic, "mutable": False},
        "P2P_ErrorStatus": {"obj_id": 746, "datatype": Enumerated, "mutable": False},
    },
}

JCIAnalogInputObject = {
    "name": "JCIAnalogInputObject",
    "vendor_id": 5,
    "objectType": "analogInput",
    "bacpypes_type": AnalogInputObject,
    "properties": {
        "Offset": {"obj_id": 956, "datatype": Real, "mutable": True},
        "Offline": {"obj_id": 913, "datatype": Boolean, "mutable": False},
        "SABusAddr": {"obj_id": 3645, "datatype": Unsigned, "mutable": False},
        "InputRangeLow": {"obj_id": 1293, "datatype": Real, "mutable": True},
        "InputRangeHigh": {"obj_id": 1294, "datatype": Real, "mutable": True},
        "OutputRangeLow": {"obj_id": 1295, "datatype": Real, "mutable": True},
        "OutputRangeHigh": {"obj_id": 1296, "datatype": Real, "mutable": True},
    },
}

JCIAnalogOutputObject = {
    "name": "JCIAnalogOutputObject",
    "vendor_id": 5,
    "objectType": "analogOutput",
    "bacpypes_type": AnalogOutputObject,
    "properties": {
        "Offline": {"obj_id": 913, "datatype": Boolean, "mutable": False},
        "SABusAddr": {"obj_id": 3645, "datatype": Unsigned, "mutable": False},
        "InputRangeLow": {"obj_id": 1293, "datatype": Real, "mutable": True},
        "InputRangeHigh": {"obj_id": 1294, "datatype": Real, "mutable": True},
        "OutputRangeLow": {"obj_id": 1295, "datatype": Real, "mutable": True},
        "OutputRangeHigh": {"obj_id": 1296, "datatype": Real, "mutable": True},
        "polarity": {"obj_id": "polarity", "datatype": Enumerated, "mutable": True},
        "stroketime": {"obj_id": 3478, "datatype": Real, "mutable": True},
    },
}


def tec_short_point_list(unit_type="2-pipe"):
    """
    unit_type can be :
        - 4-pipe
        - 2-pipe
        - VAV
    """
    _lst = [
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
        # ("analogValue", 29502),
        # ("analogValue", 29503),
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
        ("multiStateValue", 6),
        ("trendLog", 101010),
    ]
    if unit_type == "4-pipe":
        _lst.append(("analogOutput", 86914))
        _lst.append(("analogOutput", 86915))

    return _lst
