#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0

from BAC0.core.devices.create_objects import create_AV, create_MV, create_BV
    

def test_ReadAV(network_and_devices):
    test_device = network_and_devices.test_device_30
    assert (test_device['av3'] - 99.90) < 0.01

def test_ReadMV(network_and_devices):
    test_device = network_and_devices.test_device_30
    assert test_device['mv5'].value == 1
    
def test_ReadBV(network_and_devices):
    test_device = network_and_devices.test_device_30
    assert test_device['bv9'].value == 'active'
