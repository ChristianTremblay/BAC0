Write to network
===================
Write is very similar to read in term of concept. You typically want to write a value to a 
property which is part of an object.

So to write to the `presentValue` of an analogValue (if we keep the same object than in the read chapter)
will need you to tell BAC0 to which address you want to write, which object, at what instance and what property, 
just like when you read.

But you also need to provide supplemental information :

  - what value you want to write
  - what priority 

priority
----------
In BACnet, object to which we can write often provide what is called the `priorityArray`.
This array contains 16 levels to which we can write (1 being the highest priority). 

Typical usage of priority is :

    1	Manual-Life Safety
    2	Automatic-Life Safety
    3	Available
    4	Available
    5	Critical Equipment Control
    6	Minimum On/Off
    7	Available
    8	Manual Operator (Override)
    9	Available
    10	Available (Typical Control from a Supervisor)
    11	Available
    12	Available
    13	Available
    14	Available
    15	Available (Schedule)
    16	Available


Write to a simple property
---------------------------
To write to a single property ::

    bacnet.write('address object object_instance property value - priority')

Write to multiple properties
-------------------------------
Write property multiple is also implemented. You will need to build a list for your requets ::

    r = ['analogValue 1 presentValue 100','analogValue 2 presentValue 100','analogValue 3 presentValue 100 - 8','@obj_142 1 @prop_1042 True']
    bacnet.writeMultiple(addr='2:5',args=r,vendor_id=842)
    
..note::
    WARNING. See the section on Proprietary objects and properties for details about vendor_id and @obj_142.


.. _berryconda : https://github.com/jjhelmus/berryconda  
.. _RaspberryPi : http://www.raspberrypi.org
