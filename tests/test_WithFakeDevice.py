#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0
import time

from BAC0.core.devices.create_objects import create_AV, create_MV

# We'll need a device


@pytest.fixture
def network_and_devices():
    bacnet = BAC0.connect()
    while not bacnet._started:
        time.sleep(0.1)
    # print('{}'.format(bacnet))

    device_app = BAC0.lite(port=47809)
    while not device_app._started:
        time.sleep(0.1)
    # print('{}'.format(device_app))

    mv = create_MV(oid=1, name='mv', pv=1)
    av = create_AV(oid=1, name='av', pv=99.9)

    # Adding two object to the fake device
    device_app.this_application.add_object(mv)
    device_app.this_application.add_object(av)
    #print('Device App : {}'.format(device_app))

    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    # Connect to test device using main network
    test_device = BAC0.device('{}:47809'.format(ip), boid, bacnet)

    return (bacnet, device_app, test_device)


def test_ReadAV(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    print('{}'.format(test_device.points))
    print('{}'.format(test_device['av'].value))
    assert (test_device['av'] - 99.90) < 0.01
    bacnet.disconnect()
    device_app.disconnect()


def test_ReadMV(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    assert test_device['mv'].value == 1
    bacnet.disconnect()
    device_app.disconnect()
