import asyncio

from bacpypes3.app import Application
from bacpypes3.pdu import Address
from BAC0.core.app.asyncApp import BAC0Application

from ...core.utils.notes import note_and_log


@note_and_log
class Alias:
    """
    Bacpypes3 now offer a wide range a functions out of the box
    This mixin bring them to the BAC0 app so it's easy to use
    """

    async def who_is(self, address=None, low_limit=0, high_limit=4194303, timeout=3):
        """
        Build a WhoIs request. WhoIs requests are sent to discover devices on the network.
        If an address is specified, the request is sent to that address. Otherwise,
        the request is broadcast to the local network.

        :param address: (optional) The address to send the request to.
        :param destination: (optional) The destination address.

        :returns: List of IAm responses.

        Example::

            import BAC0
            bacnet = BAC0.lite()

            bacnet.whois()
            bacnet.whois('2:5')
        """
        _iams = await self.this_application.app.who_is(
            address=Address(address),
            low_limit=low_limit,
            high_limit=high_limit,
            timeout=timeout,
        )
        return _iams

    def iam(self, address=None):
        """
        Build an IAm response.  IAm are sent in response to a WhoIs request that;
        matches our device ID, whose device range includes us, or is a broadcast.
        Content is defined by the script (deviceId, vendor, etc...)

        Example::

            iam()
        """
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        self.log("do_iam", level="debug")

        _app.i_am(address=address)

    async def whois_router_to_network(
        self, network=None, *, destination=None, timeout=3
    ):
        """
        Send a Who-Is-Router-To-Network request. This request is used to discover routers
        on the network that can route messages to a specific network.

        The function sends a broadcast message to the local network to find routers that
        can route messages to the specified network. The response will contain information
        about the routers that can handle the routing.

        Example::

            whois_router_to_network()
        """
        # build a request
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        try:
            network_numbers = await asyncio.wait_for(
                _app.nse.who_is_router_to_network(), timeout
            )
            return network_numbers
        except asyncio.TimeoutError:
            # Handle the timeout error
            self.log(
                "Request timed out for whois_router_to_network, no response",
                level="warning",
            )
            return []

    async def init_routing_table(self, address):
        """
        irt <addr>

        Send an empty Initialize-Routing-Table message to an address, a router
        will return an acknowledgement with its routing table configuration.
        """
        # build a request
        self.log(f"Addr : {address}", level="info")
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        await _app.nse.initialize_routing_table()

    async def what_is_network_number(self, destination=None, timeout=3):
        """
        winn [ <addr> ]

        Send a What-Is-Network-Number message.  If the address is unspecified
        the message is locally broadcast.
        """
        # build a request
        # self.log("Addr : {}".format(address), level='info')
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        try:
            network_number = await asyncio.wait_for(
                _app.nse.what_is_network_number(), timeout
            )
            return network_number
        except asyncio.TimeoutError:
            # Handle the timeout error
            self.log(
                "Request timed out for what_is_network_number, no response",
                level="warning",
            )
            return None

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
