import asyncio
from typing import List, Optional, Tuple, Union

from bacpypes3.app import Application
from bacpypes3.netservice import RouterEntryStatus
from bacpypes3.npdu import RejectMessageToNetwork
from bacpypes3.pdu import Address, GlobalBroadcast

from BAC0.core.app.asyncApp import BAC0Application

from ...core.utils.notes import note_and_log

ROUTER_TUPLE_TYPE = Union[
    Tuple[Union[Address, str], Union[int, List[int]]],
    Tuple[Union[Address, str], Union[int, List[int]], Optional[int]],
]


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
            address=Address(address) if address else None,
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
        self, network=None, *, destination=None, timeout=3, global_broadcast=False
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
        if destination and not isinstance(destination, Address):
            destination = Address(destination)
        elif global_broadcast:
            destination = GlobalBroadcast()

        try:
            network_numbers = await asyncio.wait_for(
                _app.nse.who_is_router_to_network(
                    destination=destination, network=network
                ),
                timeout,
            )
            return network_numbers
        except asyncio.TimeoutError:
            # Handle the timeout error
            self.log(
                "Request timed out for whois_router_to_network, no response",
                level="warning",
            )
            return []

    async def init_routing_table(self, address=None):
        """
        irt <addr>

        Send an empty Initialize-Routing-Table message to an address, a router
        will return an acknowledgement with its routing table configuration.
        """
        # build a request
        self.log(f"Addr : {address}", level="info")
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        if address is not None and not isinstance(address, Address):
            address = Address(address)
        await _app.nse.initialize_routing_table(destination=address)

    async def use_router(
        self,
        router_infos: Union[
            Tuple[Union[Address, str], Union[int, List[int]]],
            Tuple[Union[Address, str], Union[int, List[int]], Optional[int]],
        ] = (None, None, None),
    ):
        address, dnets = router_infos[:2]
        try:
            snet = router_infos[2]
        except IndexError:
            snet = None
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        if not isinstance(address, Address):
            address = Address(address)
        if not isinstance(dnets, list):
            dnets = [dnets]
        response = await self.who_is(address=address)
        if response:
            self._log.info(f"Router found at {address}")
            self._log.info(
                f"Adding router reference -> Snet : {snet} Addr : {address} dnets : {dnets}"
            )
            await _app.nsap.update_router_references(
                snet=snet, address=address, dnets=dnets
            )
            self._ric = self.this_application.app.nsap.router_info_cache
            self._log.info(
                f"Updating router info cache -> Snet : {snet} Addr : {address} dnets : {dnets}"
            )
            for each in dnets:
                await self._ric.set_path_info(
                    snet, each, address, RouterEntryStatus.available
                )
                _this_application._learnedNetworks.add(each)
        else:
            self._log.warning(f"Router not found at {address}")

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
