import pytest
import re


@pytest.mark.parametrize(
    "req",
    [
        "303:5 binaryOutput:2132 presentValue inactive - 8",
        "192.168.1.149 binaryOutput:2132 presentValue inactive - 8",
        "303:5 binaryOutput 2132 presentValue inactive - 8",
        "303:5 @obj_142:2132 presentValue inactive - 8",
        "303:5 @obj_142:2132 @prop_345 inactive - 8",
        "303:5 @obj_142:2132 @prop_345 inactive",
        "303:5 binary-input 1095 presentValue active",
    ],
)
def test_pattern(req):
    pattern = r"(?P<address>\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b|(\b\d+:\d+\b)) (?P<objId>(@obj_)?[-\w]*[: ]*\d*) (?P<propId>(@prop_)?\w*) (?P<value>\w*)[ ]?(?P<indx>-|\d*)?[ ]?(?P<priority>(1[0-6]|[0-9]))?"
    match = re.search(pattern, req)
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
