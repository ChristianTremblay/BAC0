from .decorator import bacnet_properties, make_commandable, create

from ...utils.notes import note_and_log
from ....scripts.Base import Base
from ...app.ScriptApplication import BAC0Application

from bacpypes.object import (
    AnalogInputObject,
    AnalogValueObject,
    BinaryValueObject,
    Property,
    register_object_type,
    registered_object_types,
    DatePatternValueObject,
    ReadableProperty,
    WritableProperty,
    OptionalProperty,
)
from bacpypes.basetypes import (
    EngineeringUnits,
    DateTime,
    PriorityArray,
    StatusFlags,
    Reliability,
    Polarity,
)

from collections import namedtuple
from colorama import Fore, Back, Style


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

    instances = {}

    definition = namedtuple(
        "Definition",
        "name, objectType, instance, properties, description, presentValue, is_commandable, relinquish_default",
    )

    objects = {}
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
        relinquish_default=None,
    ):
        self._properties = ObjectFactory.default_properties(
            objectType, properties, is_commandable, relinquish_default
        )
        pv_datatype = ObjectFactory.get_pv_datatype(objectType)

        if not isinstance(presentValue, pv_datatype):
            try:
                presentValue = pv_datatype(presentValue)
            except:
                raise ValueError("Wrong datatype provided for presentValue")

        @bacnet_properties(self._properties)
        @make_commandable()
        def _create_commandable(
            objectType, instance, objectName, presentValue, description
        ):
            return create(objectType, instance, objectName, presentValue, description)

        @bacnet_properties(self._properties)
        def _create(objectType, instance, objectName, presentValue, description):
            return create(objectType, instance, objectName, presentValue, description)

        objectName, instance = self.validate_name_and_instance(
            objectType, objectName, instance
        )

        if is_commandable:
            self.objects[objectName] = _create_commandable(
                objectType, instance, objectName, presentValue, description
            )
        else:
            self.objects[objectName] = _create(
                objectType, instance, objectName, presentValue, description
            )

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
                self._log.warning(
                    "Instance alreaday taken, using {} instead".format(instance)
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
            objectName = "{}-{}".format(objectName, instance)
            self._log.warning("Name already taken, using {} instead".format(objectName))

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
            relinquish_default=definition["relinquish_default"],
        )

    @staticmethod
    def properties_for(objectType):
        prop_list = {}
        for prop in objectType.properties:
            prop_list[prop.identifier] = {
                "datatype": prop.datatype,
                "optional": prop.optional,
                "mutable": prop.mutable,
                "default": prop.default,
            }
        return prop_list

    @staticmethod
    def get_pv_datatype(objectType):
        for prop in objectType.properties:
            if prop.identifier == "presentValue":
                return prop.datatype
        raise KeyError("Unknown")

    @staticmethod
    def clear_objects():
        ObjectFactory.objects = {}
        ObjectFactory.instances = {}

    def add_objects_to_application(self, app):
        if isinstance(app, Base):
            app = app.this_application
        if not isinstance(app, BAC0Application):
            raise TypeError("Provide BAC0Application object or BAC0 Base instance")
        for k, v in self.objects.items():
            try:
                app.add_object(v)
                self._log.info("Adding {} to application.".format(k))
            except RuntimeError:
                self._log.warning(
                    "There is already an object named {} in application.".format(k)
                )

    def __repr__(self):
        return "{}".format(self.objects)

    @staticmethod
    def default_properties(
        objectType, properties, is_commandable=False, relinquish_default=None
    ):
        _properties = properties or {}
        if "statusFlags" not in _properties.keys():
            _properties["statusFlags"] = [0, 0, 0, 0]
        if "reliability" not in _properties.keys():
            _properties["reliability"] = Reliability(0)
        if (
            "analog" in objectType.__name__.lower()
            and "units" not in _properties.keys()
        ):
            raise ValueError("Provide Engineering Units in properties")
        if is_commandable and (
            "input" in objectType.__name__.lower()
            or "output" in objectType.__name__.lower()
        ):
            _properties["outOfService"] = False
        if is_commandable:
            _properties["priorityArray"] = PriorityArray()
            _properties["relinquishDefault"] = ObjectFactory.relinquish_default_value(
                objectType, relinquish_default
            )
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
        _repr += "\n| " + Fore.CYAN + "{}".format(objectType)
        _repr += Fore.YELLOW + "\n|" + "*" * 99
        _repr += "\n"
        _repr += (
            "| "
            + Fore.WHITE
            + "Support COV : {}\n".format(bacnet_object._object_supports_cov)
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
