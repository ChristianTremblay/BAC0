#!/usr/bin/env python

"""
Johnson Controls Proprietary Objects for FX/FEC Line
"""
from bacpypes.primitivedata import Boolean
from bacpypes.object import BinaryValueObject, Property, register_object_type

#
#   Vendor TECSupOnline Value Object Type
#

class TECSupOnline(BinaryValueObject):
    """
    This class will provide to a BAC0 device referring to a Johnson Controls TEC3000
    thermostats the Supervisor Online variable. This will allow testing of remote
    occupancy schedules.
    """
    objectType = 'device'
    vendor_id = 5

    properties = [
        Property(3653, Boolean, mutable=True),
        ]

    def __init__(self, **kwargs):
        BinaryValueObject.__init__(self, **kwargs)

def register(cls, vendor_id=5):
    register_object_type(cls, vendor_id=vendor_id)

def tec_short_point_list():
    lst = [('binaryInput', 30827),
         ('binaryInput', 30828),
         ('binaryOutput', 86908),
         ('binaryOutput', 86909),
         ('binaryOutput', 86910),
         ('binaryOutput', 86911),
         ('binaryOutput', 86912),
         ('binaryOutput', 87101),
         ('binaryOutput', 87102),
         ('multiStateValue', 29501),
         ('multiStateValue', 29500),
         ('multiStateValue', 29509),
         ('multiStateValue', 29517),
         ('multiStateValue', 29518),
         ('multiStateValue', 29519),
         ('multiStateValue', 29520),
         ('multiStateValue', 29524),
         ('multiStateValue', 29525),
         ('multiStateValue', 29527),
         ('multiStateValue', 29712),
         ('multiStateValue', 29700),
         ('multiStateValue', 29709),
         ('multiStateValue', 29708),
         ('analogValue', 29505),
         ('analogValue', 29502),
         ('analogValue', 29503),
         ('analogValue', 29504),
         ('analogValue', 29506),
         ('analogValue', 29507),
         ('analogValue', 29508),
         ('analogValue', 29515),
         ('analogValue', 29522),
         ('analogValue', 29529),
         ('analogValue', 29530),
         ('analogValue', 29532),
         ('analogValue', 29701),
         ('analogValue', 29703),
         ('analogValue', 29705),
         ('analogValue', 29706),
         ('analogValue', 29707),
         ('analogValue', 29714),
         ('analogValue', 29717),
         ('analogValue', 29725),
         ('analogValue', 29726),
         ('analogValue', 29727),
         ('analogOutput', 86905),
         ('analogOutput', 86914),
         ('analogOutput', 86915),
         ('multiStateValue', 6)]
    return lst