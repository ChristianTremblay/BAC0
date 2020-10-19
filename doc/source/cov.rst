COV in BAC0
====================

BACnet supports a change of value (COV) mechanism that allow to subscribe to a device point 
to get notified when the value of this point changes.

In BAC0, you can subscribe to a COV from a point directly ::

    device['point'].subscribe_cov()

or from the network itself ::

    bacnet.cov(address, objectID)


Confirmed COV
--------------
If the device to which you want to subscribe a COV supports it, it is possible to use
a `confirmed` COV. In this case, the device will wait for a confirmation that you 
received the notification. This is the default case for BAC0.

To disable this, just pass `confirmed=False` to the subscribe_cov function.

Lifetime
--------------- 
COV subscription can be restricted in time by using the `lifetime` argument. By default, this is
set to None (unlimited).

Callback
========
It can be required to call a function when a COV notification is received. This is done by providing 
the function as a callback to the subscription ::

    # The Notification will pass a variable named "elements" to the callback
    # your function must include this argument

    # elements is a dict containing all the information of the COV 
    def my_callback(elements):
        print("Present value is : {}".format(elements['properties']['presentValue'])

.. note:: 
    Here you can find a typical COV notification and the content of elements.
    {'source': <RemoteStation 2:6>, 'object_changed': ('analogOutput', 2131), 'properties': {'presentValue': 45.250762939453125, 'statusFlags': [0, 0, 0, 0]}}