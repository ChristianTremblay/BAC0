from bacpypes.apdu import SimpleAckPDU, WritePropertyRequest
from bacpypes.basetypes import DeviceObjectPropertyReference, EventParameter
from bacpypes.constructeddata import Any
from bacpypes.core import deferred
from bacpypes.iocb import IOCB
from bacpypes.pdu import Address

from ..io.IOExceptions import NoResponseFromController
from ..io.Read import find_reason


# this class follows the same design as schedule/calendar
class EventEnrollment:
    def __make_event_parameters_request(
        self, destination, object_instance, event_parameters
    ):
        request = WritePropertyRequest(
            objectIdentifier=("eventEnrollment", object_instance),
            propertyIdentifier="eventParameters",
        )

        address = Address(destination)
        request.pduDestination = address
        request.propertyValue = Any()
        request.propertyValue.cast_in(event_parameters)
        request.priority = 15
        return request

    def __send_event_parameters_request(self, request, timeout=10):
        iocb = IOCB(request)
        iocb.set_timeout(timeout)
        deferred(self.this_application.request_io, iocb)

        iocb.wait()

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self.log("Not an ack, see debug for more infos.", level='warning')
                self.log(f"Not an ack. | APDU : {apdu} / {type(apdu)}", level='debug')
                return
        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController(f"APDU Abort Reason : {reason}")

        self._log.info(
            f"Event Parameters Write request sent to device : {request.pduDestination}"
        )

    # external interface
    def write_event_parameters(
        self, destination, event_enrollment_instance, event_parameters
    ):
        if type(event_parameters) is not EventParameter:
            self.log.warning("Data is not of type EventParameter.")
            return

        request = self.__make_event_parameters_request(
            destination=destination,
            object_instance=event_enrollment_instance,
            event_parameters=event_parameters,
        )
        self.__send_event_parameters_request(request)

    def __make_obj_prop_ref_request(self, destination, object_instance, obj_prop_ref):
        request = WritePropertyRequest(
            objectIdentifier=("eventEnrollment", object_instance),
            propertyIdentifier="objectPropertyReference",
        )

        address = Address(destination)
        request.pduDestination = address
        request.propertyValue = Any()
        request.propertyValue.cast_in(obj_prop_ref)
        request.priority = 15
        return request

    def __send_obj_prop_ref_request(self, request, timeout=10):
        iocb = IOCB(request)
        iocb.set_timeout(timeout)
        deferred(self.this_application.request_io, iocb)

        iocb.wait()

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self.log("Not an ack, see debug for more infos.", level='warning')
                self.log(
                    f"Not an ack. | APDU : {apdu} / {type(apdu)}", level='debug'
                )
                return
        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController(f"APDU Abort Reason : {reason}")

        self._log.info(
            "Object Property Reference Write request sent to device : {}".format(
                request.pduDestination
            )
        )

    # external interface
    def write_obj_prop_ref(self, destination, event_enrollment_instance, obj_prop_ref):
        if type(obj_prop_ref) is not DeviceObjectPropertyReference:
            self.log.warning("Data is not of type ObjectPropertyReference.")
            return

        request = self.__make_obj_prop_ref_request(
            destination=destination,
            object_instance=event_enrollment_instance,
            obj_prop_ref=obj_prop_ref,
        )
        self.__send_obj_prop_ref_request(request)
