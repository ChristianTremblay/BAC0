"""
#   PRIVA BV 105
#   Proprietary Objects and their attributes
#   reference needed
#
# Register Priva BV Proprietary Objects and properties
"""

# from . import OptionalUnsigned
from bacpypes3.basetypes import PropertyIdentifier
from bacpypes3.debugging import ModuleLogger
from bacpypes3.object import AnalogInputObject as _AnalogInputObject
from bacpypes3.object import AnalogOutputObject as _AnalogOutputObject
from bacpypes3.object import AnalogValueObject as _AnalogValueObject
from bacpypes3.object import DeviceObject as _DeviceObject
from bacpypes3.object import NetworkPortObject as _NetworkPortObject
from bacpypes3.primitivedata import (
    CharacterString,
    ObjectType,
)
from bacpypes3.vendor import VendorInfo, get_vendor_info

# some debugging
_debug = 0
_log = ModuleLogger(globals())


# this vendor identifier reference is used when registering custom classes
_vendor_id = 105
_vendor_name = "PRIVA BV"


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

    custom_description = 10502


try:
    _priva = VendorInfo(
        _vendor_id, ProprietaryObjectType, ProprietaryPropertyIdentifier
    )
except RuntimeError:
    pass  # we are re-running the script... forgive us or maybe we already read a priva bv device
    _priva = get_vendor_info(_vendor_id)


class PrivaBVDeviceObject(_DeviceObject):
    """
    When running as an instance of this custom device, the DeviceObject is
    an extension of the one defined in bacpypes3.local.device
    """

    custom_description: CharacterString


class NetworkPortObject(_NetworkPortObject):
    """
    When running as an instance of this custom device, the NetworkPortObject is
    an extension of the one defined in bacpypes3.local.networkport (in this
    case doesn't add any proprietary properties).
    """

    pass


class PrivaBVAnalogInputObject(_AnalogInputObject):
    custom_description: CharacterString


class PrivaBVAnalogValueObject(_AnalogValueObject):
    custom_description: CharacterString


class PrivaBVAnalogOutputObject(_AnalogOutputObject):
    custom_description: CharacterString
