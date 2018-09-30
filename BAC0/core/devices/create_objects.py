from bacpypes.object import MultiStateValueObject
from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import ArrayOf

from bacpypes.primitivedata import Real
from bacpypes.object import AnalogValueObject, Property, register_object_type

def create_MV(oid=1, pv=0, name='MV', states=['red','green','blue']):
    msvo = MultiStateValueObject(
           objectIdentifier=('multiStateValue', oid),
           objectName=name,
           presentValue=pv,
           numberOfStates=len(states),
           stateText=ArrayOf(CharacterString)(states),
           )
    return msvo

def create_AV(oid=1, pv=0, name='AV', units=''):
    avo = AnalogValueObject(
           objectIdentifier=('analogValue', oid),
           objectName=name,
           presentValue=pv,
           )
    return avo