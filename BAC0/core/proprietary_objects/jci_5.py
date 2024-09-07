"""
#   JCI 5
#   Proprietary Objects and their attributes
#   https://cgproducts.johnsoncontrols.com/MET_PDF/12013102.pdf
#
# Register Johnson Controls Proprietary Objects and properties
"""

from bacpypes3.vendor import VendorInfo, get_vendor_info
from bacpypes3.basetypes import PropertyIdentifier
from bacpypes3.debugging import ModuleLogger
from bacpypes3.object import AnalogInputObject as _AnalogInputObject
from bacpypes3.object import AnalogOutputObject as _AnalogOutputObject
from bacpypes3.object import AnalogValueObject as _AnalogValueObject
from bacpypes3.object import DeviceObject as _DeviceObject
from bacpypes3.object import NetworkPortObject as _NetworkPortObject
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

# from . import OptionalUnsigned
from bacpypes3.basetypes import OptionalUnsigned

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
    alarm_state = 1006
    archive_date = 849
    archive_status = 1187
    archive_time = 850
    cpu_usage = 2583
    enabled = 673
    execution_priority = 2197
    extended_proto_version = 2291
    flash_usage = 2584
    item_reference = 32527
    jci_status = 847
    memory_usage = 2581
    object_category = 908
    object_memory_usage = 2582
    status = 512
    bacnet_broadcast_receive_rate = 745
    default_base_units = 2206
    estimated_flash_available = 2395
    last_idle_sample = 30082
    max_message_buffer = 848
    user_name = 2390
    pcode = 1320
    sab_device_status_list_changed = 4514
    events_lost = 1479
    accept_bacnet_time_sync = 4970
    supervisory_device_online = 3653
    # "STANDARD_TIME_OFFSET ": {"obj_id": 1017, "datatype": Signed, "mutable": False}, # -900-900
    # "DAYLIGHT_SAVING_TIME_OFFSET ": {"obj_id": 1093, "datatype": Signed, "mutable": False}, # -900-900
    # "STANDARD_TIME_START ": {"obj_id": 988, "datatype": Complex, "mutable": True},
    # "DAYLIGHT_SAVING_TIME_START ": {"obj_id": 1040, "datatype": Complex, "mutable": True},
    # "LAST_BACNET_TIME_SYNC_RECEIVED ": {"obj_id": 5728, "datatype": Complex, "mutable": False},
    # "ASSET_VERSIONS": {"obj_id": 4960, "datatype": Complex, "mutable": False},
    supervisory_offline_timeout = 6002
    next_available_oid = 787
    has_unbound_references = 767
    surrogate_cache_cnt = 571
    surrogate_cache_max = 639
    load_balancer_level = 4722
    timer_db_size = 733
    timer_used = 734
    timer_peak = 735
    timer_messages_aborted = 4959
    bacnet_oid_allocated = 1291
    bacnet_oid_used = 1292
    sign_pri_db_size = 730
    sign_pri_used = 731
    sign_pri_peak = 732
    bacnet_encode_type = 32578
    routing_mode = 4307
    bacnet_integrated_objects = 4302
    bacnet_compatible = 4581
    send_i_am_rate = 579
    default_time_zone = 32583
    time_zone = 1403
    local_time_zone = 1404
    fc_multicast_responder = 3390
    fc_wait_before_polling = 3391
    supervisor_mac_address = 3652
    library_part_id = 3295
    application_class_set_version = 4128
    device_model_class_set_version = 4129
    cov_min_send_time = 3929
    cov_transmits_per_minute = 651
    control_sequence_in_test = 3651
    end_of_line = 603
    device_address = 876
    fc_bus_communication_mod = 4400
    system_type = 3900
    system_configuration = 3899
    sabusperformance = 12157
    sabustokenlooptime = 12158
    sabuscovrcvperminute = 12159
    sabuscovwritesperminute = 12160
    # AV, AI, AO
    flow_sp_eeprom = 3113
    offset = 956
    offline = 913
    sabusaddr = 3645
    peertopeer = 748
    p2p_errorstatus = 746
    inputrangelow = 1293
    inputrangehigh = 1294
    outputrangelow = 1295
    outputrangehigh = 1296
    min_out_value = 652
    max_out_value = 653
    # polarity = polarity
    stroketime = 3478


try:
    _jci = VendorInfo(_vendor_id, ProprietaryObjectType, ProprietaryPropertyIdentifier)
except RuntimeError:
    pass  # we are re-running the script... forgive us or maybe we already read a jci device
    _jci = get_vendor_info(_vendor_id)


class JCIDeviceObject(_DeviceObject):
    """
    When running as an instance of this custom device, the DeviceObject is
    an extension of the one defined in bacpypes3.local.device
    """

    alarm_state: Enumerated
    archive_date: Date
    archive_status: Unsigned
    archive_time: Time
    cpu_usage: Real
    enabled: Boolean
    execution_priority: Enumerated
    extended_proto_version: Unsigned
    flash_usage: Real
    item_reference: CharacterString
    jci_status: Enumerated
    memory_usage: Real
    object_category: Enumerated
    object_memory_usage: Real
    status: Enumerated
    bacnet_broadcast_receive_rate: Unsigned
    default_base_units: Enumerated
    estimated_flash_available: Real
    last_idle_sample: Real
    max_message_buffer: Unsigned
    user_name: CharacterString
    pcode: CharacterString
    sab_device_status_list_changed: OptionalUnsigned
    events_lost: Unsigned
    accept_bacnet_time_sync: Boolean
    supervisory_device_online: Boolean
    supervisory_offline_timeout: Unsigned
    next_available_oid: Unsigned
    has_unbound_references: Boolean
    surrogate_cache_cnt: Unsigned
    surrogate_cache_max: Unsigned
    load_balancer_level: Enumerated
    timer_db_size: Unsigned
    timer_used: Unsigned
    timer_peak: Unsigned
    timer_messages_aborted: Unsigned
    bacnet_oid_allocated: Unsigned
    bacnet_oid_used: Unsigned
    sign_pri_db_size: Unsigned
    sign_pri_used: Unsigned
    sign_pri_peak: Unsigned
    bacnet_encode_type: Unsigned
    routing_mode: Enumerated
    bacnet_integrated_objects: Enumerated
    bacnet_compatible: Unsigned
    send_i_am_rate: Unsigned
    default_time_zone: Enumerated
    time_zone: Enumerated
    local_time_zone: Enumerated
    fc_multicast_responder: Unsigned
    fc_wait_before_polling: Unsigned
    supervisor_mac_address: Unsigned
    library_part_id: CharacterString
    application_class_set_version: Unsigned
    device_model_class_set_version: Unsigned
    cov_min_send_time: Unsigned
    cov_transmits_per_minute: Unsigned
    control_sequence_in_test: Unsigned
    end_of_line: Boolean
    device_address: Unsigned
    fc_bus_communication_mod: Enumerated
    system_type: Unsigned
    system_configuration: Unsigned
    sabusperformance: Unsigned
    sabustokenlooptime: Unsigned
    sabuscovrcvperminute: Unsigned
    sabuscovwritesperminute: Unsigned


class NetworkPortObject(_NetworkPortObject):
    """
    When running as an instance of this custom device, the NetworkPortObject is
    an extension of the one defined in bacpypes3.local.networkport (in this
    case doesn't add any proprietary properties).
    """

    pass


class JCIAnalogInputObject(_AnalogInputObject):
    offset: Real
    offline: Boolean
    sabusaddr: OptionalUnsigned
    inputrangelow: Real
    inputrangehigh: Real
    outputrangelow: Real
    outputrangehigh: Real


class JCIAnalogValueObject(_AnalogValueObject):
    flow_sp_eeprom: Real
    offset: Real
    offline: Boolean
    sabusaddr: OptionalUnsigned
    peertopeer: Atomic
    p2p_errorstatus: Enumerated


class JCIAnalogOutputObject(_AnalogOutputObject):
    offline: Boolean
    sabusaddr: OptionalUnsigned
    min_out_value: Real
    max_out_value: Real
    # polarity = polarity
    stroketime: Real
