BAC0 |build-status| |coverage| |docs|
=====================================
BAC0 is a Python 3 (3.4 and later) scripting application that uses BACpypes_ to process BACnet messages on a IP network. 
This library exposes simple functions to browse the BACnet network, and read & write properties from the BACnet devices.

Python is a simple language to learn and a very powerful tool for data processing. Coupled with BACnet, 
it becomes a **great tool for testing BACnet** and interacting with BACnet controllers.

BAC0 takes its name from the default IP port assigned to BACnet/IP communications - port (47808 decimal, 0xBAC0 
hexadecimal).

Test driven development (TDD) for DDC controls
==============================================
BAC0 is intended for assisting BAS (building automation system) programmers, with configuring, testing, and 
commissioning of BAS Controllers - often called DDC (Direct Digital Control) Controllers.

Typically BAS controllers are programmed using vendor specific tools, and vendor specific programming languages 
to define how they will operate.  The resulting programs are the controller's **sequence of operations**.  
Different vendors, use different methods to define these sequences - including 'block programming', 
'graphical programming', and 'text/procedural programming'.  

BAC0 provides a generalized (vendor-independent) means to programmatically interact with the BAS controllers, 
via Python and the BACnet/IP communication protocol.  BAC0 allows users to test a controller even if no sensors 
or outputs are connected to the controller.  Thanks to the BACnet **out_of_service** property, it is easy to write 
a value to the input pin(s) so the controller believes a sensor is connected, and its **operating sequence** will 
respond accordingly.  Likewise, it is possible to write a value to an output pin(s) to operate any connected 
equipment (often called a **manual command** or to **override an output**).  In fact, BAC0 exposes a great many of a  
controller's BACnet Objects and Object Properties, enabling automated interactions using Python; as a simple 
scripting language, a powerful testing & commissioning tool, or a general application development environment.

Using BAC0 as test tool, makes automated BAS testing quick, reliable, and repeatable.  Compare this to 
the BAS vendor provided tools, which only allow the controllers to be programmed, and where all the 
testing must be done manually.  Very slow.  Very error-prone.  Now you can write your tests and re-run them 
as often as you need.


Better commissioning thanks to automatic data logging
=====================================================
As you will discover, when you define a controller in BAC0, you automatically get **historical data logs** for  
every variable in the controller.  All I/O points are trended every 10 seconds (by default).  Meaning 
you can do data analysis of the controller's operation while you're doing your basic **sequence testing**. 
This gives you a high-level overview of the controller's performance while highlighting trouble areas really fast.

BAC0 is not only a good tool for testing your **sequence of operations** while in-the-office.
It is also a really good tool to assist on-site.  Use it to test controller startup, operation, and balancing 
in-the-field.  When combined with Jupyter Notebook, you are even able to create nice looking reports right from your 
automation code.


.. |build-status| image:: https://travis-ci.org/ChristianTremblay/BAC0.svg?branch=master
   :target: https://travis-ci.org/ChristianTremblay/BAC0
   :alt: Build status
     
.. |docs| image:: https://readthedocs.org/projects/bac0/badge/?version=latest
   :target: http://bac0.readthedocs.org/
   :alt: Documentation
   
.. |coverage| image:: https://coveralls.io/repos/ChristianTremblay/BAC0/badge.svg?branch=master&service=github 
   :target: https://coveralls.io/github/ChristianTremblay/BAC0?branch=master
   :alt: Coverage

.. _bacpypes : https://github.com/JoelBender/bacpypes

.. _bokeh : http://www.bokehplots.com
