#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import time
from collections import namedtuple

import pytest

import BAC0
from BAC0.core.devices.local.models import (
    analog_input,
    analog_output,
    analog_value,
    binary_input,
    binary_output,
    binary_value,
    character_string,
    date_value,
    datetime_value,
    humidity_input,
    humidity_value,
    make_state_text,
    multistate_input,
    multistate_output,
    multistate_value,
    temperature_input,
    temperature_value,
)
from BAC0.core.devices.local.object import ObjectFactory


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
        is_commandable=True,
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
        _new_objects = character_string(presentValue="test", is_commandable=True)

    _new_objects.add_objects_to_application(device)


@pytest.fixture(scope="session")
def network_and_devices():

    # This is the BACnet network and the "client" instance used to interact with
    # devices that will be created.
    bacnet = BAC0.lite()

    # We'll use 3 devices with our first instance
    device_app = BAC0.lite(port=47809, deviceId=101)
    device30_app = BAC0.lite(port=47810, deviceId=102)
    # device300_app = BAC0.lite(port=47811, deviceId=103)

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
