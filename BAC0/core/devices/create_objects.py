
from bacpypes.object import MultiStateValueObject, AnalogValueObject, \
    BinaryValueObject, AnalogInputObject, \
    BinaryInputObject, AnalogOutputObject, \
    BinaryOutputObject, Property, register_object_type
from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import ArrayOf
from bacpypes.primitivedata import Real, Boolean
from bacpypes.basetypes import EngineeringUnits


def create_MV(oid=1, pv=0, name='MV', states=['red', 'green', 'blue']):
    msvo = MultiStateValueObject(
        objectIdentifier=('multiStateValue', oid),
        objectName=name,
        presentValue=pv,
        numberOfStates=len(states),
        stateText=ArrayOf(CharacterString)(states)
    )
    return msvo


def create_AV(oid=1, pv=0, name='AV', units=None):
    avo = AnalogValueObject(
        objectIdentifier=('analogValue', oid),
        objectName=name,
        presentValue=pv,
        units=units,
    )
    return avo


def create_BV(oid=1, pv=0, name='BV', activeText='On', inactiveText='Off'):
    bvo = BinaryValueObject(
        objectIdentifier=('binaryValue', oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText,
    )
    return bvo


def create_AI(oid=1, pv=0, name='AI', units=None):
    aio = AnalogInputObject(
        objectIdentifier=('analogInput', oid),
        objectName=name,
        presentValue=pv,
        units=units
    )
    return aio


def create_BI(oid=1, pv=0, name='BI', activeText='On', inactiveText='Off'):
    bio = BinaryInputObject(
        objectIdentifier=('binaryInput', oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText
    )
    return bio


def create_AO(oid=1, pv=0, name='AO', units=None):
    aoo = AnalogOutputObject(
        objectIdentifier=('analogOutput', oid),
        objectName=name,
        presentValue=pv,
        units=units
    )
    return aoo


def create_BO(oid=1, pv=0, name='BO', activeText='On', inactiveText='Off'):
    boo = BinaryOutputObject(
        objectIdentifier=('binaryOutput', oid),
        objectName=name,
        presentValue=pv,
        activeText=activeText,
        inactiveText=inactiveText
    )
    return boo
