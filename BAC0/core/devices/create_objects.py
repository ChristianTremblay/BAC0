from bacpypes.object import (
    MultiStateValueObject,
    AnalogValueObject,
    BinaryValueObject,
    AnalogInputObject,
    BinaryInputObject,
    AnalogOutputObject,
    BinaryOutputObject,
    CharacterStringValueObject,
    DateTimeValueObject,
    Property,
    register_object_type,
)

from bacpypes.local.object import (
    AnalogOutputCmdObject,
    AnalogValueCmdObject,
    BinaryOutputCmdObject,
    BinaryValueCmdObject,
)

from bacpypes.primitivedata import CharacterString, Date, Time, Real, Boolean
from bacpypes.constructeddata import ArrayOf
from bacpypes.basetypes import EngineeringUnits, DateTime, PriorityArray, StatusFlags

from .mixins.CommandableMixin import LocalBinaryOutputObjectCmd


def _make_mutable(obj, identifier="presentValue", mutable=True):
    """ 
    This function is not the way to go as it changes the class
    property...As bacpypes issue #224, it will need a lot of work
    """
    for prop in obj.properties:
        if prop.identifier == identifier:
            prop.mutable = mutable
    return obj


def create_MV(
    oid=1, pv=0, name="MV", states=["red", "green", "blue"], pv_writable=False
):
    msvo = MultiStateValueObject(
        objectIdentifier=("multiStateValue", oid),
        objectName=name,
        presentValue=pv,
        numberOfStates=len(states),
        stateText=ArrayOf(CharacterString)(states),
        priorityArray=PriorityArray(),
        statusFlags=StatusFlags(),
    )
    msvo = _make_mutable(msvo, mutable=pv_writable)
    deprecate_msg()
    return msvo


def create_AV(oid=1, pv=0, name="AV", units=None, pv_writable=False):
    avo = AnalogValueObject(
        objectIdentifier=("analogValue", oid),
        objectName=name,
        presentValue=pv,
        units=units,
        relinquishDefault=0,
        priorityArray=PriorityArray(),
        statusFlags=StatusFlags(),
    )
    avo = _make_mutable(avo, mutable=pv_writable)
    avo = _make_mutable(avo, identifier="relinquishDefault", mutable=pv_writable)
    deprecate_msg()
    return avo


def create_BV(
    oid=1, pv=0, name="BV", activeText="On", inactiveText="Off", pv_writable=False
):
    bvo = BinaryValueObject(
        objectIdentifier=("binaryValue", oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText,
        priorityArray=PriorityArray(),
        statusFlags=StatusFlags(),
    )
    bvo = _make_mutable(bvo, mutable=pv_writable)
    deprecate_msg()
    return bvo


def create_AI(oid=1, pv=0, name="AI", units=None):
    aio = AnalogInputObject(
        objectIdentifier=("analogInput", oid),
        objectName=name,
        presentValue=pv,
        units=units,
        outOfService=Boolean(False),
        statusFlags=StatusFlags(),
    )
    aio = _make_mutable(aio, identifier="outOfService", mutable=True)
    deprecate_msg()
    return aio


def create_BI(oid=1, pv=0, name="BI", activeText="On", inactiveText="Off"):
    deprecate_msg()
    return BinaryInputObject(
        objectIdentifier=("binaryInput", oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText,
        statusFlags=StatusFlags(),
    )


def create_AO(oid=1, pv=0, name="AO", units=None, pv_writable=False):
    aoo = AnalogOutputObject(
        objectIdentifier=("analogOutput", oid),
        objectName=name,
        presentValue=pv,
        units=units,
        priorityArray=PriorityArray(),
        statusFlags=StatusFlags(),
    )
    aoo = _make_mutable(aoo, mutable=pv_writable)
    deprecate_msg()
    return aoo


def create_BO(
    oid=1, pv=0, name="BO", activeText="On", inactiveText="Off", pv_writable=False
):
    boo = LocalBinaryOutputObjectCmd(
        objectIdentifier=("binaryOutput", oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText,
        statusFlags=StatusFlags(),
    )
    boo = _make_mutable(boo, mutable=pv_writable)
    deprecate_msg()
    return boo


def create_CharStrValue(oid=1, pv="null", name="String", pv_writable=False):
    charval = CharacterStringValueObject(
        objectIdentifier=("characterstringValue", oid),
        objectName=name,
        priorityArray=PriorityArray(),
        statusFlags=StatusFlags(),
    )
    charval = _make_mutable(charval, mutable=pv_writable)
    charval.presentValue = CharacterString(pv)
    deprecate_msg()
    return charval


def create_DateTimeValue(
    oid=1, date=None, time=None, name="DateTime", pv_writable=False
):
    datetime = DateTimeValueObject(
        objectIdentifier=("datetimeValue", oid),
        objectName=name,
        statusFlags=StatusFlags(),
    )
    datetime = _make_mutable(datetime, mutable=pv_writable)
    datetime.presentValue = DateTime(date=Date(date), time=Time(time))
    deprecate_msg()
    return datetime


def create_object(
    object_class, oid, objectName, description, presentValue=None, commandable=False
):
    new_object = object_class(
        objectIdentifier=(object_class.objectType, oid),
        objectName="{}".format(objectName),
        presentValue=presentValue,
        description=CharacterString("{}".format(description)),
        statusFlags=StatusFlags(),
    )
    deprecate_msg()
    return _make_mutable(new_object, mutable=commandable)


def set_pv(obj=None, value=None, flags=[0, 0, 0, 0]):
    obj.presentValue = value
    obj.statusFlags = flags


def create_object_list(objects_dict):
    """
    d = {name: (name, description, presentValue, units, commandable)}
    """
    obj_list = []
    for obj_id, v in objects_dict.items():
        object_class, name, oid, description, presentValue, commandable = v
        description = CharacterString(description)
        new_obj = create_object(
            object_class, name, oid, description, commandable=commandable
        )
        if presentValue:
            new_obj.presentValue = presentValue
        obj_list.append(new_obj)
    return obj_list


def deprecate_msg():
    print("*" * 80)
    print("create_xx functions are deprecated and will disappear from a future release")
    print(
        "BAC0.core.device.local.object using the ObjectFactory will be the new way to define objects"
    )
    print("Refer to the doc for details")
    print("*" * 80)
