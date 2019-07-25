Proprietary Objects
====================

Some manufacturers provide special variables inside their controllers in the
form of proprietary objects or expand some objects with proprietary properties. 
BAC0 supports the creation of those objects but some work is needed on your side to register them.

In fact, you will need to know what you are looking for when dealing with proprietary objects or properties.
Should you write to them or make them read only ? What type should you declare ? 

Once you know the information, you are ready to make your implementation.

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
Eventually, BAC0 could be "aware" of the vendor_id in the context of a `BAC0.device` and automatically
use the vendor_id syntax in the read. This is a work in progress.

Proprietary objects
--------------------
WIP

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
