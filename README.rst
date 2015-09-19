.. BAC0 documentation master file

BAC0 is a Python 3 scripting application that uses BACpypes to process bacnet messages on a IP network. 
This library brings out simple commands to browse a bacnet network, read properties from bacnet devices or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled to bacnet, it becomes a great 
tool to test devices an interact with controllers.

Test driven development (TDD) for DDC controls
----------------------------------------------
BAC0 allows users to simply test an application even if sensors are not connected to the controller. Using the out_of_service
property, it's easy to write a value to the input so the controller will think an input is conencted. 

Without a program like BAC0, you can rely on your DDC programming tool... but it is often slow and
every test must be done manually.

Now you can write your test and run them as often as you want.

How to use it
-------------

Example::

    import BAC0
    bacnet = BAC0.ReadWriteScript()

    # Define a controller (this one is on MSTP #3, MAC addr 4, device ID 5504)    
    mycontroller = BAC0.device('3:4', 5504, bacnet)

    # Simulate an input (out_of_service -> true)
    # Use 10 as the value for pointName
    mycontroller.sim('pointName 10')

    # Release the simulation
    mycontroller.release('pointName')

    # Release all simulated points
    mycontroller.releaseAll()

    # Write to a point
    mycontroller.write('pointName active')

    # Write to relinquish default
    mycontroller.default('pointName 120')

    # Read
    mycontroller.read('pointName can be more than one word')

Now you can build simple tests using assert syntax for example and make your DDC code stronger.

Assert ?
--------
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
***********************
Controller is defined and its variable name is mycontroller
Fan command = SF-C
Fan Status = SF-S
Dampers command = MAD-O
Heater = RH-O
Occupancy command = OCC-SCHEDULE

System Stopped Test Code::

    mycontroller.write('OCC-SCHEDULE Unoccupied')
    time.sleep(10)
    assert mycontroller.read('SF-C').value() == 'Off'
    assert mycontroller.read('MAD-O').value() == 0
    assert mycontroller.read('RH-O').value() == 0

    # Simulate fan status as SF-C is Off
    mycontroller.sim('SF-S Off')

Sytstem Started Test Code::

    mycontroller.write('OCC-SCHEDULE Occupied')
    time.sleep(10)
    assert mycontroller.read('SF-C').value() == 'On'
    # Give status
    mycontroller.sim('SF-S On')
    time.sleep(15)
    assert mycontroller.read('MAD-O') == mycontroller.read('MADMIN-POS')

And so on...

You are now able to define any test you want. You will probably use more precise conditions
instead of time.sleep() function (example read a value that tells actual mode is active)

You can then test random temperature values, build functions that will simulate discharge air
temperature depending on heatign or cooling stages... it's up to you !

Where to download
-----------------
http://christiantremblay.github.io/BAC0/

What you need
-------------
BAC0 is based on BACpypes found here::

    git clone https://github.com/JoelBender/bacpypes.git

Bacpypes is now available for python 2.5, 2.7 and 3.4. You can also download it using Pypy.

You will also need Pandas as data processing is so easier with this !

If running Python on Windows, I recommend the use of complete distributions like Anaconda or Enthought Canopy.

How to install BAC0
-------------------
Once the repo has been cloned, use::

    python setup.py install

Demo in a Jupyter Notebook
--------------------------
When installed, module can be used to script communication with bacnet device.
Jupyter Notebooks are an excellent way to test it

https://github.com/ChristianTremblay/BAC0/blob/master/Jupyter/BAC0.ipynb
