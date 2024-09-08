#!/usr/BIn/env python
# -*- coding utf-8 -*-
from typing import AsyncGenerator
import pytest

"""
Test Bacnet communication with another device
"""

CHANGE_DELTA_AI = 99.90
CHANGE_DELTA_AO = 89.90
CHANGE_DELTA_AV = 79.90
TOLERANCE = 0.01
BINARY_TEST_STATE_STR1 = False
BINARY_TEST_STATE_STR2 = False
BINARY_TEST_STATE_BOOL = False
CHARACTERSTRINGVALUE = "test"


@pytest.mark.asyncio
async def test_ReadAnalog(network_and_devices: AsyncGenerator):
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources

        await test_device["AV"].value
        assert (test_device["AV"].lastValue - CHANGE_DELTA_AV) < TOLERANCE

        # assert not test_device["MSV"] == 1

        assert test_device["BIG-ALARM"] == "Normal"
        await test_device["AI"].value
        assert (test_device["AI"].lastValue - CHANGE_DELTA_AI) < TOLERANCE
        await test_device["AO"].value
        assert (test_device["AO"].lastValue - CHANGE_DELTA_AO) < TOLERANCE

        # assert test_device["CS_VALUE"] == CHARACTERSTRINGVALUE


@pytest.mark.asyncio
async def test_ReadBinary(network_and_devices: AsyncGenerator):
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        await test_device["BV-1"].value
        # assert test_device["BV-1"] is False
        print(test_device["BV-1"])
        # assert test_device["BV-1"] == BINARY_TEST_STATE
        # assert test_device["CS_VALUE"] == CHARACTERSTRINGVALUE
        assert test_device["BI"] == BINARY_TEST_STATE_STR1

        assert test_device["BO"] == BINARY_TEST_STATE_STR2
        assert test_device["BO-1"] == BINARY_TEST_STATE_BOOL
