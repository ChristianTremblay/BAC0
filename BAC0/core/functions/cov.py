from bacpypes.apdu import SubscribeCOVRequest, SimpleAckPDU, RejectPDU, AbortPDU
from bacpypes.iocb import IOCB
from bacpypes.core import deferred
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.constructeddata import Array
from bacpypes.primitivedata import Tag, ObjectIdentifier, Unsigned

from BAC0.core.io.Read import cast_datatype_from_tag

"""

using cov, we build a "context" which is turned into a subscription being sent to 
the destination.

Once the IOCB is over, the callback attached to it will execute (subscription_acknowledged)
and we'll get the answer

"""


class SubscriptionContext:
    next_proc_id = 1

    def __init__(self, address, objectID, confirmed=None, lifetime=None):
        self.address = address
        self.subscriberProcessIdentifier = self.next_proc_id
        self.next_proc_id += 1
        # subscription_contexts[self.subscriberProcessIdentifier] = self
        self.monitoredObjectIdentifier = objectID
        self.issueConfirmedNotifications = confirmed
        self.lifetime = lifetime

    def cov_notification(self, apdu):
        # make a rash assumption that the property value is going to be
        # a single application encoded tag
        source = apdu.pduSource
        object_changed = apdu.monitoredObjectIdentifier

        elements = {
            "source": source,
            "object_changed": object_changed,
            "properties": {},
        }
        for element in apdu.listOfValues:
            prop_id = element.propertyIdentifier
            datatype = get_datatype(object_changed[0], prop_id)
            value = element.value

            if not datatype:
                # raise TypeError("unknown datatype")
                value = cast_datatype_from_tag(
                    element.value, object_changed[0], prop_id
                )
            else:
                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (
                    element.propertyArrayIndex is not None
                ):
                    if element.propertyArrayIndex == 0:
                        value = element.value.cast_out(Unsigned)
                    else:
                        value = element.value.cast_out(datatype.subtype)
                else:
                    value = element.value.cast_out(datatype)

            elements["properties"][prop_id] = value

        return elements


class CoV:
    """
    Mixin to support COV registration
    """

    def cov_notification(self, apdu):
        print("do something here")

    def send_cov_subscription(self, request):
        self._log.info("Request : {}".format(request))
        iocb = IOCB(request)
        # iocb.add_callback(self.subscription_acknowledged)
        self._log.info("IOCB : {}".format(iocb))

        iocb.add_callback(self.subscription_acknowledged)

        # pass to the BACnet stack
        deferred(self.this_application.request_io, iocb)

        # Unconfirmed request...so wait until complete
        # iocb.wait()  # Wait for BACnet response

    def subscription_acknowledged(self, iocb):
        if iocb.ioResponse:
            self._log.info("Subscription success")

        if iocb.ioError:
            self._log.error("Subscription failed. {}".format(iocb.ioError))

    def cov(self, address, objectID, confirmed=True, lifetime=None):
        address = Address(address)
        context = self._build_cov_context(
            address, objectID, confirmed=confirmed, lifetime=lifetime
        )
        request = self._build_cov_request(context)
        self.send_cov_subscription(request)

    def _build_cov_context(self, address, objectID, confirmed=True, lifetime=None):
        context = SubscriptionContext(
            address=address, objectID=objectID, confirmed=confirmed, lifetime=lifetime
        )
        self.this_application.subscription_contexts[
            context.subscriberProcessIdentifier
        ] = context
        return context

    def _build_cov_request(self, context):
        request = SubscribeCOVRequest(
            subscriberProcessIdentifier=context.subscriberProcessIdentifier,
            monitoredObjectIdentifier=context.monitoredObjectIdentifier,
        )
        request.pduDestination = context.address

        # optional parameters
        if context.issueConfirmedNotifications is not None:
            request.issueConfirmedNotifications = context.issueConfirmedNotifications
        if context.lifetime is not None:
            request.lifetime = context.lifetime

        return request
