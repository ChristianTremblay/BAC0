#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0

def test_ReadAV(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device['av0'] - 99.90) < 0.01

def test_ReadMV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device['mv0'].value == 1
    
def test_ReadBV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device['bv0'].value == 'active'
