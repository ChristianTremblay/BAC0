from .decorator import bacnet_properties, make_commandable, create

from ...utils.notes import note_and_log

from bacpypes.object import (
    AnalogInputObject,
    AnalogValueObject,
    BinaryValueObject,
    Property,
    register_object_type,
    registered_object_types,
    DatePatternValueObject,
)
from bacpypes.basetypes import (
    EngineeringUnits,
    DateTime,
    PriorityArray,
    StatusFlags,
    Reliability,
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

        if is_commandable:
            self.objects[objectName] = _create_commandable(
                objectType, instance, objectName, presentValue, description
            )
        else:
            self.objects[objectName] = _create(
                objectType, instance, objectName, presentValue, description
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

    def add_objects_to_application(self, app):
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
