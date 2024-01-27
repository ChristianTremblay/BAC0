from bacpypes3.local.object import Object as _Object

from bacpypes3.object import CharacterStringValueObject as _CharacterStringValueObject
from bacpypes3.object import DateTimeValueObject as _DateTimeValueObject
from bacpypes3.object import DateValueObject as _DateValueObject
from bacpypes3.object import TrendLogObject as _TrendLogObject

"""
Those models are opiniated versions of BACnet objects.
They are meant to supply an easy mechanism to build BACnet objects
that will be served by the local device of BAC0.

You can indeed use this "method" and modify it to fill your needs.
"""


# First create our local classes which are missing from bacpypes3


class CharacterStringValueObject(_Object, _CharacterStringValueObject):
    pass


class DateValueObject(_Object, _DateValueObject):
    pass


class DateTimeValueObject(_Object, _DateTimeValueObject):
    pass


class TrendLogObject(_Object, _TrendLogObject):
    pass
