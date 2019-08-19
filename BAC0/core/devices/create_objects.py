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
from bacpypes.primitivedata import CharacterString, Date, Time, Real, Boolean
from bacpypes.constructeddata import ArrayOf
from bacpypes.basetypes import EngineeringUnits, DateTime


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
    )
    msvo = _make_mutable(msvo, mutable=pv_writable)
    return msvo


def create_AV(oid=1, pv=0, name="AV", units=None, pv_writable=False):
    avo = AnalogValueObject(
        objectIdentifier=("analogValue", oid),
        objectName=name,
        presentValue=pv,
        units=units,
    )
    avo = _make_mutable(avo, mutable=pv_writable)
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
    )
    bvo = _make_mutable(bvo, mutable=pv_writable)
    return bvo


def create_AI(oid=1, pv=0, name="AI", units=None):
    aio = AnalogInputObject(
        objectIdentifier=("analogInput", oid),
        objectName=name,
        presentValue=pv,
        units=units,
    )
    return aio


def create_BI(oid=1, pv=0, name="BI", activeText="On", inactiveText="Off"):
    bio = BinaryInputObject(
        objectIdentifier=("binaryInput", oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText,
    )
    return bio


def create_AO(oid=1, pv=0, name="AO", units=None, pv_writable=False):
    aoo = AnalogOutputObject(
        objectIdentifier=("analogOutput", oid),
        objectName=name,
        presentValue=pv,
        units=units,
    )
    aoo = _make_mutable(aoo, mutable=pv_writable)
    return aoo


def create_BO(
    oid=1, pv=0, name="BO", activeText="On", inactiveText="Off", pv_writable=False
):
    boo = BinaryOutputObject(
        objectIdentifier=("binaryOutput", oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText,
    )
    boo = _make_mutable(boo, mutable=pv_writable)
    return boo


def create_CharStrValue(oid=1, pv="null", name="String", pv_writable=False):
    charval = CharacterStringValueObject(
        objectIdentifier=("characterstringValue", oid), objectName=name
    )
    charval = _make_mutable(charval, mutable=pv_writable)
    charval.presentValue = CharacterString(pv)
    return charval


def create_DateTimeValue(
    oid=1, date=None, time=None, name="DateTime", pv_writable=False
):
    datetime = DateTimeValueObject(
        objectIdentifier=("datetimeValue", oid), objectName=name
    )
    datetime = _make_mutable(datetime, mutable=pv_writable)
    datetime.presentValue = DateTime(date=Date(date), time=Time(time))
    return datetime
