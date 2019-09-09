#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

CHANGE_DELTA = 99.90
TOLERANCE = 0.01
BINARY_TEST_STATE = "active"
CHARACTERSTRINGVALUE = "test"


def test_ReadAV(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device["av0"] - CHANGE_DELTA) < TOLERANCE


def test_ReadMV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["mv0"].value == 1


def test_ReadBV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["bv0"].value == BINARY_TEST_STATE


def test_ReadAI(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device["ai0"] - CHANGE_DELTA) < TOLERANCE


def test_ReadAO(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device["ao0"] - CHANGE_DELTA) < TOLERANCE


def test_ReadBI(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["bi0"].value == BINARY_TEST_STATE


def test_ReadBO(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["bo0"].value == BINARY_TEST_STATE


def test_ReadCharacterstringValue(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["string0"].value == CHARACTERSTRINGVALUE
