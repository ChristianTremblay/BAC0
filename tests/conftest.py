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

from bacpypes.primitivedata import CharacterString, Date, Time, Real, Boolean, Integer
from bacpypes.basetypes import EngineeringUnits, BinaryPV

from bacpypes.local.object import (
    AnalogOutputCmdObject,
    AnalogValueCmdObject,
    BinaryOutputCmdObject,
    BinaryValueCmdObject,
    MultiStateValueCmdObject,
    CharacterStringValueCmdObject,
)

from bacpypes.object import (
    MultiStateValueObject,
    AnalogValueObject,
    BinaryValueObject,
    AnalogInputObject,
    BinaryInputObject,
    AnalogOutputObject,
    BinaryOutputObject,
    CharacterStringValueObject,
    DateTimeValueObject,
    Property,
    register_object_type,
)
from bacpypes.constructeddata import ArrayOf


@pytest.fixture(scope="session")
def network_and_devices():
    bacnet = BAC0.lite()

    # Register class to activate behaviours
    register_object_type(AnalogOutputCmdObject, vendor_id=842)
    register_object_type(AnalogValueCmdObject, vendor_id=842)
    register_object_type(BinaryOutputCmdObject, vendor_id=842)
    register_object_type(BinaryValueCmdObject, vendor_id=842)
    register_object_type(MultiStateValueCmdObject, vendor_id=842)

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
            states = ["red", "green", "blue"]
            new_mv = MultiStateValueCmdObject(
                objectIdentifier=("multiStateValue", i),
                objectName="mv{}".format(i),
                presentValue=1,
                numberOfStates=len(states),
                stateText=ArrayOf(CharacterString)(states),
                description=CharacterString(
                    "MultiState Value Description {}".format(i)
                ),
            )
            new_mv.add_property(
                Property("relinquishDefault", Integer, default=0, mutable=True)
            )
            mvs.append(new_mv)

            new_av = AnalogValueCmdObject(
                objectIdentifier=("analogValue", i),
                objectName="av{}".format(i),
                presentValue=99.9,
                description=CharacterString("AnalogValue Description {}".format(i)),
                units=EngineeringUnits.enumerations["degreesCelsius"],
            )
            new_av.add_property(
                Property("relinquishDefault", Real, default=0, mutable=True)
            )
            avs.append(new_av)

            new_bv = BinaryValueCmdObject(
                objectIdentifier=("binaryValue", i),
                objectName="bv{}".format(i),
                presentValue="active",
                description=CharacterString("Binary Value Description {}".format(i)),
            )
            new_bv.add_property(
                Property(
                    "relinquishDefault", BinaryPV, default="inactive", mutable=True
                )
            )
            bvs.append(new_bv)

            new_ai = AnalogInputObject(
                objectIdentifier=i,
                objectName="ai{}".format(i),
                presentValue=99.9,
                units=EngineeringUnits.enumerations["percent"],
                description=CharacterString("AnalogInput Description {}".format(i)),
            )
            new_ai.add_property(
                Property("outOfService", Boolean, default=False, mutable=True)
            )
            ais.append(new_ai)

            new_ao = AnalogOutputCmdObject(
                objectIdentifier=("analogOutput", i),
                objectName="ao{}".format(i),
                presentValue=99.9,
                units=EngineeringUnits.enumerations["percent"],
                description=CharacterString("AnalogOutput Description {}".format(i)),
            )
            aos.append(new_ao)

            new_bi = BinaryInputObject(
                objectIdentifier=i,
                objectName="bi{}".format(i),
                presentValue="active",
                description=CharacterString("BinaryInput Description {}".format(i)),
            )
            new_bi.add_property(
                Property("outOfService", Boolean, default=False, mutable=True)
            )
            bis.append(new_bi)

            bos.append(
                BinaryOutputCmdObject(
                    objectIdentifier=("binaryOutput", i),
                    objectName="bo{}".format(i),
                    presentValue="active",
                    description=CharacterString(
                        "BinaryOutput Description {}".format(i)
                    ),
                )
            )
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
