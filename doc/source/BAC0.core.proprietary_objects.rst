Proprietary objects with bacpypes3
==================================

bacpypes3 handles vendor extensions by defining real Python classes for
proprietary objects and their properties. Importing these classes registers
the vendor information (VendorInfo) and proprietary enums with bacpypes3.

BAC0 integrates this pattern and supports two complementary ways to work with
vendor extensions.

Option A: Use numeric IDs (no imports)
--------------------------------------

This works without any vendor-specific imports:

- Use ``@obj_<id>`` for proprietary object types
- Use ``@prop_<id>`` for proprietary property identifiers

Examples::

    # Read a proprietary property by numeric IDs
    await bacnet.read('2:5 @obj_142 1 @prop_1032')

    # Read multiple (mix standard and proprietary)
    await bacnet.readMultiple('2:5 @obj_142 1 objectName @prop_1032')

Writes require the vendor classes to be imported so bacpypes3 knows the
datatype/encoding. If you still use the raw string form, include vendor_id::

   # Fire-and-forget write using numeric property id (after importing vendor classes)
   bacnet.write('2:5 device 5005 3653 true', vendor_id=5)

   # Await the write completion
   await bacnet._write('2:5 device 5005 3653 true', vendor_id=5)

Option B: Import vendor classes to use names
--------------------------------------------

If you prefer readable names instead of numeric IDs, import the vendor modules
once at startup. BAC0 exposes ready-to-import classes under
``BAC0.core.proprietary_objects``; the import registers VendorInfo and enables
named properties and object types.

Available re-exports include:

- Johnson Controls (vendor_id 5):
   ``JCIDeviceObject``, ``JciNetworkPortObject``,
   ``JCIAnalogInputObject``, ``JCIAnalogOutputObject``, ``JCIAnalogValueObject``
- PRIVA BV (vendor_id 105):
   ``PrivaBVDeviceObject``, ``PrivaNetworkPortObject``,
   ``PrivaBVAnalogInputObject``, ``PrivaBVAnalogOutputObject``,
   ``PrivaBVAnalogValueObject``
- Produal SyxthSense (vendor_id 651):
   ``Produal651Config``, ``Produal651ObjectType``, ``Produal651PropertyIdentifier``
- Produal Oy (vendor_id 783):
   ``Produal783Config1``, ``Produal783Config2``,
   ``Produal783ObjectType``, ``Produal783PropertyIdentifier``

Examples
........

Register JCI properties (import side effects), then read by name through a
device instance::

    from BAC0.core.proprietary_objects import JCIDeviceObject  # registers VendorInfo 5

    dev = await BAC0.device('2:5', 5005, bacnet)  # vendor_id discovered from device
    val = await dev.read_property('extended_proto_version')
    # same as numeric @prop_ usage but human readable

Produal (vendor_id 783) proprietary object and property names::

    from BAC0.core.proprietary_objects import (
          Produal783Config1, Produal783PropertyIdentifier,
    )  # registers VendorInfo 783

    dev = await BAC0.device('2:5', 1234, bacnet)
    # Read a property from a proprietary object type by name
    temp_sp_ll = await dev.read_property(('CONFIG1', 1, 'TEMPSP_LL'))

PRIVA BV proprietary property by name::

    from BAC0.core.proprietary_objects import PrivaBVDeviceObject  # registers VendorInfo 105

    dev = await BAC0.device('2:5', 9876, bacnet)
    desc = await dev.read_property('custom_description')

Tips
....

- Importing is sufficient; no explicit registration calls are required.
- If a property or object name isn’t recognized, fall back to the numeric
   style (``@obj_...``, ``@prop_...``).
- When using ``device.read_property(...)`` BAC0 automatically passes the
   device vendor_id to the underlying bacpypes3 read, so named properties work
   as soon as the vendor module was imported.
- For writes, bacpypes3 uses the device info cache to resolve the vendor. After
    importing vendor classes (required for proprietary writes), you can use either
    device-bound calls or raw strings. Passing ``vendor_id`` is optional and only
    needed if the cache hasn’t been populated yet.


Why not autodoc vendor modules here?
------------------------------------

Autodoc of vendor-specific modules tries to import and reflect all symbols,
which can break on environments that don’t have the corresponding devices or
when registrations differ. To keep this page reliable, we document the usage
patterns and provide import paths, without importing those modules during the
doc build.
