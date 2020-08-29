Local Objects
================

Until now, we've looked into the capability of BAC0 to act as a "client" device. This is not a very
good term in the context of BACnet but at least it is easy to understand. But BAC0 can also act as 
a BACnet device. It can be found in a network and will present its properties to every other BACnet devices.

What if you want to create a BACnet device with objects with BAC0 ?

You will need to provide local objects that will be added to the application part of the BAC0 instance.
This part is called `this_application`.

What are BACnet objects
-------------------------

BACnet objects are very diverse. You probably know the main ones like AnalogValue or BinaryInput or
AnalogOutput, etc.
But there are more. Depending on your needs, there will be an object that fit what you try to define
in your application.
The complet definition of all BACnet objects fall outside the scope of this document. Please refer to
the BACnet standard if you want to know more about them. For the sake of understanding, I'll cover
a few of them.

The definition of the BACnet obejcts is provided by `bacpypes.object`. You will need to import the 
different classes of objects you need when you will create the objects.

An object, like you probably know now, owes properties. Those properties can be read-only, writable,
mandatory or optional. This is defined in the standard. Typically, the actual value of an object is 
given by a property name `presentValue`. Another property called `relinquishDefault` would hold the 
value the object should give as a presentValue when all other priorityArray are null. PriorityArray 
is also a property of an object. When you create an object, you must know which properties you must
add to the object and how you will interact with thoses properties and how they will interact with 
one another.

This makes a lot to know when you first want to create one object.

A place to start
------------------

The enormous complexity of BACnet objects led me to think of a way to generate objects with a good
basis. Just enough properties depending on the commandability of the object (do you need other devices
to write to those objects ?). This decision have an impact on the chosen properties of a BACnet object.

For any commandable object, it would be reasonable to provide a priorityArray and a relinquishDefault.
Those propoerties make no sense for a non-commandable object.

For any analog object, an engineering unit should be provided.

Those basic properties, depending on the type of objects, the BAC0's user should not have to think about
them. They should just be part of the object.

Working in the factory
------------------------

BAC0 will allow the creation of BACnet objects with a special class named ObjectFactory. This class will take
as argument the objectType, instance, name, description, properties, etc and create the object. This object 
will then be added to a class variable (a dict) that will be used later to populate the application will all 
the created objects.

The factory will take as an argument `is_commandable` (boolean) and will modify the base type of object to 
make it commandable if required. This part is pretty complex as a subclass with a Commandable mixin must be
created fot each objectType. ObjectFactory uses a special decorator that will recreate a new subclass with
eveything that is needed to make the point commandable.

Another decorator will also allow the addition of custom properties (that would not be provided by default)
if it's required. 

Another decorator will allow the addition of "features" to the objects. Thos will need to be defined but we 
can think about event generation, alarms, MinOfOff behaviour, etc.

The user will not have to think about the implementation of the decorators as everything is handled by the
ObjectFactory. But that said, nothing prevent you to create your own implementation of a factory using those
decorators.

An example
-----------

A good way to understand how things work is by giving an example. This code is part of the tests folder and
will give you a good idea of the way objects can be defined inside a BAC0's instance ::

    def build():
        bacnet = BAC0.lite(deviceId=3056235)

        new_obj = ObjectFactory(
            AnalogValueObject,
            0,
            "av0",
            properties={"units": "degreesCelsius"},
            presentValue=1,
            description="Analog Value 0",
        )
        ObjectFactory(
            AnalogValueObject,
            1,
            "av1",
            properties={"units": "degreesCelsius"},
            presentValue=12,
            description="Analog Value 1",
            is_commandable=True,
        )
        ObjectFactory(
            CharacterStringValueObject,
            0,
            "cs0",
            presentValue="Default value",
            description="String Value 0",
        )
        ObjectFactory(
            CharacterStringValueObject,
            1,
            "cs1",
            presentValue="Default value",
            description="Writable String Value 1",
            is_commandable=True,
        )

        new_obj.add_objects_to_application(bacnet.this_application)
        return bacnet