import asyncio
import random

from bacpypes3.primitivedata import Real

import BAC0
from BAC0.core.devices.local.factory import analog_value
from BAC0.scripts.script_runner import run

bacnet = None


async def main():
    async with BAC0.start() as bacnet:
        device = BAC0.start(port=47809, deviceId=123)

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
        av = dev["AV"]
        bacnet._log.info("Subscribing to AV")
        await dev["AV"].subscribe_cov(lifetime=90)

        while True:
            dev_av.presentValue = Real(random.randint(1, 100))
            bacnet._log.info(f"Setting AV to {dev_av.presentValue}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    run(main, bacnet)
