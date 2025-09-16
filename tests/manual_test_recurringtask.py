import asyncio
import random

import BAC0
from BAC0.tasks.RecurringTask import RecurringTask
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
    # Configuration
    # # Initialize BACnet
    print(BAC0.infos.__version__)

    async with BAC0.start(ip="127.0.0.1/24", deviceId=111) as bacnet:
        async with BAC0.start(ip="127.0.0.1/24:47809", deviceId=222) as fake_device:
            add_points(1, fake_device)

            await asyncio.sleep(2)
            fake_from_bacnet = await BAC0.device('127.0.0.1/24:47809', 222, bacnet)

            async def read_task():
                #bacnet._log.info("Reading Task")
                await fake_from_bacnet["ZN-T"].value

            async def write_task():
                #bacnet._log.info("Writing Task")
                fake_device["ZN-T"].presentValue = random.randint(15, 30)

            

            for _ in range(100):
                t = RecurringTask(read_task, delay=5, name="Read ZN-T", minimum_delay=0)
                t.start()
                t2 = RecurringTask(write_task, delay=5, name="Write ZN-T", minimum_delay=0)
                t2.start()

            while True:
                await asyncio.sleep(5)
                #bacnet._log.info(t)
                #bacnet._log.info(t2)
                #bacnet._log.info(Task.tasks)
                bacnet._log.info(f"\nt.previous_execution: {t.last_time}, \nt.next_execution: {t.next_time}, \nt.average_latency: {t.average_latency}, \nt.average_execution_delay: {t.average_execution_delay}")


if __name__ == "__main__":
    # run(main, bacnet) # Run the script and deals with SIGINT and SIGTERM, useful for long time runnign scripts.
    asyncio.run(main())
