#!/usr/bin/env python

"""
This sample application shows how to extend one of the basic objects, an Analog
Value Object in this case, to provide a present value. This type of code is used
when the application is providing a BACnet interface to a collection of data.
It assumes that almost all of the default behaviour of a BACpypes application is
sufficient.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.primitivedata import Boolean
from bacpypes.object import BinaryValueObject, Property, register_object_type


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals


#
#   Vendor TECSupOnline Value Object Type
#

@bacpypes_debugging
class TECSupOnline(BinaryValueObject):
    objectType = 'device'
    vendor_id = 5

    properties = [
        Property(3653, Boolean, mutable=True),
        ]

    def __init__(self, **kwargs):
        if _debug: TECSupOnline._debug("__init__ %r", kwargs)
        BinaryValueObject.__init__(self, **kwargs)

def register(cls, vendor_id=5):
    register_object_type(cls, vendor_id=vendor_id)

