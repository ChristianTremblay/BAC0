# Produal https://produal-pim.rockon.io/rockon/api/v1/int/extmedia/openFile/01TGWJBKHN5NJ7WCUCEBD3WTAZWWYXGYKY
"""
Custom Objects and Properties
"""

from bacpypes3.basetypes import PropertyIdentifier
from bacpypes3.debugging import ModuleLogger
from bacpypes3.local.object import _Object
from bacpypes3.primitivedata import (
    ObjectType,
    Real,
    Unsigned,
)


# some debugging
_debug = 0
_log = ModuleLogger(globals())


# this vendor identifier reference is used when registering custom classes
_vendor_id = 783
_vendor_name = "Produal Oy"


class ProprietaryObjectType(ObjectType):
    """
    This is a list of the object type enumerations for proprietary object types,
    see Clause 23.4.1.
    """

    CONFIG1 = 128
    CONFIG2 = 128


class Config1(_Object):
    """
    This is a proprietary object type.
    """

    # object identifiers are interpreted from this customized subclass of the
    # standard ObjectIdentifier that leverages the ProprietaryObjectType
    # enumeration in the vendor information
    objectIdentifier: ProprietaryObjectType.CONFIG1

    # all objects get the object-type property to be this value
    objectType = ProprietaryObjectType("CONFIG1")

    # all objects have an object-name property, provided by the parent class
    # with special hooks if an instance of this class is bound to an application
    # objectName: CharacterString

    # the property-list property of this object is provided by the getter
    # method defined in the parent class and computed dynamically
    # propertyList: ArrayOf(PropertyIdentifier)
    TEMPSP_LL: Real
    TEMPSP_HL: Real
    NMBHTGSTAGES: Unsigned


class Config2(_Object):
    """
    This is a proprietary object type.
    """

    # object identifiers are interpreted from this customized subclass of the
    # standard ObjectIdentifier that leverages the ProprietaryObjectType
    # enumeration in the vendor information
    objectIdentifier: ProprietaryObjectType.CONFIG2

    # all objects get the object-type property to be this value
    objectType = ProprietaryObjectType("CONFIG2")

    # all objects have an object-name property, provided by the parent class
    # with special hooks if an instance of this class is bound to an application
    # objectName: CharacterString

    # the property-list property of this object is provided by the getter
    # method defined in the parent class and computed dynamically
    # propertyList: ArrayOf(PropertyIdentifier)
    LOCK_MODE: Unsigned
    LOCK_PWD: Unsigned
    BOOST_TRGT: Unsigned


class ProprietaryPropertyIdentifier(PropertyIdentifier):
    """
    This is a list of the property identifiers that are used in custom object
    types or are used in custom properties of standard types.
    """

    # this is a custom property using a standard datatype
    LOCK_MODE = 40155
    LOCK_PWD = 40156
    BOOST_TRGT = 40158
