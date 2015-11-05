BAC0 |build-status| |coverage| |docs|
=====================================
BAC0 is a Python 3 (3.4 and over) scripting application that uses bacpypes_ to process bacnet messages on a IP network. 
This library brings out simple commands to browse a bacnet network, read properties from bacnet devices or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled to bacnet, it becomes a great 
tool to test devices an interact with controllers.

Test driven development (TDD) for DDC controls
==============================================
BAC0 allows users to simply test an application even if sensors are not connected to the controller. Using the out_of_service
property, it's easy to write a value to the input so the controller will think an input is conencted. 

Without a program like BAC0, you can rely on your DDC programming tool... but it is often slow and
every test must be done manually.

Now you can write your test and run them as often as you want.

How to use it
=============

Example::

    import BAC0
    bacnet = BAC0.connect()
    # or specify the IP you want to use / bacnet = BAC0.connect(ip='192.168.1.10')

    # Define a controller (this one is on MSTP #3, MAC addr 4, device ID 5504)    
    mycontroller = BAC0.device('3:4', 5504, bacnet)

    """
    Access point value
    """
    mycontroller['point_name']

    """
    Write to point value
    If the point is an analog/multistate or binary value, it will try to write to the present value.
    If this fails, it'll try with the relinquish default
    
    If the point is an input of some kind, it'll try a simulation which is :
        - write out_of_service = True
        - write to the present_value

    If the point is an output of some kind, it'll override the point writing
    to priority 8
    """
    mycontroller['point_name'] = value

    """
    Automatic history
    Each time a point is read or written to, the value is added to a history
    table (a pandas Series). You can then easily see what happened to the 
    point while your were making tests.

    It's also easy to plot the result
    """
    his = mycontroller['point_name'].history
    his.plot(ylim=[0,100])

Now you can build simple tests using assert syntax for example and make your DDC code stronger.

Assert ?
========
Let's say your sequence is really simple. Something like this : 

System stopped
==============
When system is stopped, fan must be off, dampers must be closed, heater cannot operate.

System started
==============
When system starts, fan command will be on. Dampers will open to minimum position.
If fan status turns on, heating sequence will starts.

And so on...

How would I test that ?
=======================
* Controller is defined and its variable name is mycontroller
* fan command = SF-C
* Fan Status = SF-S
* Dampers command = MAD-O
* Heater = RH-O
* Occupancy command = OCC-SCHEDULE

System Stopped Test Code::

    mycontroller['OCC-SCHEDULE'] = Unoccupied
    time.sleep(10)
    assert mycontroller['SF-C'] == False
    assert mycontroller['MAD-O'] == 0
    assert mycontroller['RH-O'] == 0

    # Simulate fan status as SF-C is Off
    mycontroller['SF-S'] = 'Off'

Sytstem Started Test Code::

    mycontroller['OCC-SCHEDULE'] = 'Occupied'
    time.sleep(10)
    assert mycontroller['SF-C'] == 'On'
    # Give status
    mycontroller['SF-S'] = 'On'
    time.sleep(15)
    assert mycontroller['MAD-O'] == mycontroller['MADMIN-POS']

And so on...

You are now able to define any test you want. You will probably use more precise conditions
instead of time.sleep() function (example read a value that tells actual mode is active)

You can then test random temperature values, build functions that will simulate discharge air
temperature depending on heatign or cooling stages... it's up to you !

Tasks
=====
POLLING
Let's say you want to poll a point every 5 seconds to see later how the point reacted.

mycontroller['point_name'].poll(delay=5)

MATCH
Let's say you want to automatically match the status of a point with the command

mycontroller['status'].match(mycontroller['command'])

Access a historyTable::
    
    controller['nvoAI1'].history

Result example ::

    controller['nvoAI1'].history
    Out[8]:
    2015-09-20 21:41:37.093985    21.740000
    2015-09-20 21:42:23.672387    21.790001
    2015-09-20 21:42:34.358801    21.790001
    2015-09-20 21:42:45.841596    21.790001
    2015-09-20 21:42:56.308144    21.790001
    2015-09-20 21:43:06.897034    21.790001
    2015-09-20 21:43:17.593321    21.790001
    2015-09-20 21:43:28.087180    21.790001
    2015-09-20 21:43:38.597702    21.790001
    2015-09-20 21:43:48.815317    21.790001
    2015-09-20 21:44:00.353144    21.790001
    2015-09-20 21:44:10.871324    21.790001

Show a chart::

    controller['nvoAI1'].history.plot()

Where to download
=================
https://github.com/ChristianTremblay/BAC0/

What you need
=============
BAC0 is based on BACpypes found here::

    git clone https://github.com/JoelBender/bacpypes.git

Bacpypes is now available for python 2.5, 2.7 and 3.4. You can also download it using Pypy.

You will also need Pandas as data processing is so easier with this !

If running Python on Windows, I recommend the use of complete distributions like Anaconda or Enthought Canopy.

How to install BAC0
===================
Once the repo has been cloned, use::

    python setup.py install

Demo in a Jupyter Notebook
==========================
When installed, module can be used to script communication with bacnet device.
Jupyter Notebooks are an excellent way to test it

https://github.com/ChristianTremblay/BAC0/blob/master/Jupyter/BAC0.ipynb
http://bac0.readthedocs.org/en/latest/
https://readthedocs.org/projects/bac0/
Doc
===
http://bac0.readthedocs.org/en/latest/
https://travis-ci.org/ChristianTremblay/BAC0

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
