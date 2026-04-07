#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""
import asyncio
import pytest
from typing import AsyncGenerator

NEWCSVALUE = "New_Test"


@pytest.mark.asyncio(loop_scope="session")
async def test_WriteAV(network_and_devices: AsyncGenerator):
    loop, bacnet, device_app, device30_app, test_device, test_device_30 = (
        network_and_devices
    )
    # Write to an object and validate new value is correct
    old_value = await test_device["AV"].value #noqa F841
    await test_device["AV"]._set(11.2)
    await asyncio.sleep(0.5)
    test_device["AV"]._cache["_previous_read"] = (None, None) # to speed up test by skipping cache, else we are limited by the 5 seconds
    new_value = await test_device["AV"].value
    assert (new_value - 11.2) < 0.01


@pytest.mark.asyncio(loop_scope="session")
async def test_RelinquishDefault(network_and_devices: AsyncGenerator):
    loop, bacnet, device_app, device30_app, test_device, test_device_30 = (
        network_and_devices
    )
    # Write to an object and validate new value is correct
    old_value = await test_device["AV"].value #noqa F841
    await test_device["AV"].default(90)
    test_device["AV"]._cache["_previous_read"] = (None, None) # to speed up test by skipping cache, else we are limited by the 5 seconds
    new_value = await test_device["AV"].value
    assert (new_value - 90) < 0.01


@pytest.mark.asyncio(loop_scope="session")
async def test_WriteCharStr(network_and_devices: AsyncGenerator):
    # Write to an object and validate new value is correct
    loop, bacnet, device_app, device30_app, test_device, test_device_30 = (
        network_and_devices
    )
    char_point_name = next(
        (name for name in test_device.points_name if name.startswith("CS_VALUE")),
        None,
    )
    if char_point_name is None:
        pytest.skip("Character string point not discovered on this stack/version")
    await test_device[char_point_name]._set(NEWCSVALUE)
    test_device[char_point_name]._cache["_previous_read"] = (None, None) # to speed up test by skipping cache, else we are limited by the 5 seconds
    new_value = await test_device[char_point_name].value
    assert new_value == NEWCSVALUE


@pytest.mark.skip(
    "Not ready yet as BAC0 do not support out_of_service write -> unlocking PV"
)
async def test_SimulateAI(network_and_devices: AsyncGenerator):
    # Write to an object and validate new value is correct
    loop, bacnet, device_app, device30_app, test_device, test_device_30 = (
        network_and_devices
    )
    test_device["AI"] = 1
    # time.sleep(1)
    new_value = await test_device["AI"].value #noqa F841
    assert test_device.read_property(("analogInput", 0, "outOfService"))
    # something is missing so pv can be written to if outOfService is True
    # assert new_value == 1


@pytest.mark.skip(
    "Not ready yet as BAC0 do not support out_of_service write -> unlocking PV"
)
async def test_RevertSimulation(network_and_devices: AsyncGenerator):
    # Write to an object and validate new value is correct
    loop, bacnet, device_app, device30_app, test_device, test_device_30 = (
        network_and_devices
    )
    test_device["AI"] = "auto"
    # time.sleep(1)
    new_value = await test_device["AI"].value #noqa F841
    assert not test_device.read_property(("analogInput", 0, "outOfService"))
    assert (new_value - 99.9) < 0.01
