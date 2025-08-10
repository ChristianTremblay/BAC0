COV in BAC0
====================

BACnet supports a change of value (COV) mechanism that allow to subscribe to a device point 
to get notified when the value of this point changes.

In BAC0, you can subscribe to a COV from a point directly (awaitable) ::

    # subscribe for 90 seconds (renew as needed)
    await device['AV'].subscribe_cov(lifetime=90)

or from the network itself (starts a background task immediately) ::

    bacnet.cov(address, objectID, lifetime=300, confirmed=False)

.. note:: 
    objectID is a tuple created with the object type as a string and the instance. For example
    analog input 1 would be : `("analogInput", 1)`

Minimal async example
----------------------
This mirrors the pattern in tests/manual_test_cov.py, trimmed to essentials ::

    async with BAC0.start() as bacnet:
        # Connect to a remote device and get a point
        dev = await BAC0.device("192.168.1.50:47808", 1234, bacnet, poll=0)
        av = dev["AV"]

        # Subscribe to COV notifications for 90 seconds
        await av.subscribe_cov(lifetime=90)

Confirmed COV
--------------
If the device to which you want to subscribe a COV supports it, it is possible to use
a `confirmed` COV. In this case, the device will wait for a confirmation that you 
received the notification. The default in BAC0 is unconfirmed (confirmed=False).

To require confirmation, pass `confirmed=True` to subscribe_cov or bacnet.cov.

Lifetime
--------------- 
COV subscription duration is controlled by the `lifetime` argument (seconds). By default, this is
set to 900 seconds. Renew as needed to keep the subscription alive.

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
    # property_identifier and property_value (runs in background)
    bacnet.cov('3:10', ("analogValue", 1), callback=my_point_callback)

Canceling a subscription
------------------------
- Point-level: await device['AV'].cancel_cov()
- Network-level: use bacnet.cov_tasks to locate the process identifier and cancel it ::

    ids = list(bacnet.cov_tasks.keys())
    if ids:
        bacnet.cancel_cov(ids[0])

.. note:: 
    Point-level subscribe_cov is awaited to establish the subscription. The network-level `bacnet.cov(...)` helper starts a background task immediately and does not return a task id; inspect `bacnet.cov_tasks` to manage running subscriptions.