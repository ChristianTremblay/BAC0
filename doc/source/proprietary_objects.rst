Proprietary Objects
====================

Some manufacturers provide special variables inside their controllers in the
form of proprietary objects or expand some objects with proprietary properties. 
BAC0 supports the creation of those objects but some work is needed on your side to register them.

In fact, you will need to know what you are looking for when dealing with proprietary objects or properties.
Should you write to them or make them read only ? What type should you declare ? 

Once you know the information, you are ready to make your implementation.

The actual BAC0 implementation allow the user to be able to read proprietary objects or proprietary properties
without defining a special class. This is done using a special syntax that will inform BAC0 of the nature or the read.

Why ? Bacpypes requests (in BAC0) are made sequencially using well-known property names and address. When dealing
with proprietary objects or properties, names and addresses are numbers. This is somewhat hard to detect if the
request contains an error, is malformed or contains a proprietary thing in it. The new syntax will tell BAC0 that 
we need to read a proprietary object or property.

If you need to read an object named "142", you will tell BAC0 to read `@obj_142`
If you need to read a property named 1032, you will tell BAC0 to read `@prop_1032`

This way, you could build a request this way : 

    bacnet.read('2:5 @obj_142 1 @prop_1032')
    # or
    bacnet.readMultiple('2:5 @obj_142 1 objectName @prop_1032')

Writing to proprietary properties
**********************************
If you need to write to the property, things are a litlle more complicated. For example, JCI TEC3000 have 
a variable that needs to be written to so the thermostat know that the supervisor is active, a condition to 
use network schedule (if not, switch to internal schedule).

If you try this :

    bacnet.write('2000:10 device 5010 3653 True')

You'll get :

    TypeError: issubclass() arg 1 must be a class

This is because BAC0 doesn't know how to encode the value to write. You will need to define a class, register 
it so BAC0 knows how to encore the value and most importantly, you will need to provide the `vendor_id` to the
write function so BAC0 will know which class to use. Because 2 different vendors could potentially use the same 
"number" for a proprietary object or property with different type.


How to implement
-----------------
BAC0 will allow dynamic creation of the classes needed to read and write to those special variables. To
do so, a special dictionary need to be declared in this form ::
::

    name = {
        "name": "Class_Name",
        "vendor_id": integer,
        "objectType": "type",
        "bacpypes_type": Object,
        "properties": {
            "NameOfProprietaryProp": {"obj_id": 1110, "primitive": Boolean, "mutable": True},
        },
    }

    # name : Name of the class to be created
    # vendor_id : the manufacturer of the device
    # objectType : see bacpypes.object for reference (ex. 'device')
    # bacpypes_type : base class to instanciate (ex. BinaryValueObject)
    # properties : list of proprietary properties to add 
    #     name of the property (for reference)
    #     obj_id : instance of the property, usually an integer
    #     primitive : the kind of data for this property. Refer to `bacpypes.primitivedata`
    #     mutable : true = writable, default to false


Once the dictionary is completed, you need to call the spceial function `create_proprietaryobject`.
This function will dynamically create the class and register it with bacpypes so you will be able 
to read and write to the object.

To access the information (for now), you will use this syntax ::

    # Suppose an MSTP controller at address 2:5, device instance 5003
    # Vendor being Servisys (ID = 842)
    # Proprietary property added to the device object with object ID 1234
    bacnet.read('2:5 device 5003 1234', vendor_id=842)

If you want to look at the object registration, you can use this ::

    from bacpypes.object import registered_object_types
    registered_object_types

It is a dictionary containing all the registered type in use. As you can see, the majority of the
registration use vendor_id 0 which is the default. But if you register something for another vendor_id, 
you will see a new dictionary entry. 
Using the special `bacnet.read` argument "vendor_id" will then inform bacpypes that we want to use 
the special object definition for this particular vendor.

.. note::
    BAC0 will automatically register known proprietary classes at startup. See BAC0.core.proprietary_objects
    for details.

Proprietary objects
--------------------
Proprietary object can be accessed using ::

    # Let say device '2:5' have object (140,1)
    bacnet.read('2:5 140 1 objectName')

As they are proprietary objects, you will have to know what you are looking for. Typically, the properties
`objectName`, `objectIdentifier`, will be available. But you will often see proprietary properties 
attached to those objects. See next section.

To read all properties from an object, if implemented, one can use ::

    bacnet.readMultiple('2:5 140 1 all')

BAC0 will do its best to give you a complete list.

.. note::
    Please note that arrays under proprietary objects are not implemented yet. Also, context tags 
    objects are not detected automatically. You will need to build the object class to interact 
    with those objects. See next section.

Proprietary Property 
---------------------
One common case I'm aware of is the addition of proprietary properties to the DeviceObject of a device.
Those properties may, for example, give the CPU rate or memory usage of the controllers. On the TEC3000 (JCI), 
there is a "SupervisorOnline" property needed to be written to, allowing the BAS schedule to work.

To declare those properties, we need to extend the base object (the DeviceObject in this case) pointing this 
declaration to the vendor ID so bacpypes will know where to look. 

The following code is part of BAC0.core.proprietary_objects.jci and define proprietary properties added to 
the device object for JCI devices. Note that as there are multiple proprietary properties, we need to declare
them all in the same new class (the example presents 2 new properties). 

::

    #
    #   Proprietary Objects and their attributes
    #

    JCIDeviceObject = {
        "name": "JCI_DeviceObject",
        "vendor_id": 5,
        "objectType": "device",
        "bacpypes_type": DeviceObject,
        "properties": {
            "SupervisorOnline": {"obj_id": 3653, "primitive": Boolean, "mutable": True},
            "Model": {"obj_id": 1320, "primitive": CharacterString, "mutable": False},
        },
    }

This will allow us to interact with them after registration ::

    from BAC0.core.proprietary_objects.jci import JCIDeviceObject
    from BAC0.core.proprietary_objects.object import create_proprietaryobject
    create_proprietaryobject(**JCIDeviceObject)

    # Read model of TEC
    bacnet.read('2:5 device 5005 1320', vendor_id=5)
    # Write to supervisor Online
    bacnet.write('2:5 device 5005 3653 true',vendor_id=5)


.. note:: 
    In future version it will be able to define special device and attach some
    proprietary objects to them so tec['SupOnline'] would work...

Vendor Context for Read and Write
**********************************
In `BAC0.device`, the vendor_id context will be provided to the stack automatically. This mean that 
if a device is created and there is a extended implementation of an object (JCIDeviceObject for example)
BAC0 will recognize the proprietary object by default, without having the need to explicitly define the
vendor_id in the request ::

    instance_number = 1000
    prop_id = 1320
    device.read_property(('device',instance_number, prop_id))

will work.

Also, proprietary objects and properties classes are defined at startup so it is not necessary to explicitly 
register them.

Can proprietary objects be addded to a BAC0.device points
********************************************************************
Actually not, because of the way "points" are defined in BAC0. If you look at `BAC0.core.devices.Points.Point`
you will see that the notion of point is oriented differently than a BACnet object. 
Properties are a set of informations useful for BAC0 itself but are not "strictly" BACnet properties.
The value of a point will always be the `presentValue` of the BACnet object. In the context of proprietary
objects, this can't fit.

There are no "standard" way to create a proprietary object. Beside the fact that objectName, objectType and 
objectIdentifier must be provided, everything else is custom.

For this reason, proprietary objects must be dealt outside of the scope of a device, especially in the context
of writing to them.

How to implement readMultiple with proprietary objects and properties
**********************************************************************
It is possible to create read property multiple requests with them, using the syntax `@obj_` and `@prop_`.
So for now, you will be able to create a request yourself for one device at a time by chaining properties you want 
to read : 

    bacnet.readMultiple('2000:31 device 5012 @prop_3653 analogInput 1106 presentValue units') 

How to find proprietary objects and properties
********************************************************************
In BAC0, for a device or a point, you can use :

    device.bacnet_properties
    # or
    point.bacnet_properties

This will list `all` properties in the object. (equivalent of `bacnet.readMultiple('addr object id all')`)