"""
Custom Objects and Properties
"""

from bacpypes3.basetypes import PropertyIdentifier
from bacpypes3.debugging import ModuleLogger
from bacpypes3.local.analog import AnalogInputObject as _AnalogInputObject
from bacpypes3.local.analog import AnalogOutputObject as _AnalogOutputObject
from bacpypes3.local.analog import AnalogValueObject as _AnalogValueObject
from bacpypes3.local.device import DeviceObject as _DeviceObject
from bacpypes3.local.networkport import NetworkPortObject as _NetworkPortObject
from bacpypes3.vendor import VendorInfo
from bacpypes3.primitivedata import Boolean  # Signed,
from bacpypes3.primitivedata import (
    Atomic,
    CharacterString,
    Date,
    Enumerated,
    ObjectType,
    Real,
    Time,
    Unsigned,
)

# some debugging
_debug = 0
_log = ModuleLogger(globals())


# this vendor identifier reference is used when registering custom classes
_vendor_id = 5
_vendor_name = "Johnson Controls"


class ProprietaryObjectType(ObjectType):
    """
    This is a list of the object type enumerations for proprietary object types,
    see Clause 23.4.1.
    """

    pass


class ProprietaryPropertyIdentifier(PropertyIdentifier):
    """
    This is a list of the property identifiers that are used in custom object
    types or are used in custom properties of standard types.
    """

    # DEVICE OBJECT
    ALARM_STATE = 1006
    ARCHIVE_DATE = 849
    ARCHIVE_STATUS = 1187
    ARCHIVE_TIME = 850
    CPU_USAGE = 2583
    ENABLED = 673
    EXECUTION_PRIORITY = 2197
    EXTENDED_PROTO_VERSION = 2291
    FLASH_USAGE = 2584
    ITEM_REFERENCE = 32527
    JCI_STATUS = 847
    MEMORY_USAGE = 2581
    OBJECT_CATEGORY = 908
    OBJECT_MEMORY_USAGE = 2582
    STATUS = 512
    BACNET_BROADCAST_RECEIVE_RATE = 745
    DEFAULT_BASE_UNITS = 2206
    ESTIMATED_FLASH_AVAILABLE = 2395
    LAST_IDLE_SAMPLE = 30082
    MAX_MESSAGE_BUFFER = 848
    USER_NAME = 2390
    PCODE = 1320
    SAB_DEVICE_STATUS_LIST_CHANGED = 4514
    EVENTS_LOST = 1479
    ACCEPT_BACNET_TIME_SYNC = 4970
    SUPERVISORY_DEVICE_ONLINE = 3653
    # "STANDARD_TIME_OFFSET ": {"obj_id": 1017, "datatype": Signed, "mutable": False}, # -900-900
    # "DAYLIGHT_SAVING_TIME_OFFSET ": {"obj_id": 1093, "datatype": Signed, "mutable": False}, # -900-900
    # "STANDARD_TIME_START ": {"obj_id": 988, "datatype": Complex, "mutable": True},
    # "DAYLIGHT_SAVING_TIME_START ": {"obj_id": 1040, "datatype": Complex, "mutable": True},
    # "LAST_BACNET_TIME_SYNC_RECEIVED ": {"obj_id": 5728, "datatype": Complex, "mutable": False},
    # "ASSET_VERSIONS": {"obj_id": 4960, "datatype": Complex, "mutable": False},

    SUPERVISORY_OFFLINE_TIMEOUT = 6002
    NEXT_AVAILABLE_OID = 787
    HAS_UNBOUND_REFERENCES = 767
    SURROGATE_CACHE_CNT = 571
    SURROGATE_CACHE_MAX = 639
    LOAD_BALANCER_LEVEL = 4722
    TIMER_DB_SIZE = 733
    TIMER_USED = 734
    TIMER_PEAK = 735
    TIMER_MESSAGES_ABORTED = 4959
    BACNET_OID_ALLOCATED = 1291
    BACNET_OID_USED = 1292
    SIGN_PRI_DB_SIZE = 730
    SIGN_PRI_USED = 731
    SIGN_PRI_PEAK = 732
    BACNET_ENCODE_TYPE = 32578
    ROUTING_MODE = 4307
    BACNET_INTEGRATED_OBJECTS = 4302
    BACNET_COMPATIBLE = 4581
    SEND_I_AM_RATE = 579
    DEFAULT_TIME_ZONE = 32583
    TIME_ZONE = 1403
    LOCAL_TIME_ZONE = 1404
    FC_MULTICAST_RESPONDER = 3390
    FC_WAIT_BEFORE_POLLING = 3391
    SUPERVISOR_MAC_ADDRESS = 3652
    LIBRARY_PART_ID = 3295
    APPLICATION_CLASS_SET_VERSION = 4128
    DEVICE_MODEL_CLASS_SET_VERSION = 4129
    COV_MIN_SEND_TIME = 3929
    COV_TRANSMITS_PER_MINUTE = 651
    CONTROL_SEQUENCE_IN_TEST = 3651
    END_OF_LINE = 603
    DEVICE_ADDRESS = 876
    FC_BUS_COMMUNICATION_MOD = 4400
    SYSTEM_TYPE = 3900
    SYSTEM_CONFIGURATION = 3899
    SABusPerformance = 12157
    SABusTokenLoopTime = 12158
    SABusCOVRcvPerMinute = 12159
    SABusCOVWritesPerMinute = 12160
    # AV, AI, AO
    FLOW_SP_EEPROM = 3113
    Offset = 956
    Offline = 913
    SABusAddr = 3645
    PeerToPeer = 748
    P2P_ErrorStatus = 746
    InputRangeLow = 1293
    InputRangeHigh = 1294
    OutputRangeLow = 1295
    OutputRangeHigh = 1296
    MIN_OUT_VALUE = 652
    MAX_OUT_VALUE = 653
    # polarity = polarity
    stroketime = 3478


class DeviceObject(_DeviceObject):
    """
    When running as an instance of this custom device, the DeviceObject is
    an extension of the one defined in bacpypes3.local.device (in this case
    doesn't add any proprietary properties).
    """

    ALARM_STATE: Enumerated
    ARCHIVE_DATE: Date
    ARCHIVE_STATUS: Unsigned
    ARCHIVE_TIME: Time
    CPU_USAGE: Real
    ENABLED: Boolean
    EXECUTION_PRIORITY: Enumerated
    EXTENDED_PROTO_VERSION: Unsigned
    FLASH_USAGE: Real
    ITEM_REFERENCE: CharacterString
    JCI_STATUS: Enumerated
    MEMORY_USAGE: Real
    OBJECT_CATEGORY: Enumerated
    OBJECT_MEMORY_USAGE: Real
    STATUS: Enumerated
    BACNET_BROADCAST_RECEIVE_RATE: Unsigned
    DEFAULT_BASE_UNITS: Enumerated
    ESTIMATED_FLASH_AVAILABLE: Real
    LAST_IDLE_SAMPLE: Real
    MAX_MESSAGE_BUFFER: Unsigned
    USER_NAME: CharacterString
    PCODE: CharacterString
    SAB_DEVICE_STATUS_LIST_CHANGED: Unsigned
    EVENTS_LOST: Unsigned
    ACCEPT_BACNET_TIME_SYNC: Boolean
    SUPERVISORY_DEVICE_ONLINE: Boolean
    # "STANDARD_TIME_OFFSET ": {"obj_id": 1017, "datatype": Signed, "mutable": False}, # -900-900
    # "DAYLIGHT_SAVING_TIME_OFFSET ": {"obj_id": 1093, "datatype": Signed, "mutable": False}, # -900-900
    # "STANDARD_TIME_START ": {"obj_id": 988, "datatype": Complex, "mutable": True},
    # "DAYLIGHT_SAVING_TIME_START ": {"obj_id": 1040, "datatype": Complex, "mutable": True},
    # "LAST_BACNET_TIME_SYNC_RECEIVED ": {"obj_id": 5728, "datatype": Complex, "mutable": False},
    # "ASSET_VERSIONS": {"obj_id": 4960, "datatype": Complex, "mutable": False},

    SUPERVISORY_OFFLINE_TIMEOUT: Unsigned
    NEXT_AVAILABLE_OID: Unsigned
    HAS_UNBOUND_REFERENCES: Boolean
    SURROGATE_CACHE_CNT: Unsigned
    SURROGATE_CACHE_MAX: Unsigned
    LOAD_BALANCER_LEVEL: Enumerated
    TIMER_DB_SIZE: Unsigned
    TIMER_USED: Unsigned
    TIMER_PEAK: Unsigned
    TIMER_MESSAGES_ABORTED: Unsigned
    BACNET_OID_ALLOCATED: Unsigned
    BACNET_OID_USED: Unsigned
    SIGN_PRI_DB_SIZE: Unsigned
    SIGN_PRI_USED: Unsigned
    SIGN_PRI_PEAK: Unsigned
    BACNET_ENCODE_TYPE: Unsigned
    ROUTING_MODE: Enumerated
    BACNET_INTEGRATED_OBJECTS: Enumerated
    BACNET_COMPATIBLE: Unsigned
    SEND_I_AM_RATE: Unsigned
    DEFAULT_TIME_ZONE: Enumerated
    TIME_ZONE: Enumerated
    LOCAL_TIME_ZONE: Enumerated
    FC_MULTICAST_RESPONDER: Unsigned
    FC_WAIT_BEFORE_POLLING: Unsigned
    SUPERVISOR_MAC_ADDRESS: Unsigned
    LIBRARY_PART_ID: CharacterString
    APPLICATION_CLASS_SET_VERSION: Unsigned
    DEVICE_MODEL_CLASS_SET_VERSION: Unsigned
    COV_MIN_SEND_TIME: Unsigned
    COV_TRANSMITS_PER_MINUTE: Unsigned
    CONTROL_SEQUENCE_IN_TEST: Unsigned
    END_OF_LINE: Boolean
    DEVICE_ADDRESS: Unsigned
    FC_BUS_COMMUNICATION_MOD: Enumerated
    SYSTEM_TYPE: Unsigned
    SYSTEM_CONFIGURATION: Unsigned
    SABusPerformance: Unsigned
    SABusTokenLoopTime: Unsigned
    SABusCOVRcvPerMinute: Unsigned
    SABusCOVWritesPerMinute: Unsigned


class NetworkPortObject(_NetworkPortObject):
    """
    When running as an instance of this custom device, the NetworkPortObject is
    an extension of the one defined in bacpypes3.local.networkport (in this
    case doesn't add any proprietary properties).
    """

    pass


class AnalogInputObject(_AnalogInputObject):
    Offset: Real
    Offline: Boolean
    SABusAddr: Unsigned
    InputRangeLow: Real
    InputRangeHigh: Real
    OutputRangeLow: Real
    OutputRangeHigh: Real


class AnalogValueObject(_AnalogValueObject):
    FLOW_SP_EEPROM: Real
    Offset: Real
    Offline: Boolean
    SABusAddr: Unsigned
    PeerToPeer: Atomic
    P2P_ErrorStatus: Enumerated


class AnalogOutputObject(_AnalogOutputObject):
    Offline: Boolean
    SABusAddr: Unsigned
    MIN_OUT_VALUE: Real
    MAX_OUT_VALUE: Real
    # polarity = polarity
    stroketime: Real
