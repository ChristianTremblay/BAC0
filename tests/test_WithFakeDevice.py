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
global bacnet
global device_app
global test_device

bacnet = BAC0.connect()
while not bacnet._started:
    time.sleep(0.1)
print('{}'.format(bacnet))

device_app = BAC0.lite(port=47809)
while not device_app._started:
    time.sleep(0.1)
print('{}'.format(device_app))

mv = create_MV(oid=1, name='mv', pv=1)
av = create_AV(oid=1, name='av', pv=99.9)

# Adding two object to the fake device
device_app.this_application.add_object(mv)
device_app.this_application.add_object(av)
print('Device App : {}'.format(device_app))

test_device = None


def test_DeviceCreation():
    global bacnet
    global test_device
    global device_app
    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    # Connect to test device using main network
    test_device = BAC0.device('{}:47809'.format(ip), boid, bacnet)


def test_ReadAV():
    global test_device
    print('{}'.format(test_device.points))
    print('{}'.format(test_device['av'].value))
    assert (test_device['av'] - 99.90) < 0.01


def test_ReadMV():
    global test_device
    assert test_device['mv'].value == 1


def test_disconnect():
    test_device.properties.network.disconnect()
    device_app.disconnect()
