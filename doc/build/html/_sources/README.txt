.. BACØ documentation master file

BACØ is a Python 3 scripting application that uses BACpypes to process bacnet messages on a IP network. 
This library brings out simple commands to browse a bacnet network, read properties from bacnet devices or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled to bacnet, it becomes a great 
tool to test devices an interact with controllers.

Test driven development (TDD) for DDC controls
----------------------------------------------
BACØ allows users to simply test an application even if sensors are not connected to the controller. Using the out_of_service
property, it's easy to write a value to the input so the controller will think an input is conencted. 

Without a program like BACØ, you can rely on your DDC programming tool... but it is often slow and
every test must be done manually.

Now you can write your test and run them as often as you want.

How to use it
-------------

Example::

    import BAC0
    bacnet = ReadWriteScript()
    # Define a controller (this one is on MSTP #3, MAC addr 4, device ID 5504)    
    mycontroller = BAC0.device('3:4', 5504, bacnet)
    # Simulate an input (out_of_service -> true)
    # Use 1Ø as the value for pointName
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

Where to download
-----------------
http://christiantremblay.github.io/BAC0/

What you need
-------------
BACØ is based on BACpypes found here::

    git clone https://github.com/JoelBender/bacpypes.git

Bacpypes is now available for python 2.5, 2.7 and 3.4. You can also download it using Pypy.

You will also need Pandas as data processing is so easier with this !

If running Python on Windows, I recommend the use of complete distributions like Anaconda or Enthought Canopy.

How to install BACØ
-------------------
Once the repo has been cloned, use::

    python setup.py install

Demo in a Jupyter Notebook
--------------------------
When installed, module can be used to script communication with bacnet device.
Jupyter Notebooks are an excellent way to test it

https://github.com/ChristianTremblay/BAC0/blob/master/Jupyter/BAC0.ipynb
