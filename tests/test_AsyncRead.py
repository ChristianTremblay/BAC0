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


async def test_read(event_loop, async_network_and_devices):
    test_device = async_network_and_devices.test_device

    async def test():
        assert (test_device["AV"] - CHANGE_DELTA_AV) < TOLERANCE

        assert await test_device["MSV"].value == 1
        assert test_device["BIG-ALARM"] == "Normal"

        assert await test_device["BV"].value == BINARY_TEST_STATE

        assert (test_device["AI"] - CHANGE_DELTA_AI) < TOLERANCE

        assert (test_device["AO"] - CHANGE_DELTA_AO) < TOLERANCE

        assert await test_device["BI"].value == BINARY_TEST_STATE

        assert await test_device["BO"].value == BINARY_TEST_STATE

        assert await test_device["CS_VALUE"].value == CHARACTERSTRINGVALUE

    event_loop.run_until_complete(test())
