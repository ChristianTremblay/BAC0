#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""
import os.path

import BAC0


def test_SaveToSQL(network_and_devices):
    test_device = network_and_devices.test_device
    test_device_30 = network_and_devices.test_device_30
    # test_device_300 = network_and_devices.test_device_300
    test_device.save()
    test_device_30.save(filename="obj30.db")
    # test_device_300.save(filename="obj300")
    assert os.path.isfile("{}.db".format(test_device.properties.db_name))
    assert os.path.isfile("{}.db".format("obj30"))
    # assert os.path.isfile("{}.db".format("obj300"))


def test_disconnection_of_device(network_and_devices):
    test_device = network_and_devices.test_device
    test_device_30 = network_and_devices.test_device_30
    test_network = network_and_devices.bacnet
    # test_device_300 = network_and_devices.test_device_300
    test_device.disconnect()
    test_device_30.disconnect()
    # test_device_300.save(filename="obj300")
    assert isinstance(test_device, BAC0.core.devices.Device.DeviceFromDB)
    assert isinstance(test_device_30, BAC0.core.devices.Device.DeviceFromDB)
    # assert os.path.isfile("{}.db".format("obj300"))
    test_device.connect(network=test_network)
    test_device_30.connect(network=test_network)
    assert isinstance(test_device, BAC0.core.devices.Device.RPMDeviceConnected)
    assert isinstance(test_device_30, BAC0.core.devices.Device.RPMDeviceConnected)
