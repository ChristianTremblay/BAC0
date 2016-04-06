Using Pytest_
=============
Pytest_ is a "a mature full-featured Python testing tool".
It allows the creation of test files that can be called by a command line script.
It's then possible to create different test, all in there own file start 
the process and work on something else while tests are running.

Here an example of a Pytest_ module that could be created.

Please note that Pytest_ on its own is a very complete solution. For more documentation about 
it, please refer to the documentation of the project.

I'll simply describe minimal feature I present in the example.

Some basic stuff before we begin
--------------------------------
Pytest is a very simple testing tool. The default unit test tool for python is called 
unittest. Based on Java xUnit, it's more formal, uses a lot of different functions and classes... 
It can easily become too much for the needs of testing DDC controllers.

Pytest uses only simple `assert` command, inside functions defined in a module.

Pytest also allows the usage of "fixtures" which are little snippets of code that will be
used to prepare what's needed for the test, then finalize the process when it's over. In unittest, 
thoses functions are called setUp and tearDown.

In the example module I'll show you, I'm using fixtures to create the BACnet connection at the beginning 
of the test, making this connection valid for all the tests in the module, then closing the connection
after the tests have been done, just after having saved the controller so the histories be available.

Example
+++++++

Code ::

    import BAC0
    import time
    import pytest

    # Make a fixture to handle connection and close it when it's over
    @pytest.fixture(scope='module')
    def bacnet_network(request):
        print("Let's go !")
        bacnet = BAC0.connect()
        controller = BAC0.device('2:5', 5, bacnet)
        
        def terminate():
            controller.save()
            bacnet.disconnect()
            print('It's over')
        request.addfinalizer(terminate)
        return controller

    def test_input1_is_greater_than_zero(bacnet_network):
        assert controller['nvoAI1'] > 0

    def test_input2_equals_fifty(bacnet_network):
        assert controller['nvoAI2'] > 0

    def test_stop_fan_and_check_status_is_off(bacnet_network):
        controller['SF-C'] = False
        time.sleep(2)
        assert controller['SF-S'] == False
    
    def test_start_fan_and_check_status_is_on(controller):
        controller['SF-C'] = True
        time.sleep(2)
        assert controller['SF-S'] == True

Success result
..............
If you named you file test_mytest.py, you can just run ::

    py.test -v -s

Pytest_ will look for test files, find them and run them. Or you can define the
file you want to run ::

    py.test mytestfile.py -v -s

Here's what it looks like ::

    ============================= test session starts =============================
    platform win32 -- Python 3.4.4, pytest-2.8.5, py-1.4.31, pluggy-0.3.1 -- C:\User
    s\ctremblay.SERVISYS\AppData\Local\Continuum\Anaconda3\python.exe
    cachedir: .cache
    rootdir: c:\0Programmes\Github\BAC0, inifile:
    plugins: bdd-2.16.1, cov-2.2.1, pep8-1.0.6
    collected 2 items
    
    pytest_example.py::test_input1_is_greater_than_zero Let's go !
    Using ip : 192.168.210.95
    Starting app...
    App started
    Starting Bokeh Serve
    Click here to open Live Trending Web Page
    http://localhost:5006/?bokeh-session-id=um2kEfnM97alVOr3GRu5xt07hvQItkruMVUUDpsh
    S8Ha
    Changing device state to <class 'BAC0.core.devices.Device.DeviceDisconnected'>
    Changing device state to <class 'BAC0.core.devices.Device.RPMDeviceConnected'>
    Found FX14 0005... building points list
    Failed running bokeh.bat serve
    Bokeh server already running
    Ready!
    Polling started, every values read each 10 seconds
    PASSED
    pytest_example.py::test_input2_equals_fifty PASSEDFile exists, appending data...
    
    FX14 0005 saved to disk
    Stopping app
    App stopped
    It's over
    
    
    ========================== 2 passed in 27.94 seconds ==========================

Failure result
..............

Here's what it looks like when a test fails ::

    ============================= test session starts =============================
    platform win32 -- Python 3.4.4, pytest-2.8.5, py-1.4.31, pluggy-0.3.1 -- C:\User
    s\ctremblay.SERVISYS\AppData\Local\Continuum\Anaconda3\python.exe
    cachedir: .cache
    rootdir: c:\0Programmes\Github\BAC0, inifile:
    plugins: bdd-2.16.1, cov-2.2.1, pep8-1.0.6
    collected 2 items
    
    pytest_example.py::test_input1_is_greater_than_zero Let's go !
    Using ip : 192.168.210.95
    Starting app...
    App started
    Starting Bokeh Serve
    Click here to open Live Trending Web Page
    http://localhost:5006/?bokeh-session-id=TKgDiRoCkut2iobSFRlWGA2nhJlPCtXU3ZTWL3cC
    nxRI
    Changing device state to <class 'BAC0.core.devices.Device.DeviceDisconnected'>
    Changing device state to <class 'BAC0.core.devices.Device.RPMDeviceConnected'>
    Found FX14 0005... building points list
    Failed running bokeh.bat serve
    Bokeh server already running
    Ready!
    Polling started, every values read each 10 seconds
    PASSED
    pytest_example.py::test_input2_equals_fifty FAILEDFile exists, appending data...
    
    FX14 0005 saved to disk
    Stopping app
    App stopped
    It's over
    
    
    ================================== FAILURES ===================================
    __________________________ test_input2_equals_fifty ___________________________
    
    controller = FX14 0005 / Connected
    
        def test_input2_equals_fifty(controller):
    >       assert controller['nvoAI2'] > 1000
    E       assert nvoAI2 : 20.58 degreesCelsius > 1000
    
    pytest_example.py:30: AssertionError
    ===================== 1 failed, 1 passed in 30.71 seconds =====================

I modified the test here to generate an failure if nvoAI2 is not greater than 1000.

Conclusion
----------
Using Pytest_ is a really good way to generate test files that can be reused and modified
depending on different use cases. It's a good way to run multiple tests at once.
It will give you a concise report of every failure and tell you if tests succeeded.

.. _pytest : http://pytest.org/latest/