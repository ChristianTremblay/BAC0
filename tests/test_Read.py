#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

def test_ReadAV(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device['av0'] - 99.90) < 0.01

def test_ReadMV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device['mv0'].value == 1
    
def test_ReadBV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device['bv0'].value == 'active'

def test_ReadAI(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device['ai0'] - 99.90) < 0.01
    
def test_ReadAO(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device['ao0'] - 99.90) < 0.01
    
def test_ReadBI(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device['bi0'].value == 'active'
    
def test_ReadBO(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device['bo0'].value == 'active'