#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import asyncio
import time
from collections import namedtuple

import pytest
import pytest_asyncio

import BAC0

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_network_and_devices(event_loop):
    assert event_loop is asyncio.get_running_loop()
    # This is the BACnet network and the "client" instance used to interact with
    # devices that will be created.
    bacnet = BAC0.Async()

    # We'll use 3 devices with our first instance
    device_app = BAC0.Async(port=47809, deviceId=101)
    device30_app = BAC0.Async(port=47810, deviceId=102)
    # device300_app = BAC0.lite(port=47811, deviceId=103)
    # time.sleep(0.01)

    add_points(2, device_app)
    add_points(5, device30_app)
    # add_points(10, device300_app)

    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    ip_30 = device30_app.localIPAddr.addrTuple[0]
    boid_30 = device30_app.Boid

    # ip_300 = device300_app.localIPAddr.addrTuple[0]
    # boid_300 = device300_app.Boid

    # Connect to test device using main network
    test_device = BAC0.ADevice("{}:47809".format(ip), boid, bacnet, poll=10)
    test_device_30 = BAC0.ADevice("{}:47810".format(ip_30), boid_30, bacnet, poll=0)
    # test_device_300 = BAC0.device("{}:47811".format(ip_300), boid_300, bacnet, poll=0)

    params = namedtuple(
        "devices",
        ["bacnet", "device_app", "test_device", "test_device_30", "test_device_300"],
    )
    params.bacnet = bacnet
    params.device_app = device_app
    params.test_device = test_device
    params.test_device_30 = test_device_30
    # params.test_device_300 = test_device_300

    yield params

    # Close when done
    params.test_device.disconnect()
    params.test_device_30.disconnect()
    # params.test_device_300.disconnect()

    params.bacnet.disconnect()
    # If too quick, we may encounter socket issues...


"""
@pytest.fixture(scope="session")
def network_and_devices():
    # This is the BACnet network and the "client" instance used to interact with
    # devices that will be created.
    bacnet = BAC0.lite()

    # We'll use 3 devices with our first instance
    device_app = BAC0.lite(port=47809, deviceId=101)
    device30_app = BAC0.lite(port=47810, deviceId=102)
    # device300_app = BAC0.lite(port=47811, deviceId=103)
    # time.sleep(0.01)

    add_points(2, device_app)
    add_points(5, device30_app)
    # add_points(10, device300_app)

    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    ip_30 = device30_app.localIPAddr.addrTuple[0]
    boid_30 = device30_app.Boid

    # ip_300 = device300_app.localIPAddr.addrTuple[0]
    # boid_300 = device300_app.Boid

    # Connect to test device using main network
    test_device = BAC0.device("{}:47809".format(ip), boid, bacnet, poll=10)
    test_device_30 = BAC0.device("{}:47810".format(ip_30), boid_30, bacnet, poll=0)
    # test_device_300 = BAC0.device("{}:47811".format(ip_300), boid_300, bacnet, poll=0)

    params = namedtuple(
        "devices",
        ["bacnet", "device_app", "test_device", "test_device_30", "test_device_300"],
    )
    params.bacnet = bacnet
    params.device_app = device_app
    params.test_device = test_device
    params.test_device_30 = test_device_30
    # params.test_device_300 = test_device_300

    yield params

    # Close when done
    params.test_device.disconnect()
    params.test_device_30.disconnect()
    # params.test_device_300.disconnect()

    params.bacnet.disconnect()
    # If too quick, we may encounter socket issues...
    time.sleep(1)
"""
