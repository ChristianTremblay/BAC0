#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0

from BAC0.core.devices.create_objects import create_AV, create_MV, create_BV

@pytest.fixture(scope='session')
def network_and_devices():
    bacnet = BAC0.connect()

    device_app = BAC0.lite(port=47809)
    mv = create_MV(oid=1, name='mv', pv=1)
    av = create_AV(oid=1, name='av', pv=99.9)
    bv = create_BV(oid=1, name='bv', pv=1)

    # Adding objects to the fake device
    device_app.this_application.add_object(mv)
    device_app.this_application.add_object(av)
    device_app.this_application.add_object(bv)

    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    # Connect to test device using main network
    test_device = BAC0.device('{}:47809'.format(ip), boid, bacnet)

    yield (bacnet, device_app, test_device)
    # Close when done
    bacnet.disconnect()
    device_app.disconnect()

def test_ReadAV(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    assert (test_device['av'] - 99.90) < 0.01

def test_ReadMV(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    assert test_device['mv'].value == 1
    
def test_ReadBV(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    assert test_device['bv'].value == 'active'
