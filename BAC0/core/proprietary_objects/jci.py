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

