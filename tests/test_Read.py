#!/usr/BIn/env python
# -*- coding utf-8 -*-
import pytest

"""
Test Bacnet communication with another device
"""

CHANGE_DELTA_AI = 99.90
CHANGE_DELTA_AO = 89.90
CHANGE_DELTA_AV = 79.90
TOLERANCE = 0.01
BINARY_TEST_STATE = "inactive"
CHARACTERSTRINGVALUE = "test"


@pytest.mark.asyncio
def test_ReadAV(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device["AV"] - CHANGE_DELTA_AV) < TOLERANCE


@pytest.mark.asyncio
def test_ReadMV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["MSV"].value == 1
    assert test_device["BIG-ALARM"] == "Normal"


@pytest.mark.asyncio
def test_ReadBV(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["BV"].value == BINARY_TEST_STATE


@pytest.mark.asyncio
def test_ReadAI(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device["AI"] - CHANGE_DELTA_AI) < TOLERANCE


@pytest.mark.asyncio
def test_ReadAO(network_and_devices):
    test_device = network_and_devices.test_device
    assert (test_device["AO"] - CHANGE_DELTA_AO) < TOLERANCE


@pytest.mark.asyncio
def test_ReadBI(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["BI"].value == BINARY_TEST_STATE


@pytest.mark.asyncio
def test_ReadBO(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["BO"].value == BINARY_TEST_STATE


@pytest.mark.asyncio
def test_ReadCharacterstringValue(network_and_devices):
    test_device = network_and_devices.test_device
    assert test_device["CS_VALUE"].value == CHARACTERSTRINGVALUE
