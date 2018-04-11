Proprietary Objects
====================

Some manufacturers provide special variables inside their controllers in the
form of proprietary objects. BAC0 support the creation of those objects but
some work is needed on your side to register them.

By default, BAC0 implements the Supervisor Online variable for TEC3000

Example ::

    from BAC0.core.proprietary_objects.jci import TECSupOnline, register
    register(TECSupOnline)
    bacnet.read('216:9 device 521609 3653', vendor_id=5)
    # or
    bacnet.write('216:9 device 521609 3653 true', vendor_id=5)

.. note:: 
    In future version it will be able to define special device and attach some
    proprietary objects to them so tec['SupOnline'] would work...
