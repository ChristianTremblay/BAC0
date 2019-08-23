#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0

from BAC0.core.devices.create_objects import (
    create_AV,
    create_MV,
    create_BV,
    create_AI,
    create_BI,
    create_AO,
    create_BO,
    create_CharStrValue,
)

from collections import namedtuple
import time

from bacpypes.primitivedata import CharacterString
from bacpypes.basetypes import EngineeringUnits


@pytest.fixture(scope="session")
def network_and_devices():
    bacnet = BAC0.lite()

    def _add_points(qty, device):
        # Add a lot of points for tests (segmentation required)
        mvs = []
        avs = []
        bvs = []
        ais = []
        bis = []
        aos = []
        bos = []
        charstr = []

        for i in range(qty):
            mvs.append(create_MV(oid=i, name="mv{}".format(i), pv=1, pv_writable=True))
            new_av = create_AV(oid=i, name="av{}".format(i), pv=99.9, pv_writable=True)
            new_av.units = EngineeringUnits.enumerations["degreesCelsius"]
            new_av.description = "Fake Description {}".format(i)
            avs.append(new_av)
            bvs.append(create_BV(oid=i, name="bv{}".format(i), pv=1, pv_writable=True))
            ais.append(create_AI(oid=i, name="ai{}".format(i), pv=99.9))
            aos.append(create_AO(oid=i, name="ao{}".format(i), pv=99.9))
            bis.append(create_BI(oid=i, name="bi{}".format(i), pv=1))
            bos.append(create_BO(oid=i, name="bo{}".format(i), pv=1))
            charstr.append(
                create_CharStrValue(
                    oid=i,
                    name="string{}".format(i),
                    pv=CharacterString("test"),
                    pv_writable=True,
                )
            )

        for mv in mvs:
            device.this_application.add_object(mv)
        for av in avs:
            device.this_application.add_object(av)
        for bv in bvs:
            device.this_application.add_object(bv)
        for ai in ais:
            device.this_application.add_object(ai)
        for ao in aos:
            device.this_application.add_object(ao)
        for bi in bis:
            device.this_application.add_object(bi)
        for bo in bos:
            device.this_application.add_object(bo)
        for cs in charstr:
            device.this_application.add_object(cs)

    # We'll use 3 devices with our first instance
    device_app = BAC0.lite(port=47809)
    device30_app = BAC0.lite(port=47810)
    device300_app = BAC0.lite(port=47811)

    _add_points(1, device_app)
    _add_points(10, device30_app)
    _add_points(30, device300_app)

    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    ip_30 = device30_app.localIPAddr.addrTuple[0]
    boid_30 = device30_app.Boid

    ip_300 = device300_app.localIPAddr.addrTuple[0]
    boid_300 = device300_app.Boid

    # Connect to test device using main network
    test_device = BAC0.device("{}:47809".format(ip), boid, bacnet, poll=10)
    test_device_30 = BAC0.device("{}:47810".format(ip_30), boid_30, bacnet, poll=0)
    test_device_300 = BAC0.device("{}:47811".format(ip_300), boid_300, bacnet, poll=0)

    params = namedtuple(
        "devices",
        ["bacnet", "device_app", "test_device", "test_device_30", "test_device_300"],
    )
    params.bacnet = bacnet
    params.device_app = device_app
    params.test_device = test_device
    params.test_device_30 = test_device_30
    params.test_device_300 = test_device_300

    yield params

    # Close when done
    params.test_device.disconnect()
    params.test_device_30.disconnect()
    params.test_device_300.disconnect()

    params.bacnet.disconnect()
    # If too quick, we may encounter socket issues...
    time.sleep(1)
