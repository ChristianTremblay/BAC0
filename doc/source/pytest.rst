Using Pytest_
=============
Pytest_ [https://docs.pytest.org/en/latest/] is a "a mature full-featured Python testing tool".
It allows the creation of test files that can be called by a command line script, 
and run automatically while you work on something else.

For more details, please refer Pytest's documentation.


Some basic stuff before we begin
--------------------------------
Pytest is a very simple testing tool.  While, the default unit test tool for python is  
**unittest** (which is more formal and has more features); unittest can easily become 
too much for the needs of testing DDC controllers.

Pytest uses only simple the `assert` command, and locally defined functions.
It also allows the usage of "fixtures" which are little snippets of code that prepare things 
prior to the test (setUp), then finalize things when the test is over (tearDown).

The following example uses fixtures to establish the BACnet connection prior to the test, 
and then saves the controller histories and closes the connection after the tests are done.

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
If you name the file: test_mytest.py, you can just run ::

    py.test -v -s

Pytest_ will look for the test files, find them and run them. Or you can define the
exact file you want to run ::

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

Here's what a test failure looks like::

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

Note: I modified the test to generate an failure - nvoAI2 cannot exceed 1000.

Conclusion
----------
Using Pytest_ is a really good way to generate test files that can be reused and modified
depending on different use cases. It's a good way to run multiple tests at once.
It provides concise reports of every failure and tells you when your tests succeed.

.. _pytest : http://pytest.org/latest/
