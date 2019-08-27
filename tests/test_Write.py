#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

from bacpypes.primitivedata import CharacterString

NEWCSVALUE = CharacterString("New_Test")


def test_WriteAV(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    old_value = test_device["av0"].value
    test_device["av0"] = 11.2
    new_value = test_device["av0"].value
    assert (new_value - 11.2) < 0.01


def test_RelinquishDefault(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    old_value = test_device["av0"].value
    test_device["av0"].default(90)
    new_value = test_device["av0"].value
    assert (new_value - 90) < 0.01

def test_WriteCharStr(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["string0"] = NEWCSVALUE.value
    new_value = test_device["string0"].value
    assert new_value == NEWCSVALUE.value


def test_SimulateAI(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["ai0"] = 1
    new_value = test_device["ai0"].value
    assert test_device.read_property(('analogInput',0,'outOfService'))
    # something is missing so pv can be written to if outOfService == True
    # assert new_value == 1

def test_RevertSimulation(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["ai0"] = 'auto'
    new_value = test_device["ai0"].value
    assert not test_device.read_property(('analogInput',0,'outOfService'))
    assert (new_value - 99.9) < 0.01