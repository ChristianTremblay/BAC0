Read from network
===================
To read from a BACnet device using the bacnet instance just created by the connection. You must
know what you are trying to read though and some technical specificities of BACnet. Let's have a 
simple look at how things work in BACnet. 

To read to a point, you need to create a request that will send some message to the network (directly
to a controller (unicast) or at large (broadcast) with the object and property from the object you
want to read from. The BACnet standard defines a lot of different objects. All objects provides some
properties that we can read from. You can refer bacpypes source code (object.py) to get some examples.

For the sake of the explanation here, we'll take one common object : an analog value.

The object type is an **analogValue**. This object contains properties. Let's have a look to 
bacpypes definition of an AnalogValue ::

    @register_object_type
    class AnalogValueObject(Object):
        objectType = 'analogValue'
        _object_supports_cov = True

        properties = \
            [ ReadableProperty('presentValue', Real)
            , ReadableProperty('statusFlags', StatusFlags)
            , ReadableProperty('eventState', EventState)
            , OptionalProperty('reliability', Reliability)
            , ReadableProperty('outOfService', Boolean)
            , ReadableProperty('units', EngineeringUnits)
            , OptionalProperty('minPresValue', Real)
            , OptionalProperty('maxPresValue', Real)
            , OptionalProperty('resolution', Real)
            , OptionalProperty('priorityArray', PriorityArray)
            , OptionalProperty('relinquishDefault', Real)
            , OptionalProperty('covIncrement', Real)
            , OptionalProperty('timeDelay', Unsigned)
            , OptionalProperty('notificationClass',  Unsigned)
            , OptionalProperty('highLimit', Real)
            , OptionalProperty('lowLimit', Real)
            , OptionalProperty('deadband', Real)
            , OptionalProperty('limitEnable', LimitEnable)
            , OptionalProperty('eventEnable', EventTransitionBits)
            , OptionalProperty('ackedTransitions', EventTransitionBits)
            , OptionalProperty('notifyType', NotifyType)
            , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp, 3))
            , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString, 3))
            , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString, 3))
            , OptionalProperty('eventDetectionEnable', Boolean)
            , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
            , OptionalProperty('eventAlgorithmInhibit', Boolean)
            , OptionalProperty('timeDelayNormal', Unsigned)
            , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
            ]

Readable properties are mandatory and all BACnet device must implement AnalogValue with those properties. 
Optional properties, may or may not be available, depending on the choices the manufacturer made.

With BAC0, there is two different kind of requests we can use to read from the network

  - read
  - readMultiple

Read will be used to read only one (1) property.
readMultiple will be used to read multiple properties. The number here is not defined. Many elements will 
have an impact on the number of properties you can retrieve using readMultiple. Is the device an MSTP one
or a IP one. Does the device support segmentation ? Etc. Many details that could prevent you from using 
readMultiple with very big requests. Usually, when discovering a device points, BAC0 will use readMultiple
and will use chunks of 25 properties. It's up to you to decide how many properties you'll read.

So, to read from BACnet. The request will contains the address of the device from which we want to read
(example '2:5'). Then the object type (analogValue), the instance number (the object "address" or "register"...
let's pretend it's 1) and the property from the object we want to read (typically the 'presentValue').

.. notes::
    Please note that some objects are very complex to read from. For instance, schedules have a lot of
    details and the properties defining the object are themselves created from arrays of other type of data.
    A simple `bacnet.read` in the context of a schedule would be pretty hard to interpret. This is why BAC0
    will implement some special read functions for complex items like that. To read schedules, have a look
    to the schedules topic and the function calld `bacnet.read_schedule()`.

Read examples
........................
Once you know the device you need to read from, you can use ::

    bacnet.read('address object object_instance property')

Read property multiple can also be used ::

    bacnet.readMultiple('address object object_instance property_1 property_2') #or
    bacnet.readMultiple('address object object_instance all')

Read multiple
..................
Using simple read is a costly way of retrieving data. If you need to read a lot of data from a controller, 
and this controller supports read multiple, you should use that feature.

When defining `BAC0.devices`, all polling requests will use readMultiple to retrive the information on the network.

There is actually two way of defining a read multiple request. The first one inherit from bacpypes console examples 
and is based on a string composed from a list of properties to be read on the network. This is the example I showed 
previously.

Recently, a more flexible way of creating those requests have been added using a dict to create the requests. 
The results are then provided as a dict for clarity. Because the old way just give all the result in order of the request, 
which can lead to some errors and is very hard to interact with on the REPL.

The `request_dict` must be created like this ::

    _rpm = {'address': '303:9', 
            'objects': {
                'analogInput:1094': ['objectName', 'presentValue', 'statusFlags', 'units','description'], 
                'analogValue:4410': ['objectName', 'presentValue', 'statusFlags', 'units', 'description']
                }
            }

If an array index needs to be used, the following syntax can be used in the property name ::

    # Array index 1 of propertyName
    'propertyName@idx:1' 

This dict must be used with the already exsiting function `bacnet.readMultiple()` and passed
via the argument named **request_dict**. ::

    bacnet.readMultiple('303:9', request_dict=_rpm)

The result will be a dict containing all the information requested. ::

    # result of request
    {
        ('analogInput', 1094): [
            ('objectName', 'DA-VP'),
            ('presentValue', 4.233697891235352),
            ('statusFlags', [0, 0, 0, 0]),
            ('units', 'pascals'),
            ('description', 'Discharge Air Velocity Pressure')
            ],
        ('analogValue', 4410): [
            ('objectName', 'SAFLOW-ABSEFFORT'),
            ('presentValue', 0.005016503389924765),
            ('statusFlags', [0, 0, 1, 0]),
            ('units', 'percent'),
            ('description', '')
            ]
    }

Write to property
........................
To write to a single property ::

    bacnet.write('address object object_instance property value - priority')

Write to multiple properties
....................................
Write property multiple is also implemented. You will need to build a list for your requets ::

    r = ['analogValue 1 presentValue 100','analogValue 2 presentValue 100','analogValue 3 presentValue 100 - 8','@obj_142 1 @prop_1042 True']
    bacnet.writeMultiple(addr='2:5',args=r,vendor_id=842)
    
..note::
    WARNING. See the section on Proprietary objects and properties for details about vendor_id and @obj_142.


.. _berryconda : https://github.com/jjhelmus/berryconda  
.. _RaspberryPi : http://www.raspberrypi.org
