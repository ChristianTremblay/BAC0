#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""


def test_WriteAV(network_and_devices):
    test_device = network_and_devices.test_device
    old_value = test_device['ao0'].value
    test_device['ao0'] = 11.2
    new_value = test_device['ao0'].value
    assert (new_value - 11.2) < 0.01
    test_device['ao0'] = old_value
    new_value = test_device['ao0'].value
    assert (new_value - old_value) < 0.01
