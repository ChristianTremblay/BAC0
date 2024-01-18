from bacpypes3.constructeddata import ArrayOf, ListOf
from bacpypes3.local.cov import COVIncrementCriteria
from bacpypes3.local.object import Object as _Object
from bacpypes3.object import AnalogInputObject as _AnalogInputObject
from bacpypes3.object import AnalogOutputObject as _AnalogOutputObject
from bacpypes3.object import AnalogValueObject as _AnalogValueObject
from bacpypes3.object import BinaryInputObject as _BinaryInputObject
from bacpypes3.object import BinaryOutputObject as _BinaryOutputObject
from bacpypes3.object import BinaryValueObject as _BinaryValueObject
from bacpypes3.object import CharacterStringValueObject as _CharacterStringValueObject
from bacpypes3.object import DateTimeValueObject as _DateTimeValueObject
from bacpypes3.object import DateValueObject as _DateValueObject
from bacpypes3.object import MultiStateInputObject as _MultiStateInputObject
from bacpypes3.object import MultiStateOutputObject as _MultiStateOutputObject
from bacpypes3.object import MultiStateValueObject as _MultiStateValueObject
from bacpypes3.object import TrendLogObject as _TrendLogObject

"""
Those models are opiniated versions of BACnet objects.
They are meant to supply an easy mechanism to build BACnet objects
that will be served by the local device of BAC0.

You can indeed use this "method" and modify it to fill your needs.
"""


# First create our local classes which are missing from bacpypes3
class MultiStateValueObject(_Object, _MultiStateValueObject):
    _cov_criteria = COVIncrementCriteria


class MultiStateInputObject(_Object, _MultiStateInputObject):
    _cov_criteria = COVIncrementCriteria


class MultiStateOutputObject(_Object, _MultiStateOutputObject):
    _cov_criteria = COVIncrementCriteria


class CharacterStringValueObject(_Object, _CharacterStringValueObject):
    pass


class DateValueObject(_Object, _DateValueObject):
    pass


class DateTimeValueObject(_Object, _DateTimeValueObject):
    pass


class TrendLogObject(_Object, _TrendLogObject):
    pass
