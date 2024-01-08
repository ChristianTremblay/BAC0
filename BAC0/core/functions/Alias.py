from BAC0.core.app.asyncApp import BAC0Application
from ...core.utils.notes import note_and_log
import typing as t
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier
from bacpypes3.app import Application
import asyncio


@note_and_log
class Alias:
    """
    Bacpypes3 now offer a wide range a functions out of the box
    This mixin bring them to the BAC0 app so it's easy to use
    """

    async def iam(self, destination=None):
        """
        Build an IAm response.  IAm are sent in response to a WhoIs request that;
        matches our device ID, whose device range includes us, or is a broadcast.
        Content is defined by the script (deviceId, vendor, etc...)

        :returns: bool

        Example::

            iam()
        """
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        self._log.debug("do_iam")

        await _app.i_am()

    async def whois_router_to_network(self, network=None, *, destination=None):
        # build a request
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        await _app.nse.who_is_router_to_network()

    async def init_routing_table(self, address):
        """
        irt <addr>

        Send an empty Initialize-Routing-Table message to an address, a router
        will return an acknowledgement with its routing table configuration.
        """
        # build a request
        self._log.info("Addr : {}".format(address))
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        await _app.nse.initialize_routing_table()

    async def what_is_network_number(self, destination=None):
        """
        winn [ <addr> ]

        Send a What-Is-Network-Number message.  If the address is unspecified
        the message is locally broadcast.
        """
        # build a request
        # self._log.info("Addr : {}".format(address))
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        await _app.nse.what_is_network_number()

    async def whohas(
        self,
        object_id=None,
        object_name=None,
        instance_range_low_limit=0,
        instance_range_high_limit=4194303,
        destination=None,
        global_broadcast=False,
    ):
        """
        Object ID : analogInput:1
        Object Name : string
        Instance Range Low Limit : 0
        Instance Range High Limit : 4194303
        destination (optional) : If empty, local broadcast will be used.
        global_broadcast : False

        """
        print("Not yet... come back later")
        await asyncio.sleep(1)

        """    
        if object_name and not object_id:
            obj_name = CharacterString(object_name)
            obj = WhoHasObject(objectName=obj_name)
        elif object_id and not object_name:
            obj_id = ObjectIdentifier(object_id)
            obj = WhoHasObject(objectIdentifier=obj_id)
        else:
            obj_id = ObjectIdentifier(object_id)
            obj_name = CharacterString(object_name)
            obj = WhoHasObject(objectIdentifier=obj_id, objectName=obj_name)
        limits = WhoHasLimits(
            deviceInstanceRangeLowLimit=instance_range_low_limit,
            deviceInstanceRangeHighLimit=instance_range_high_limit,
        )
        request = WhoHasRequest(object=obj, limits=limits)
        if destination:
            request.pduDestination = Address(destination)
        else:
            if global_broadcast:
                request.pduDestination = GlobalBroadcast()
            else:
                request.pduDestination = LocalBroadcast()
        iocb = IOCB(request)  # make an IOCB
        iocb.set_timeout(2)
        deferred(self.this_application.request_io, iocb)
        iocb.wait()

        iocb = IOCB(request)  # make an IOCB
        self.this_application._last_i_have_received = []

        if iocb.ioResponse:  # successful response
            pass

        if iocb.ioError:  # unsuccessful: error/reject/abort
            pass

        time.sleep(3)
        # self.discoveredObjects = self.this_application.i_am_counter
        return self.this_application._last_i_have_received
        """
