import asyncio
import random

from bacpypes3.primitivedata import Real

import BAC0
from BAC0.core.devices.local.factory import analog_value
from BAC0.scripts.script_runner import run

bacnet = None


async def main():
    async with BAC0.start() as bacnet:
        async with BAC0.start(port=47809, deviceId=123) as device:

            new_obj = analog_value(presentValue=0)
            new_obj.add_objects_to_application(device)

            # From Server
            dev_av = device.this_application.app.get_object_name("AV")
            print(dev_av.covIncrement)

            # From client
            ip = device.localIPAddr.addrTuple[0]
            boid = device.Boid
            bacnet._log.info("Defining device with poll 0 so the AV won't get updated")
            dev = await BAC0.device(f"{ip}:47809", boid, bacnet, poll=0)
            bacnet._log.info("Subscribing to AV")


            def my_point_callback(property_identifier, property_value):
                print(f"CALLBACK {property_identifier}: {property_value}")

            await dev["AV"].subscribe_cov(lifetime=90, callback=my_point_callback)

            while True:
                dev_av.presentValue = Real(random.randint(1, 100))
                bacnet._log.info(f"Setting AV to {dev_av.presentValue}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    run(main, bacnet)
