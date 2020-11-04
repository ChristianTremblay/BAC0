#!/usr/bin/env python

import pytest


def test_WhoHas(network_and_devices):
    # Write to an object and validate new value is correct
    bacnet = network_and_devices.bacnet
    test_device = network_and_devices.test_device
    response = bacnet.whohas(
        "analogInput:0", destination="{}".format(test_device.properties.address)
    )
    assert response
    # response = bacnet.whohas("analogInput:0", global_broadcast=True)
    # assert response
    # response = bacnet.whohas("analogInput:0")
    # assert response
    # Can't work as I'm using different ports to have multiple devices using the same IP....
    # So neither local or global broadcast will give result here
