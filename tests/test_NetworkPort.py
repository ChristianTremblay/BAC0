import pytest

import BAC0
from bacpypes3.primitivedata import ObjectIdentifier
from bacpypes3.service.object import read_property_to_result_element


@pytest.mark.asyncio
async def test_missing_fd_bbmd_address_is_encoded_as_property_error():
    async with BAC0.start(ip="127.0.0.1/24", port=47820) as bacnet:
        network_port = bacnet.this_application.app.get_object_id(
            ObjectIdentifier("network-port,1")
        )

        result = await read_property_to_result_element(
            network_port, "fdBBMDAddress"
        )

        error = result.readResult.propertyAccessError
        assert str(error.errorClass) == "property"
        assert str(error.errorCode) == "unknown-property"


@pytest.mark.asyncio
async def test_fd_bbmd_address_is_available_in_foreign_mode():
    async with BAC0.start(
        ip="127.0.0.1/24",
        port=47821,
        bbmdAddress="127.0.0.1:47808",
        bbmdTTL=60,
    ) as bacnet:
        network_port = bacnet.this_application.app.get_object_id(
            ObjectIdentifier("network-port,1")
        )

        result = await read_property_to_result_element(
            network_port, "fdBBMDAddress"
        )

        assert result.readResult.propertyAccessError is None
        assert result.readResult.propertyValue is not None
