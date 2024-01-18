import asyncio

from bacpypes3.apdu import SimpleAckPDU, WritePropertyRequest
from bacpypes3.app import Application
from bacpypes3.constructeddata import Any
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import CharacterString

from BAC0.core.app.asyncApp import BAC0Application
from BAC0.core.io.IOExceptions import NoResponseFromController, WritePropertyException
from BAC0.core.io.Read import find_reason


class TextMixin:
    """
    Mixin with functions to deal with text properties.
    Adding features to "network" itself.
    """

    def send_text_write_request(
        self, addr, obj_type, obj_inst, value, prop_id="description"
    ):
        request = self.build_text_write_request(
            addr=addr,
            obj_type=obj_type,
            obj_inst=obj_inst,
            value=value,
            prop_id=prop_id,
        )
        self.write_text_value(request)

    def build_text_write_request(
        self, addr, obj_type, obj_inst, value, prop_id="description"
    ):
        request = WritePropertyRequest(
            objectIdentifier=(obj_type, obj_inst), propertyIdentifier=prop_id
        )
        request.pduDestination = Address(addr)

        _value = Any()
        _value.cast_in(CharacterString(value))
        request.propertyValue = _value

        return request

    def write_text_value(self, request, timeout=10):
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        self._log.debug("{:>12} {}".format("- request:", request))

        _app.request(request)
