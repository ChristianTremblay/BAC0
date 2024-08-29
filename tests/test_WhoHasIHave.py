#!/usr/bin/env python
import pytest


@pytest.mark.asyncio
async def test_WhoHas(network_and_devices):
    # Write to an object and validate new value is correct
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
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
