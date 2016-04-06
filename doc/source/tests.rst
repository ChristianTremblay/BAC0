Testing and simulating with BAC0
================================
Now you can build simple tests using assert syntax for example and make your DDC code stronger.

Using Assert and other commands
-------------------------------
Let's say your sequence is really simple. Something like this : 

System stopped
--------------
When system is stopped, fan must be off, dampers must be closed, heater cannot operate.

System started
--------------
When system starts, fan command will be on. Dampers will open to minimum position.
If fan status turns on, heating sequence will starts.

And so on...

How would I test that ?
-----------------------
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

Using tasks to automate simulation
==================================
Polling
-------
Let's say you want to poll a point every 5 seconds to see later how the point reacted.::

    mycontroller['point_name'].poll(delay=5)

Note that by default, polling is on for every points every 10 seconds. But you could have
define a controller without polling and do specific polling.::

    mycontroller = BAC0.device('2:5',5,bacnet,poll=0)
    mycontroller['point_name'].poll(delay=5)

Match
-----
Let's say you want to automatically match the status of a point with the command.::

    mycontroller['status'].match(mycontroller['command'])

Custom function
---------------
You could also define a complex function, and send it to the controller. 
This way, you'll be able to continue using all synchronous functions of Jupyter Notebook for example.
(technically, a large function will block any inputs until it's finished)

PLEASE NOTE THAT THIS IS A WORK IN PROGRESS

Example ::

    import time
    
    def test_Vernier():
        for each in range(0,101):
            controller['Vernier Sim'] = each
            print('Sending : %2f' % each)
            time.sleep(30)
            
    controller.do(test_Vernier)

This function updates the variable named "Vernier Sim" each 30 seconds. By increment of 1 percent.
It will take a really long time to finish. Using the "do" method, you send the function to the controller
and it will be handled by a thread so you'll be able to continue working on the device.