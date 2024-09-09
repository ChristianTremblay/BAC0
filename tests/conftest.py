#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import asyncio
import os

import pytest
from pytest_asyncio import is_async_test

import BAC0
from BAC0.core.devices.local.factory import (
    ObjectFactory,
    analog_input,
    analog_output,
    analog_value,
    binary_input,
    binary_output,
    binary_value,
    character_string,
    date_value,
    datetime_value,
    make_state_text,
    multistate_input,
    multistate_output,
    multistate_value,
)

bacnet = None
device_app = None
device30_app = None
test_device = None
test_device_30 = None
# loop = asyncio.get_running_loop()


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


def add_points(qty_per_type, device):
    # Start from fresh
    ObjectFactory.clear_objects()
    basic_qty = qty_per_type - 1
    # Analog Inputs
    # Default... percent
    for _ in range(basic_qty):
        _new_objects = analog_input(presentValue=99.9)
        _new_objects = multistate_value(presentValue=1)

    # Supplemental with more details, for demonstration
    _new_objects = analog_input(
        name="ZN-T",
        properties={"units": "degreesCelsius"},
        description="Zone Temperature",
        presentValue=21,
    )

    states = make_state_text(["Normal", "Alarm", "Super Emergency"])
    _new_objects = multistate_value(
        description="An Alarm Value",
        properties={"stateText": states},
        name="BIG-ALARM",
        is_commandable=False,
    )

    # All others using default implementation
    for _ in range(qty_per_type):
        _new_objects = analog_output(presentValue=89.9)
        _new_objects = analog_value(presentValue=79.9)
        _new_objects = binary_input()
        _new_objects = binary_output()
        _new_objects = binary_value()
        _new_objects = multistate_input()
        _new_objects = multistate_output()
        _new_objects = date_value()
        _new_objects = datetime_value()
        _new_objects = character_string(presentValue="test")

    _new_objects.add_objects_to_application(device)


class NetworkAndDevices:
    def __init__(
        self, loop, bacnet, device_app, device30_app, test_device, test_device_30
    ):
        self.loop = loop
        self.bacnet = bacnet
        self.device_app = device_app
        self.device30_app = device30_app
        self.test_device = test_device
        self.test_device_30 = test_device_30

    def __repr__(self):
        return "NetworkAndDevices({!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.loop,
            self.bacnet,
            self.device_app,
            self.device30_app,
            self.test_device,
            self.test_device_30,
        )


@pytest.fixture(scope="session")
async def network_and_devices():
    global loop
    global bacnet
    global device_app
    global device30_app
    global test_device
    global test_device_30

    loop = asyncio.get_running_loop()
    # ip = os.getenv('RUNNER_IP')
    # if ip is not None:
    #    ip = f"{ip}/24"
    ip = "127.0.0.1/24"
    async with BAC0.start(ip=ip, localObjName="bacnet") as bacnet:
        # while bacnet._initialized is False:
        # await asyncio.sleep(1)
        async with BAC0.start(
            ip=ip, port=47809, localObjName="device_app"
        ) as device_app:
            # while device_app._initialized is False:
            # await asyncio.sleep(1)
            # await asyncio.sleep(2)
            add_points(2, device_app)
            # await asyncio.sleep(2)

            async with BAC0.start(
                ip=ip, port=47810, localObjName="device30_app"
            ) as device30_app:
                # while device30_app._initialized is False:
                # await asyncio.sleep(1)
                # await asyncio.sleep(5) # let all the objects be valid before continuing
                # await asyncio.sleep(2)
                add_points(5, device30_app)
                # await asyncio.sleep(2)
                # add_points(10, device300_app)

                ip = device_app.localIPAddr.addrTuple[0]
                boid = device_app.Boid

                ip_30 = device30_app.localIPAddr.addrTuple[0]
                boid_30 = device30_app.Boid
                # Connect to test device using main network
                test_device = await BAC0.device(
                    "{}:47809".format(ip), boid, bacnet, poll=10
                )
                test_device_30 = await BAC0.device(
                    "{}:47810".format(ip_30), boid_30, bacnet, poll=0
                )
                # t1 = test_device.creation_task
                # t2 = test_device_30.creation_task
                # await asyncio.gather(t1, t2)
                # Wait for the instances to be initialized
                net_and_dev = (
                    loop,
                    bacnet,
                    device_app,
                    device30_app,
                    test_device,
                    test_device_30,
                )
                try:
                    yield net_and_dev
                finally:
                    await test_device._disconnect(save_on_disconnect=False)
                    await test_device_30._disconnect(save_on_disconnect=False)
