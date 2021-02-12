from bacpypes.iocb import IOCB
from bacpypes.core import deferred
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU
from bacpypes.primitivedata import CharacterString
from bacpypes.constructeddata import Any
from bacpypes.pdu import Address
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
        try:
            iocb = IOCB(request)
            iocb.set_timeout(timeout)
            # pass to the BACnet stack
            deferred(self.this_application.request_io, iocb)

            iocb.wait()  # Wait for BACnet response

            if iocb.ioResponse:  # successful response
                apdu = iocb.ioResponse

                if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                    self._log.error("Not an ack, see debug for more infos.")
                    return

            if iocb.ioError:  # unsuccessful: error/reject/abort
                apdu = iocb.ioError
                reason = find_reason(apdu)
                raise NoResponseFromController("APDU Abort Reason : {}".format(reason))

        except WritePropertyException as error:
            # construction error
            self._log.error(("exception: {!r}".format(error)))
