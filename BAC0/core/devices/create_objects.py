from bacpypes.object import MultiStateValueObject,AnalogValueObject, BinaryValueObject, Property, register_object_type
from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import ArrayOf
from bacpypes.primitivedata import Real, Boolean
from bacpypes.basetypes import EngineeringUnits


def create_MV(oid=1, pv=0, name='MV', states=['red','green','blue']):
    msvo = MultiStateValueObject(
           objectIdentifier=('multiStateValue', oid),
           objectName=name,
           presentValue=pv,
           numberOfStates=len(states),
           stateText=ArrayOf(CharacterString)(states),
           )
    return msvo

def create_AV(oid=1, pv=0, name='AV', units=None):
    avo = AnalogValueObject(
           objectIdentifier=('analogValue', oid),
           objectName=name,
           presentValue=pv,
           units=units
           )
    return avo

def create_BV(oid=1, pv=0, name='BV', activeText='On', inactiveText='Off'):
    bvo = BinaryValueObject(
           objectIdentifier=('binaryValue', oid),
           objectName=name,
           presentValue=pv,
           activeText=activeText,
           inactiveText=inactiveText
           )
    return bvo