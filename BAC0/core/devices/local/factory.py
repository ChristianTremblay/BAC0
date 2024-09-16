import typing as t
from collections import namedtuple

from bacpypes3.app import Application
from bacpypes3.basetypes import Date, DateTime, LogRecord, Polarity, Time, Unsigned
from bacpypes3.constructeddata import ArrayOf, ListOf
from bacpypes3.local.analog import (
    AnalogInputObject,
    AnalogOutputObject,
    AnalogValueObject,
)
from bacpypes3.local.binary import (
    BinaryInputObject,
    BinaryOutputObject,
    BinaryValueObject,
)
from bacpypes3.local.cov import COVIncrementCriteria
from bacpypes3.local.multistate import (
    MultiStateInputObject,
    MultiStateOutputObject,
    MultiStateValueObject,
)
from bacpypes3.primitivedata import CharacterString
from colorama import Fore

from BAC0.core.devices.local.trendLogs import LocalTrendLog

from ....scripts.Base import Base
from ...utils.notes import note_and_log
from .decorator import bacnet_properties, create, make_commandable, make_outOfService
from .object import (
    CharacterStringValueObject,
    DateTimeValueObject,
    DateValueObject,
    TrendLogObject,
)


@note_and_log
class ObjectFactory(object):
    """
    This is an exploration of a method to create local objects in BAC0 instance.

    First you need to know what bacpypes class of object you want to create ex. AnalogValueObject
    This class must be imported from bacpypes ex. from bacpypes.object import AnalogValueObject

    You must also define supplemental properties for the object in a dict.
    ex. :
        properties = {"outOfService" : False,
                "relinquishDefault" : 0,
                "units": "degreesCelsius",
                "highLimit": 98}

    Then you can use the factory to create your object
    ex. :

        av0 = ObjectFactory(AnalogValueObject, 1, 'av0', )

    """

    instances: t.Dict[str, t.Set] = {}

    definition = namedtuple(  # type: ignore[name-match]
        "Definition",
        "name, objectType, instance, properties, description, presentValue, is_commandable, relinquishDefault",
    )

    objects: t.Dict[str, t.Any] = {}
    # In the future... should think about a way to store relinquish default values because on a restart
    # those should be restored.

    def __init__(
        self,
        objectType,
        instance,
        objectName,
        properties=None,
        description="",
        presentValue=None,
        is_commandable=False,
        relinquishDefault=None,
    ):
        _localTrendLogDataType = properties.pop("trendLog_datatype", None)
        self._properties = ObjectFactory.default_properties(
            objectType, properties, is_commandable, relinquishDefault
        )
        # print(f"Obj {objectType} of type {type(objectType)}")
        if objectType is not TrendLogObject:
            pv_datatype = ObjectFactory.get_pv_datatype(objectType)
            self.log(f"pv datatype : {pv_datatype}", level="debug")

            def enforce_datatype(val, datatype):
                if not isinstance(val, datatype):
                    try:
                        val = datatype(val)
                    except TypeError as error:
                        raise TypeError(
                            f"Wrong datatype provided for value {val} using datatype {datatype} with target type of {pv_datatype} | {error}"
                        )
                return val

            if presentValue is not None:
                presentValue = enforce_datatype(presentValue, pv_datatype)
            if relinquishDefault is not None:
                relinquishDefault = enforce_datatype(relinquishDefault, pv_datatype)

        @bacnet_properties(self._properties)
        @make_commandable()
        def _create_commandable(
            objectType, instance, objectName, presentValue, description
        ):
            self._log.info(
                f"Making this object commandable : type:{objectType} id:{instance} name:{objectName} presentValue:{presentValue} description:{description}"
            )
            return create(objectType, instance, objectName, presentValue, description)

        @bacnet_properties(self._properties)
        @make_outOfService()
        def _create_outOfService(
            objectType, instance, objectName, presentValue, description
        ):
            return create(objectType, instance, objectName, presentValue, description)

        @bacnet_properties(self._properties)
        def _create(objectType, instance, objectName, presentValue, description):
            return create(objectType, instance, objectName, presentValue, description)

        objectName, instance = self.validate_name_and_instance(
            objectType, objectName, instance
        )

        if objectType in (AnalogInputObject, BinaryInputObject, MultiStateInputObject):
            self.objects[objectName] = _create_outOfService(
                objectType, instance, objectName, presentValue, description
            )
        elif is_commandable is True:
            self.objects[objectName] = _create_commandable(
                objectType, instance, objectName, presentValue, description
            )
        else:
            self.objects[objectName] = _create(
                objectType, instance, objectName, presentValue, description
            )
        if objectType is TrendLogObject:  # Add special internal object for trendlog
            self.objects[objectName]._local = LocalTrendLog(
                self.objects[objectName], datatype=_localTrendLogDataType
            )  # this will need to be fed by another process.
        else:
            self.objects[objectName]._cov_criteria = COVIncrementCriteria

    def validate_instance(self, objectType, instance):
        _warning = True
        try:
            _set = self.instances[objectType.__name__]
        except KeyError:
            _set = set()

        if not instance:
            instance = 0
            _warning = False

        if instance in _set:
            while instance in _set:
                instance += 1
            if _warning:
                self.log(
                    f"Instance alreaday taken, using {instance} instead",
                    level="warning",
                )

        _set.add(instance)
        self.instances[objectType.__name__] = _set
        return instance

    def validate_name_and_instance(self, objectType, objectName, instance):
        name_must_be_changed = False
        if objectName in self.objects.keys():
            name_must_be_changed = True
        instance = self.validate_instance(objectType, instance)
        if name_must_be_changed:
            objectName = f"{objectName}-{instance}"
            self.log(f"Name already taken, using {objectName} instead", level="warning")

        return (objectName, instance)

    @classmethod
    def from_dict(cls, definition):
        return cls(
            objectType=definition["objectType"],
            instance=definition["instance"],
            objectName=definition["name"],
            properties=definition["properties"],
            description=definition["description"],
            presentValue=definition["presentValue"],
            is_commandable=definition["is_commandable"],
        )

    @staticmethod
    def get_pv_datatype(objectType):
        return objectType.get_property_type("presentValue")

    @staticmethod
    def clear_objects():
        ObjectFactory.objects = {}
        ObjectFactory.instances = {}

    def add_objects_to_application(self, app):
        if isinstance(app, Base):
            app = app.this_application.app
        if not (isinstance(app, Application)):
            raise TypeError("Provide BAC0Application object or BAC0 Base instance")
        for k, v in self.objects.items():
            try:
                app.add_object(v)
                self.log(f"Adding {k} to application.", level="info")
            except RuntimeError:
                self._log.warning(
                    f"There is already an object named {k} in application."
                )

    def __repr__(self):
        return f"{self.objects}"

    @staticmethod
    def default_properties(
        objectType, properties, is_commandable=False, relinquishDefault=None
    ):
        _properties = properties or {}
        if "statusFlags" not in _properties.keys():
            _properties["statusFlags"] = [0, 0, 0, 0]
        if (
            "analog" in objectType.__name__.lower()
            and "units" not in _properties.keys()
        ):
            raise ValueError("Provide Engineering Units in properties")
        return _properties

    @staticmethod
    def relinquish_default_value(objectType, value):
        pv_datatype = ObjectFactory.get_pv_datatype(objectType)
        return pv_datatype(value)

    @staticmethod
    def inspect(bacnet_object):
        """
        A fun little snippet to inspect the properties of a BACnet object.
        """
        objectType = bacnet_object.__name__
        _repr = Fore.YELLOW + "*" * 100
        _repr += "\n| " + Fore.CYAN + f"{objectType}"
        _repr += Fore.YELLOW + "\n|" + "*" * 99
        _repr += "\n"
        _repr += (
            "| " + Fore.WHITE + f"Support COV : {bacnet_object._object_supports_cov}\n"
        )
        _repr += Fore.YELLOW + "|" + "=" * 99
        _repr += "\n\x1b[33m| {:30} \x1b[33m| {:26} \x1b[33m| {:8} \x1b[33m| {:8} \x1b[33m| {:8}".format(
            "IDENTIFIER", "DATACLASS", "OPTIONAL", "MUTABLE", "DEFAULT"
        )
        _repr += "\n|" + "=" * 99
        for prop in bacnet_object.properties:
            i, d, o, m, df = prop.__dict__.values()
            df = Fore.WHITE + df if df else Fore.WHITE + "None"
            o = Fore.GREEN + "Yes" if o else Fore.RED + "No"
            m = Fore.GREEN + "Yes" if m else Fore.RED + "No"
            _repr += (
                "\n"
                + Fore.WHITE
                + "\x1b[33m| \x1b[37m{:30} \x1b[33m| \x1b[37m{:26} \x1b[33m| {:13} \x1b[33m| {:13} \x1b[33m| {:13}".format(
                    i, d.__name__, o, m, df
                )
            )
        return _repr


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
    }
    _definition.update(definition)
    for k, v in kwargs.items():
        if k == "properties":
            for _k, _v in v.items():
                _definition["properties"][_k] = _v  # type: ignore[index]
        else:
            _definition[k] = v

    return ObjectFactory.from_dict(_definition)


def make_state_text(list_of_string: list[str]):
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
    # This is the general definition for an analog object
    # more information are provided in each of sub functions
    if "is_commandable" not in kwargs:
        kwargs["is_commandable"] = False
    definition = {
        "instance": 0,
        "description": "No description",
        "properties": {
            "units": "percent",
            # "eventState": EventState(),
            "covIncrement": 0.15,
        },
        "presentValue": 0,
    }
    return _create(definition, **kwargs)


def analog_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "AI", **kwargs)
    kwargs["objectType"] = AnalogInputObject
    kwargs["instance"] = set_default_if_not_provided("instance", 0, **kwargs)
    return analog(**kwargs)


def analog_output(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "AO", **kwargs)
    kwargs["objectType"] = AnalogOutputObject
    kwargs["instance"] = set_default_if_not_provided("instance", 0, **kwargs)
    return analog(**kwargs)


def analog_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "AV", **kwargs)
    kwargs["objectType"] = AnalogValueObject
    kwargs["instance"] = set_default_if_not_provided("instance", 0, **kwargs)
    return analog(**kwargs)


def binary(**kwargs):
    if "is_commandable" not in kwargs:
        kwargs["is_commandable"] = False
    definition = {
        "instance": 0,
        "description": "No description",
        "properties": {
            # "outOfService": Boolean(False),
            # "eventState": EventState()
        },
        "presentValue": "inactive",
    }
    return _create(definition, **kwargs)


def binary_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "BI", **kwargs)
    kwargs["objectType"] = BinaryInputObject
    try:
        kwargs["properties"].update({"polarity": Polarity("normal")})
    except KeyError:
        kwargs["properties"] = {"polarity": Polarity("normal")}
    return binary(**kwargs)


def binary_output(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "BO", **kwargs)
    kwargs["objectType"] = BinaryOutputObject
    try:
        kwargs["properties"].update({"polarity": Polarity("normal")})
    except KeyError:
        kwargs["properties"] = {"polarity": Polarity("normal")}
    return binary(**kwargs)


def binary_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "BV", **kwargs)
    kwargs["objectType"] = BinaryValueObject
    return binary(**kwargs)


def multistate(**kwargs):
    if "is_commandable" not in kwargs:
        kwargs["is_commandable"] = False
    default_states = make_state_text(["Off", "On"])
    definition = {
        "instance": 0,
        "properties": {
            # "eventState": EventState(),
            "stateText": default_states,
            # "numberOfStates": Unsigned(2),
        },
        "description": "No description",
        "presentValue": Unsigned(1),
        # "is_commandable": False,
        # "relinquishDefault": Unsigned(1),
    }
    return _create(definition, **kwargs)


def multistate_input(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "MSI", **kwargs)
    kwargs["objectType"] = MultiStateInputObject
    kwargs["relinquishDefault"] = Unsigned(1)

    return multistate(**kwargs)


def multistate_output(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "MSO", **kwargs)
    kwargs["objectType"] = MultiStateOutputObject
    kwargs["relinquishDefault"] = Unsigned(1)

    return multistate(**kwargs)


def multistate_value(**kwargs):
    kwargs["name"] = set_default_if_not_provided("name", "MSV", **kwargs)
    kwargs["objectType"] = MultiStateValueObject
    kwargs["relinquishDefault"] = Unsigned(1)

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
        "relinquishDefault": "inactive",
    }
    return _create(definition, **kwargs)


def date_value(**kwargs):
    definition = {
        "name": "DATE_VALUE",
        "objectType": DateValueObject,
        "instance": 0,
        "description": "No description",
        "presentValue": Date().now(),
        "properties": {},
        "is_commandable": False,
        # "relinquishDefault": "inactive",
    }
    return _create(definition, **kwargs)


def datetime_value(**kwargs):
    definition = {
        "name": "DATETIME_VALUE",
        "objectType": DateTimeValueObject,
        "instance": 0,
        "description": "No description",
        "presentValue": DateTime(date=Date().now(), time=Time().now()),
        "properties": {},
        "is_commandable": False,
    }
    return _create(definition, **kwargs)


def trendlog(**kwargs):
    definition = {
        "name": "TREND_LOG",
        "objectType": TrendLogObject,
        "instance": 0,
        "description": "No description",
        "properties": {
            "enable": True,
            "logBuffer": ListOf(LogRecord)([]),
            # "logDeviceObjectProperty": DeviceObjectPropertyReference(
            #    objectIdentifier=ObjectIdentifier("trendLog", 0),
            # ),
            "trendLog_datatype": "realValue",
        },
    }
    return _create(definition, **kwargs)
