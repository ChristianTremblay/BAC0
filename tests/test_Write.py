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


def test_WriteCharStr(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    test_device["string0"] = NEWCSVALUE.value
    new_value = test_device["string0"].value
    assert new_value == NEWCSVALUE.value
