import asyncio
import random

import BAC0
from BAC0.core.devices.local.factory import (
    ObjectFactory,
    analog_input,
    analog_value,
    binary_input,
    binary_output,
    binary_value,
    character_string,
    date_value,
    datetime_value,
    make_state_text,
    multistate_input,
    multistate_output,
    multistate_value,
)
from BAC0.scripts.script_runner import run

bacnet = None


def add_points(qty_per_type, device):
    # Start from fresh
    ObjectFactory.clear_objects()
    basic_qty = qty_per_type - 1
    # Analog Inputs
    # Default... percent
    for _ in range(basic_qty):
        _new_objects = analog_input(presentValue=99.9)
        # _new_objects = multistate_value(presentValue=1,is_commandable=False)

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
        is_commandable=False,
    )

    # All others using default implementation
    for _ in range(qty_per_type):
        # _new_objects = analog_output(presentValue=89.9)
        _new_objects = analog_value(presentValue=79.9, is_commandable=True)
        _new_objects = binary_input()
        _new_objects = binary_output()
        _new_objects = binary_value()
        _new_objects = multistate_input()
        _new_objects = multistate_output()
        _new_objects = date_value()
        _new_objects = datetime_value()
        _new_objects = character_string(presentValue="test")

    _new_objects.add_objects_to_application(device)


async def main():
    # We'll use 3 devices plus our main instance
    async with BAC0.start(localObjName="bacnet") as bacnet:
        async with BAC0.start(port=47809, localObjName="App1") as device_app:
            async with BAC0.start(port=47810, localObjName="App2") as device30_app:
                async with BAC0.start(port=47811, localObjName="App3") as device300_app:
                    add_points(2, device_app)
                    add_points(3, device30_app)
                    add_points(4, device300_app)

                    ip = device_app.localIPAddr.addrTuple[0]
                    boid = device_app.Boid

                    ip_30 = device30_app.localIPAddr.addrTuple[0]
                    boid_30 = device30_app.Boid

                    ip_300 = device300_app.localIPAddr.addrTuple[0]
                    boid_300 = device300_app.Boid

                    # Connect to test device using main network
                    test_device = await BAC0.device(
                        f"{ip}:47809", boid, bacnet, poll=10
                    )
                    test_device_30 = await BAC0.device(
                        f"{ip_30}:47810", boid_30, bacnet, poll=0
                    )
                    test_device_300 = await BAC0.device(
                        f"{ip_300}:47811", boid_300, bacnet, poll=0
                    )
                    bacnet._log.info("CTRL-C to exit")

                    while True:
                        await asyncio.sleep(2)
                        bacnet._log.info(f"{test_device['BIG-ALARM']}")
                        new_val_for_av1 = random.randint(1, 100)
                        bacnet._log.info(f"Setting AV-1 to {new_val_for_av1}")
                        # test_device_30['AV-1'] = new_val_for_av1
                        await test_device_30["AV-1"].write(new_val_for_av1, priority=16)
                        await asyncio.sleep(2)
                        bacnet._log.info(
                            f"Forcing a read on test_device_30/AV-1 : {await test_device_30['AV-1'].value}"
                        )
                        test_device_300["AV-1"] = new_val_for_av1
                        await asyncio.sleep(2)
                        bacnet._log.info(
                            f"Forcing a read on test_device_300/AV-1 : {await test_device_300['AV-1'].value}"
                        )
                        # (test_device_300.points)


if __name__ == "__main__":
    run(main, bacnet)
    # asyncio.run(main())
