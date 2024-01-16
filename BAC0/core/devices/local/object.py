from bacpypes3.constructeddata import ArrayOf, ListOf
from bacpypes3.object import (
    AnalogInputObject as _AnalogInputObject,
    AnalogOutputObject as _AnalogOutputObject,
    AnalogValueObject as _AnalogValueObject,
    BinaryInputObject as _BinaryInputObject,
    BinaryOutputObject as _BinaryOutputObject,
    BinaryValueObject as _BinaryValueObject,
    CharacterStringValueObject as _CharacterStringValueObject,
    DateTimeValueObject as _DateTimeValueObject,
    DateValueObject as _DateValueObject,
    MultiStateInputObject as _MultiStateInputObject,
    MultiStateOutputObject as _MultiStateOutputObject,
    MultiStateValueObject as _MultiStateValueObject,
    TrendLogObject as _TrendLogObject,
)


from bacpypes3.local.object import Object as _Object
from bacpypes3.local.cov import COVIncrementCriteria

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