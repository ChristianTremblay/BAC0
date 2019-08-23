#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""


def test_WriteAV(network_and_devices):
    # Write to an object and validate new value is correct
    test_device = network_and_devices.test_device
    old_value = test_device["av0"].value
    test_device["av0"] = 11.2
    new_value = test_device["av0"].value
    assert (new_value - 11.2) < 0.01
