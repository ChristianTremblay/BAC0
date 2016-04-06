# -*- coding: utf-8 -*-
"""
Created on Tue Apr  5 21:01:02 2016

@author: CTremblay
"""

import BAC0
import time
import pytest

# Make a fixture to handle connection and close it when it's over
@pytest.fixture(scope='module')
def controller(request):
    print("Let's go !")
    bacnet = BAC0.connect()
    controller = BAC0.device('2:5', 5, bacnet)
    
    def terminate():
        controller.save()
        bacnet.disconnect()
        print("It's over")
    request.addfinalizer(terminate)
    return controller

def test_input1_is_greater_than_zero(controller):
    assert controller['nvoAI1'] > 0

def test_input2_equals_fifty(controller):
    assert controller['nvoAI2'] > 1000

#def test_stop_fan_and_check_status_is_off(controller):
#    controller['SF-C'] = False
#    time.sleep(2)
#    assert controller['SF-S'] == False

#def test_start_fan_and_check_status_is_on(controller):
#    controller['SF-C'] = True
#    time.sleep(2)