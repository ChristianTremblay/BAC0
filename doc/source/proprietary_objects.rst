Proprietary Objects
====================

Some manufacturers provide special variables inside their controllers in the
form of proprietary objects or expand standard objects with proprietary
properties. BAC0 supports both via two complementary approaches:

1) Numeric IDs (no imports)
---------------------------

Use numeric object and property identifiers directly in a request string:

- ``@obj_142`` means a proprietary object type with ID 142
- ``@prop_1032`` means a proprietary property identifier 1032

Examples::

    await bacnet.read('2:5 @obj_142 1 @prop_1032')
    await bacnet.readMultiple('2:5 @obj_142 1 objectName @prop_1032')

2) Class-based registration (import vendor classes)
---------------------------------------------------

bacpypes3 uses real Python classes to define vendor extensions. Importing these
classes registers the vendor information and enables named properties and
objects. BAC0 re-exports known vendor classes for convenience. Import once at
startup and bacpypes3 will “know what to do.”

See: :doc:`BAC0.core.proprietary_objects`

Quick examples::

    # Johnson Controls (vendor_id 5)
    from BAC0.core.proprietary_objects import JCIDeviceObject

    dev = await BAC0.device('2:5', 5005, bacnet)
    val = await dev.read_property('supervisory_device_online')

    # Produal (vendor_id 783) proprietary object names
    from BAC0.core.proprietary_objects import Produal783Config1
    temp_sp_ll = await dev.read_property(('CONFIG1', 1, 'TEMPSP_LL'))

Writing to proprietary properties
*********************************

When writing to a proprietary property with the raw string API you may see
errors like ``TypeError: issubclass() arg 1 must be a class`` if bacpypes3
doesn’t know how to encode the value. You must import the vendor classes so
bacpypes3 knows the datatype and encoding for that proprietary property. Vendor
context alone with numeric IDs is not sufficient.

Examples::

    # Via a device instance (vendor classes have been imported; vendor_id is passed automatically)
    await dev.write_property(('device', 5005, 'supervisory_device_online'), True)

    # Raw string syntax with numeric IDs (vendor classes must be imported)
    await bacnet._write('2:5 device 5005 3653 true', vendor_id=5)

Register vendor classes (bacpypes3 style)
-----------------------------------------

No dynamic class creation is needed. Simply import the vendor modules exposed
by BAC0; the import registers everything:

::

    from BAC0.core.proprietary_objects import (
        JCIDeviceObject,              # vendor_id 5
        PrivaBVDeviceObject,          # vendor_id 105
        Produal651Config,             # vendor_id 651
        Produal783Config1, Produal783Config2,  # vendor_id 783
    )

Proprietary objects
-------------------

Read by numeric IDs or by names (after import):

::

    # Numeric
    await bacnet.read('2:5 140 1 objectName')
    await bacnet.readMultiple('2:5 140 1 all')

    # Named (after importing vendor classes)
    name = await dev.read_property(('CONFIG1', 1, 'objectName'))

Proprietary properties
----------------------

Examples on a JCI device (vendor_id 5):

::

    # Named (after import)
    model = await dev.read_property(('device', 5005, 'pcode'))
    await dev.write_property(('device', 5005, 'supervisory_device_online'), True)

Vendor context for reads and writes
-----------------------------------

- bacpypes3 resolves vendor context from the device info cache. On first
    contact, BAC0 populates this cache (Who-Is/I-Am), so subsequent reads/writes
    use the correct VendorInfo automatically.
- When you use ``BAC0.device(...)``, the device’s vendor_id is known and passed
    through; you don’t need to specify it.
- With the raw string API, you usually don’t need to pass ``vendor_id`` either,
    because the device_info_cache provides it. Supplying ``vendor_id=<id>`` is an
    optional fallback if the cache hasn’t been populated yet.
- Proprietary writes still require importing the vendor classes so bacpypes3
    knows the datatypes and encodings; vendor context alone isn’t enough.

Can proprietary objects be added to BAC0.device points?
-------------------------------------------------------

Not currently. BAC0 “points” map to presentValue-focused objects and metadata
used by BAC0, which doesn’t generalize to arbitrary proprietary objects.
Interact with proprietary objects directly via reads/writes as shown above.

How to implement readMultiple with proprietary objects and properties
---------------------------------------------------------------------

Use the ``@obj_`` and ``@prop_`` syntax when composing requests:

::

    await bacnet.readMultiple('2000:31 device 5012 @prop_3653 analogInput 1106 presentValue units')

How to find proprietary objects and properties
----------------------------------------------

For a device or a point, list all properties:

::

    props = await device.bacnet_properties()
    # or
    props = await point.bacnet_properties()

This is equivalent to ``bacnet.readMultiple('addr object id all')``.

.. note::
   The values are cached. If the device changes and you need fresh data, refresh
   first, then read again::

       await device.update_bacnet_properties()
       props = await device.bacnet_properties()

   For points::

       await point.update_bacnet_properties()
       props = await point.bacnet_properties()