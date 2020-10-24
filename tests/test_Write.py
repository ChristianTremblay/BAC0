#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

from bacpypes.primitivedata import CharacterString
import time

NEWCSVALUE = CharacterString("New_Test")


def test_WriteAV(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    old_value = test_device["AV"].value
    test_device["AV"] = 11.2
    # time.sleep(1)
    new_value = test_device["AV"].value
    assert (new_value - 11.2) < 0.01


def test_RelinquishDefault(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    old_value = test_device["AV"].value
    test_device["AV"].default(90)
    # time.sleep(1)
    new_value = test_device["AV"].value
    assert (new_value - 90) < 0.01


def test_WriteCharStr(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["CS_VALUE"] = NEWCSVALUE.value
    # time.sleep(1)
    new_value = test_device["CS_VALUE"].value
    assert new_value == NEWCSVALUE.value


def test_SimulateAI(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["AI"] = 1
    # time.sleep(1)
    new_value = test_device["AI"].value
    assert test_device.read_property(("analogInput", 0, "outOfService"))
    # something is missing so pv can be written to if outOfService == True
    # assert new_value == 1


def test_RevertSimulation(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["AI"] = "auto"
    # time.sleep(1)
    new_value = test_device["AI"].value
    assert not test_device.read_property(("analogInput", 0, "outOfService"))
    assert (new_value - 99.9) < 0.01
