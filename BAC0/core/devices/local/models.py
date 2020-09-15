from bacpypes.object import (
    AnalogValueObject,
    CharacterStringValueObject,
    AnalogInputObject,
    AnalogOutputObject,
    BinaryInputObject,
    BinaryOutputObject,
    BinaryValueObject,
    DateValueObject,
    DateTimeValueObject,
    MultiStateInputObject,
    MultiStateOutputObject,
    MultiStateValueObject,
)
from bacpypes.basetypes import (
    EngineeringUnits,
    BinaryPV,
    Polarity,
    Boolean,
    EventState,
    Date,
    DateTime,
    Unsigned,
)
from bacpypes.constructeddata import ArrayOf
from bacpypes.primitivedata import CharacterString, Real
from .object import ObjectFactory

"""
Those models are opiniated versions of BACnet objects.
They are meant to supply an easy mechanism to build BACnet objects
that will be served by the local device of BAC0.

You can indeed use this "method" and modify it to fill your needs.
"""


def _create(definition, **kwargs):
    _definition = {
        "name": None,
        "objectType": None,
        "instance": None,
        "properties": {},
        "description": None,
        "presentValue": None,
        "is_commandable": False,
        "relinquish_default": None,
    }
    _definition.update(definition)
    for k, v in kwargs.items():
        if k == "properties":
            for _k, _v in v.items():
                _definition[k][_k] = _v
        _definition[k] = v
    return ObjectFactory.from_dict(_definition)


def make_state_text(list_of_string):
    _arr = ArrayOf(CharacterString)
    _lst = [CharacterString(each) for each in list_of_string]
    return _arr(_lst)


def set_default_if_not_provided(prop, default_prop, **kwargs):
    try:
        _prop = kwargs[prop]
    except KeyError:
        _prop = default_prop
    return _prop


def analog(**kwargs):
    definition = {
        "instance": 0,
        "description": "No description",
        "properties": {
            "units": "percent",
            "eventState": EventState(),
            "covIncrement": 0.15,
        },
        "presentValue": 0,
        "is_commandable": False,
        "relinquish_default": 0,
    }
    return _create(definition, **kwargs)


def analog_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "AI", **kwargs)
    kwargs["objectType"] = AnalogInputObject
    kwargs["instance"] = 0
    # kwargs['is_commandable'] = True # Futur

    return analog(**kwargs)


def analog_output(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "AO", **kwargs)
    kwargs["objectType"] = AnalogOutputObject
    kwargs["instance"] = 0
    kwargs["is_commandable"] = True

    return analog(**kwargs)


def analog_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "AV", **kwargs)
    kwargs["objectType"] = AnalogValueObject
    kwargs["instance"] = 0
    kwargs["is_commandable"] = True
    return analog(**kwargs)


def binary(**kwargs):
    definition = {
        "instance": 0,
        "description": "No description",
        "properties": {"outOfService": Boolean(False), "eventState": EventState()},
        "presentValue": "inactive",
        "is_commandable": False,
        "relinquish_default": "inactive",
    }
    return _create(definition, **kwargs)


def binary_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "BI", **kwargs)
    kwargs["objectType"] = BinaryInputObject
    try:
        kwargs["properties"].update({"polarity": Polarity()})
    except KeyError:
        kwargs["properties"] = {"polarity": Polarity()}
    # kwargs['is_commandable'] = True # Futur

    return binary(**kwargs)


def binary_output(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "BO", **kwargs)
    kwargs["objectType"] = BinaryOutputObject
    kwargs["is_commandable"] = True
    try:
        kwargs["properties"].update({"polarity": Polarity()})
    except KeyError:
        kwargs["properties"] = {"polarity": Polarity()}
    return binary(**kwargs)


def binary_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "BV", **kwargs)
    kwargs["objectType"] = BinaryValueObject
    kwargs["is_commandable"] = True

    return binary(**kwargs)


def multistate(**kwargs):
    default_states = make_state_text(["Off", "On"])
    definition = {
        "instance": 0,
        "properties": {
            "eventState": EventState(),
            "stateText": default_states,
            # "numberOfStates": Unsigned(2),
        },
        "description": "No description",
        "presentValue": Unsigned(1),
        "is_commandable": False,
        "relinquish_default": Unsigned(1),
    }
    return _create(definition, **kwargs)


def multistate_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "MSI", **kwargs)
    kwargs["objectType"] = MultiStateInputObject
    kwargs["is_commandable"] = True
    kwargs["relinquish_default"] = Unsigned(1)

    return multistate(**kwargs)


def multistate_output(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "MSO", **kwargs)
    kwargs["objectType"] = MultiStateOutputObject
    kwargs["is_commandable"] = True
    kwargs["relinquish_default"] = Unsigned(1)

    return multistate(**kwargs)


def multistate_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "MSV", **kwargs)
    kwargs["objectType"] = MultiStateValueObject
    kwargs["is_commandable"] = True
    kwargs["relinquish_default"] = Unsigned(1)

    return multistate(**kwargs)


def temperature_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "TEMP_INPUT", **kwargs)
    kwargs["properties"] = {"units": "degreesCelsius"}
    return analog_input(**kwargs)


def temperature_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "TEMP_VALUE", **kwargs)
    kwargs["properties"] = {"units": "degreesCelsius"}
    return analog_value(**kwargs)


def humidity_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "HUM_INPUT", **kwargs)
    kwargs["properties"] = {"units": "percentRelativeHumidity"}
    return analog_input(**kwargs)


def humidity_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "HUM_VALUE", **kwargs)
    kwargs["properties"] = {"units": "percentRelativeHumidity"}
    return analog_value(**kwargs)


def character_string(**kwargs):
    definition = {
        "name": "CS_VALUE",
        "objectType": CharacterStringValueObject,
        "instance": 0,
        "description": "No description",
        "presentValue": "",
        "properties": {},
        "is_commandable": False,
        "relinquish_default": "inactive",
    }
    return _create(definition, **kwargs)


def date_value(**kwargs):
    definition = {
        "name": "DATE_VALUE",
        "objectType": DateValueObject,
        "instance": 0,
        "description": "No description",
        "presentValue": Date(),
        "properties": {},
        "is_commandable": False,
        "relinquish_default": "inactive",
    }
    return _create(definition, **kwargs)


def datetime_value(**kwargs):
    definition = {
        "name": "DATETIME_VALUE",
        "objectType": DateTimeValueObject,
        "instance": 0,
        "description": "No description",
        "presentValue": DateTime(),
        "properties": {},
        "is_commandable": False,
        "relinquish_default": "inactive",
    }
    return _create(definition, **kwargs)
