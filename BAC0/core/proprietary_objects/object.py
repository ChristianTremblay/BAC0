from bacpypes.object import (
    Object,
    BinaryValueObject,
    CharacterStringValueObject,
    Property,
    register_object_type,
)
from bacpypes.primitivedata import Boolean, Real, CharacterString, Atomic


class ProprietaryObject(Object):
    def __new__(cls, **kwargs):
        Object.__init__(cls)
        props = []
        for k, v in kwargs["properties"].items():
            props.append(
                Property(int(v["obj_id"]), v["primitive"], mutable=v["mutable"])
            )
        cls.properties = props
        return super(ProprietaryObject, cls).__new__(cls)

    def __init__(self, **kwargs):
        self.bacpypes_type.__init__(self)


def register(cls):
    register_object_type(cls, vendor_id=cls.vendor_id)


def create_proprietaryobject(**params):
    new_class = type(params["name"], (ProprietaryObject,), params)
    _nc = new_class(**params)
    register(new_class)
