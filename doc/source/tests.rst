Testing and simulating with BAC0
================================

BAC0 is a powerful BAS test tool.  With it you can easily build tests scripts, and by 
using its **assert** syntax, you can make your DDC code stronger.


Using Assert and other commands
-------------------------------
Let's say your BAC controller **sequence of operation** is really simple. Something like this::

    System stopped:
        When system is stopped, fan must be off, 
        dampers must be closed, heater cannot operate.

    System started:
        When system starts, fan command will be on. 
        Dampers will open to minimum position.
        If fan status turns on, heating sequence will start.

And so on...

How would I test that ?
-----------------------

Assuming:
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

You can define any test you want.  As complex as you want.  You will use more precise conditions
instead of a simple time.sleep() function - most likely you will read a point value that tells 
you when the actual mode is active.

You can then add tests for the various temperature ranges; and build functions to simulate discharge air
temperature depending on the heating or cooling stages... it's all up to you!


Using tasks to automate simulation
==================================

Polling
-------
Let's say you want to poll a point every 5 seconds to see how the point reacted.::

    mycontroller['point_name'].poll(delay=5)

Note: by default, polling is enabled on all points at a 10 second frequency. But you could 
    define a controller without polling and do specific point polling. ::

    mycontroller = BAC0.device('2:5',5,bacnet,poll=0)
    mycontroller['point_name'].poll(delay=5)

Match
-----
Let's say you want to automatically match the status of a point with it's command to 
find times when it is reacting to conditions other than what you expected.::

    mycontroller['status'].match(mycontroller['command'])


Custom function
---------------
You could also define a complex function, and send that to the controller. 
This way, you'll be able to continue using all synchronous functions of Jupyter Notebook for example.
(technically, a large function will block any inputs until it's finished)

.. note:: THIS IS A WORK IN PROGRESS

Example ::

    import time
    
    def test_Vernier():
        for each in range(0,101):
            controller['Vernier Sim'] = each
            print('Sending : %2f' % each)
            time.sleep(30)
            
    controller.do(test_Vernier)

This function updates the variable named "Vernier Sim" each 30 seconds; incrementing by 1 percent.
This will take a really long time to finish.  So instead, use the "do" method, and the function 
will be run is a separate thread so you are free to continue working on the device, while the 
function commands the controller's point.
