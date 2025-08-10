COV in BAC0
====================

BACnet supports a change of value (COV) mechanism that allow to subscribe to a device point 
to get notified when the value of this point changes.

In BAC0, you can subscribe to a COV from a point directly ::

    await device['point'].subscribe_cov()

or from the network itself ::

    bacnet.cov(address, objectID)

.. note:: 
    objectID is a tuple created with the object type as a string and the instance. For example
    analog input 1 would be : `("analogInput", 1)`

Confirmed COV
--------------
If the device to which you want to subscribe a COV supports it, it is possible to use
a `confirmed` COV. In this case, the device will wait for a confirmation that you 
received the notification. This is the default case for BAC0.

To disable this, pass `confirmed=False` to subscribe_cov.

Lifetime
--------------- 
COV subscription can be restricted in time by using the `lifetime` argument. By default, this is
set to None (unlimited).

Callback
========
It can be required to call a function when a COV notification is received. This is done by providing 
the function as a callback to the subscription ::

    # For device['point'].subscribe_cov the callback receives keyword args:
    #   property_identifier, property_value
    def my_point_callback(property_identifier, property_value, **_):
        print(f"{property_identifier}: {property_value}")

    await device['AV'].subscribe_cov(callback=my_point_callback)

    # For bacnet.cov(address, objectID) the callback also receives
    # property_identifier and property_value
    bacnet.cov('3:10', ("analogValue", 1), callback=my_point_callback)

.. note:: 
    Point-level subscribe_cov is awaited to establish the subscription. The network-level `bacnet.cov(...)` helper starts a background task immediately.