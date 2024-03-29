#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""
import asyncio
import pytest

NEWCSVALUE = "New_Test"


@pytest.mark.asyncio
async def test_WriteAV(network_and_devices):
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        # Write to an object and validate new value is correct
        old_value = await test_device["AV"].value
        test_device["AV"] = 11.2
        await asyncio.sleep(1.5)  # or cache will play a trick on you
        new_value = await test_device["AV"].value
        assert (new_value - 11.2) < 0.01


@pytest.mark.asyncio
async def test_RelinquishDefault(network_and_devices):
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        test_device = test_device
        # Write to an object and validate new value is correct
        old_value = await test_device["AV"].value
        test_device["AV"].default(90)
        # time.sleep(1)
        new_value = await test_device["AV"].value
        assert (new_value - 90) < 0.01


@pytest.mark.asyncio
async def test_WriteCharStr(network_and_devices):
    # Write to an object and validate new value is correct
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        test_device = test_device
        test_device["CS_VALUE"] = NEWCSVALUE
        # time.sleep(1)
        new_value = await test_device["CS_VALUE"].value
        assert new_value == NEWCSVALUE


@pytest.mark.skip(
    "Not ready yet as BAC0 do not support out_of_service write -> unlocking PV"
)
async def test_SimulateAI(network_and_devices):
    # Write to an object and validate new value is correct
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        test_device["AI"] = 1
        # time.sleep(1)
        new_value = test_device["AI"].value
        assert test_device.read_property(("analogInput", 0, "outOfService"))
        # something is missing so pv can be written to if outOfService == True
        # assert new_value == 1


@pytest.mark.skip(
    "Not ready yet as BAC0 do not support out_of_service write -> unlocking PV"
)
async def test_RevertSimulation(network_and_devices):
    # Write to an object and validate new value is correct
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        test_device["AI"] = "auto"
        # time.sleep(1)
        new_value = test_device["AI"].value
        assert not test_device.read_property(("analogInput", 0, "outOfService"))
        assert (new_value - 99.9) < 0.01
