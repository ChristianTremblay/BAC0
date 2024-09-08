import pytest

from BAC0.core.io.Write import write_pattern


@pytest.mark.parametrize(
    "req",
    [
        "303:5 binaryOutput:2132 presentValue inactive - 8",
        "192.168.1.149 binaryOutput:2132 presentValue inactive - 8",
        "303:5 binaryOutput 2132 presentValue inactive - 8",
        "303:5 @obj_142:2132 presentValue inactive - 8",
        "303:5 @obj_142:2132 @prop_345 inactive - 8",
        "303:5 @obj_142:2132 @prop_345 inactive",
        "303:5 binaryInput:1095 presentValue active",
        "303:5 analog-input 1095 presentValue 10.3",
        "303:5 analogInput:1095 presentValue 15.3",
        # "303:5 analogInput:1095",
        # "303:5 analog-input:1095",
        "303:5 analog-input 1095",
    ],
)
@pytest.mark.asyncio
async def test_pattern(network_and_devices, req):
    # async for resources in network_and_devices:
    # loop, bacnet, device_app, device30_app, test_device, test_device_30 = resources
    match = write_pattern.search(req)
    assert match is not None, f"Pattern did not match for request: {req}"
    address = match.group("address")
    objId = match.group("objId")
    prop_id = match.group("propId")
    value = match.group("value")
    indx = match.group("indx")
    priority = match.group("priority")
    assert address is not None, "Address not found"
    assert objId is not None, "Object ID not found"
    assert prop_id is not None, "Property ID not found"
    assert value is not None, "Value not found"
