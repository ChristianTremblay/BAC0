#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0
import os.path
import os

from BAC0.core.devices.create_objects import create_AV, create_MV, create_BV


@pytest.fixture(scope='session')
def network_and_devices():
    bacnet = BAC0.lite()

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

    # Delete db and bin files created
#    os.remove('{}.db'.format(test_device.properties.db_name))
#    os.remove('{}.bin'.format(test_device.properties.db_name))

    # Close when done
    test_device.disconnect()
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


def test_SaveToSQL(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    test_device.save()

    assert os.path.isfile('{}.db'.format(test_device.properties.db_name))
    assert os.path.isfile('{}.bin'.format(test_device.properties.db_name))


def test_LoadFromSQL(network_and_devices):
    bacnet, device_app, test_device = network_and_devices
    file = '{}.db'.format(test_device.properties.db_name)
    bck_dev = BAC0.device(from_backup=file)
    assert bck_dev.properties.objects_list == test_device.properties.objects_list

    assert (bck_dev['av'].history[-1:].iloc[0] - 99.9) < 0.01
