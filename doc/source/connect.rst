How to connect to a device and interact with points
===================================================
Define a bacnet network and a controller
----------------------------------------
Example::

    import BAC0
    bacnet = BAC0.connect()
    # or specify the IP you want to use / bacnet = BAC0.connect(ip='192.168.1.10')
    # by default, it will attempt an internet connection and use the network adapter
    # connected to the internet.

    # Define a controller (this one is on MSTP #3, MAC addr 4, device ID 5504)    
    mycontroller = BAC0.device('3:4', 5504, bacnet)


Look for points in controller
-----------------------------

Example::

    mycontroller.points

Read the value of a point
--------------------------
To read a point, simply ask for it using bracket syntax::

    mycontroller['point_name']

Write to a point
----------------
simple write
************
If point is a analogValue, binaryValue or a multistateValue BAC0 will write to the default
priority ::

    mycontroller['point_name'] = 10 

Relinquish default
******************
If you must write to relinquish default, it must be said explicitly ::

    mycontroller['pointToChange'].default(10)

This distinction is made because of the sensibility to multiple writes to those values.
Thoses are often written to EEPROM directly and have a ±250000 write cycle.

Override
*********
If the point is a output, BAC0 will override it (@priority 8)::

    mycontroller['outputName'] = 100

simulate (out_of_service)
**************************
If the point is an input, BAC0 will set the out_of_service flag to On and write 
to the present value (which will simulate it)::

    mycontroller['inputName'] = 34

Releasing a simulation or an override
**************************************
Simply affect 'auto' to the point ::

    mycontroller['pointToRelease'] = 'auto'