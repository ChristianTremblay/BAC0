#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacpypes version
"""
import pytest
import bacpypes3


@pytest.mark.asyncio
async def test_BacpypesVersion(network_and_devices):
    """
    The version format gives 3 parts and I would want for example
    17.5 being smaller than 17.100
    I'll trick the numbers in a way that will cover "most cases"
    Counting patch divided by 1000 should be enough.
    For comparison, 17.5 becomes 17.005
    """
    async for resources in network_and_devices:
        loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
        maj, minor, patch = bacpypes3.__version__.split(".")
        version = float(maj) * 1000000 + float(minor) + float(patch) / 1000
        assert version >= 0.083
