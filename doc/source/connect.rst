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


Writing to Points
-----------------

Simple write
************
If point is a value:

    * analogValue (AV)
    * binaryValue (BV)
    * multistateValue (MV) 
    
You can change its value with a simple assignment.  BAC0 will write the value to the object's 
**presentValue** at the default priority.::

    mycontroller['point_name'] = 23 

.. image:: images/AV_write.png


Write to an Output (Override)
*****************************
If the point is an output:

    * analogOutput (AO) 
    * binaryOutput (BO) 
    * multistateOutput (MO)

You can change its value with a simple assignment.  BAC0 will write the value to the object's 
**presentValue** (a.k.a override it) at priority 8 (Manual Operator).::

    mycontroller['outputName'] = 45

.. image:: images/AO_write.png


Write to an Input (simulate)
****************************
If the point is an input:

    * analogInput (AI) 
    * binaryOutput (BO) 
    * multistateOutput (MO) 

You can change its value with a simple assigment, thus overriding any external value it is 
reading and simulating a different sensor reading.  The override occurs because  
BAC0 sets the point's **out_of_service** (On) and then writes to the point's **presentValue**.
 
    mycontroller['inputName'] = <simulated value>

    mycontroller['Temperature'] = 23.5      # overiding actual reading of 18.8 C

.. image:: images/AI_override.png


Releasing an Input simulation or Output override
*************************************************

To return control of an Input or Output back to the controller, it needs to be released.
Releasing a point returns it automatic control.  This is done with an assignment to 'auto'.::

    mycontroller['pointToRelease'] = 'auto'

.. image:: images/AI_auto.png
.. image:: images/AO_auto.png

    
Setting a Relinquish_Default
****************************
When a point (with a priority array) is released of all override commands, it takes on the value 
of its **Relinquish_Default**. [BACnet clause 12.4.12]  If you wish to set this default value, 
you may with this command::

    mycontroller['pointToChange'].default(<value>)
    mycontroller['Output'].default(75)

.. image:: images/AO_set_default.png

