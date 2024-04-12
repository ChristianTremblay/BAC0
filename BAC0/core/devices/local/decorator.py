from functools import wraps
from typing import Any, Callable, Dict, Tuple, Type, Union

from bacpypes3.basetypes import EngineeringUnits
from bacpypes3.constructeddata import ListOf
from bacpypes3.local.cmd import Commandable
from bacpypes3.local.oos import OutOfService
from bacpypes3.primitivedata import CharacterString

# from bacpypes3.object import TrendLogObject
from BAC0.core.devices.local.object import TrendLogObject

_SHOULD_BE_COMMANDABLE = ["relinquishDefault", "outOfService", "lowLimit", "highLimit"]

_required_binary_input: Tuple[str, ...] = (
    "presentValue",
    "statusFlags",
    "eventState",
    "outOfService",
    "polarity",
)

_required_binary_output: Tuple[str, ...] = (
    "presentValue",
    "statusFlags",
    "eventState",
    "outOfService",
    "polarity",
    "priorityArray",
    "relinquishDefault",
    "currentCommandPriority",
)

_required_analog_output: Tuple[str, ...] = (
    "presentValue",
    "statusFlags",
    "eventState",
    "outOfService",
    "polarity",
    "priorityArray",
    "relinquishDefault",
    "currentCommandPriority",
)

_required_analog_value: Tuple[str, ...] = ("priorityArray",)


def make_commandable() -> Callable:
    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            _type = obj.get_property_type("presentValue")
            base_cls = obj.__class__
            base_cls_name = obj.__class__.__name__ + "Cmd"
            new_type = type(
                base_cls_name,
                (Commandable, base_cls),
                {
                    "_required": (
                        "priorityArray",
                        "relinquishDefault",
                        "currentCommandPriority",
                    )
                },
            )
            objectType, instance, objectName, presentValue, description = args
            new_object = new_type(
                objectIdentifier=(base_cls.objectType, instance),
                objectName=f"{objectName}",
                presentValue=presentValue,
                description=CharacterString(f"{description}"),
            )
            return new_object

        return wrapper

    return decorate


def make_outOfService() -> Callable:
    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            base_cls = obj.__class__
            base_cls_name = obj.__class__.__name__ + "OOS"
            new_type = type(
                base_cls_name,
                (OutOfService, base_cls),
                {},
            )
            objectType, instance, objectName, presentValue, description = args
            new_object = new_type(
                objectIdentifier=(base_cls.objectType, instance),
                objectName=f"{objectName}",
                presentValue=presentValue,
                description=CharacterString(f"{description}"),
            )
            return new_object

        return wrapper

    return decorate


def add_feature(cls: Type) -> Callable:
    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            base_cls = obj.__class__
            base_cls_name = obj.__class__.__name__ + cls.__name__
            new_type = type(base_cls_name, (cls, base_cls), {})
            instance, objectName, presentValue, description = args
            new_object = new_type(
                objectIdentifier=(base_cls.objectType, instance),
                objectName=f"{objectName}",
                presentValue=presentValue,
                description=CharacterString(f"{description}"),
            )
            return new_object

        return wrapper

    return decorate


def bacnet_properties(properties: Dict[str, Any]) -> Callable:
    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            for property_name, value in properties.items():
                if property_name == "units":
                    new_prop = EngineeringUnits(value)
                    obj.__setattr__("units", new_prop)
                else:
                    try:
                        property_type = obj.get_property_type(property_name)
                        # print(f"Property Type : {property_type}")
                        # print(f"Value : {value}")
                        obj.__setattr__(property_name, property_type(value))
                    except (KeyError, AttributeError) as error:
                        raise ValueError(
                            f"Invalid property ({property_name}) for object | {error}"
                        )
            return obj

        return wrapper

    return decorate


def create(
    object_type: Type,
    instance: int,
    objectName: str,
    value: Union[int, str, ListOf],
    description: str,
) -> Any:
    if object_type is TrendLogObject:
        new_object = object_type(
            objectIdentifier=(object_type.objectType, instance),
            objectName=f"{objectName}",
            logBuffer=value,
            description=CharacterString("{description}"),
        )
    else:
        new_object = object_type(
            objectIdentifier=(object_type.objectType, instance),
            objectName=f"{objectName}",
            presentValue=value,
            description=CharacterString(f"{description}"),
        )
    return new_object
