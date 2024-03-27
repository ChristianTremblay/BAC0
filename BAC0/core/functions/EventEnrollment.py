from bacpypes3.apdu import WritePropertyRequest
from bacpypes3.app import Application
from bacpypes3.basetypes import DeviceObjectPropertyReference, EventParameter
from bacpypes3.constructeddata import Any
from bacpypes3.pdu import Address

from BAC0.core.app.asyncApp import BAC0Application


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
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        self.log(f"{'- request:':>12} {request}", level="debug")

        _app.request(request)

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
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        self.log(f"{'- request:':>12} {request}", level="debug")

        _app.request(request)

        self._log.info(
            "Object Property Reference Write request sent to device : {request.pduDestination}"
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
