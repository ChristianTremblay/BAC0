import asyncio
import typing as t

from bacpypes3.app import Application
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier

from BAC0.core.app.asyncApp import BAC0Application

from ...core.utils.notes import note_and_log


@note_and_log
class Discover:
    """
    Define BACnet WhoIs and IAm functions.
    """

    @property
    def known_network_numbers(self) -> t.Set[int]:
        return self.this_application._learnedNetworks

    def discover(
        self,
        networks: t.Union[str, t.List[int], int] = "known",
        limits: t.Tuple[int, int] = (0, 4194303),
        global_broadcast: bool = False,
        reset: bool = False,
    ) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        asyncio.create_task(
            self._discover(
                networks=networks,
                limits=limits,
                global_broadcast=global_broadcast,
                reset=reset,
            )
        )

    async def _discover(
        self,
        networks: t.Union[str, t.List[int], int] = "known",
        limits: t.Tuple[int, int] = (0, 4194303),
        global_broadcast: bool = False,
        reset: bool = False,
    ) -> None:
        """
        Discover is meant to be the function used to explore the network when we
        connect.
        It will trigger whois request using the different options provided with
        parameters.

        By default, a local broadcast will be used. This is required as in big
        BACnet network, global broadcast can lead to network flood and loss of data.

        If not parameters are given, BAC0 will try to :

            * Find the network on which it is
            * Find routers for other networks (accessible via local broadcast)
            * Detect "known networks"
            * Use the list of known networks and create whois request to find all devices on those networks

        This should be sufficient for most cases.

        Once discovery is done, user may access the list of "discovered devices" using ::

            bacnet.discoveredDevices

        :param networks (list, integer) : A simple integer or a list of integer
            representing the network numbers used to issue whois request.

        :param limits (tuple) : tuple made of 2 integer, the low limit and the high
            limit. Those are the device instances used in the creation of the
            whois request. Min : 0 ; Max : 4194303

        :param global_broadcast (boolean) : If set to true, a global broadcast
            will be used for the whois. Use with care.
        """
        if reset:
            self.discoveredDevices = set()
        found = []
        _networks = []

        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        deviceInstanceRangeLowLimit, deviceInstanceRangeHighLimit = limits
        # Try to find on which network we are
        _this_network = await _app.nse.what_is_network_number()
        _networks.append(_this_network)
        # Try to find local routers...
        _other_networks = await _app.nse.who_is_router_to_network()
        for each in _other_networks:
            network_adapter, _iamrtn = each
            _networks.extend(_iamrtn.iartnNetworkList)
        for net in _networks:
            _this_application._learnedNetworks.add(net)
        self._log.info(f"Found those networks : {self.known_network_numbers}")

        if networks:
            if isinstance(networks, list):
                # we'll make multiple whois...
                for network in networks:
                    if network < 65535:
                        _networks.append(network)
            elif networks == "known":
                _networks = self.known_network_numbers.copy()
            else:
                if isinstance(networks, int) and networks < 65535:
                    _networks.append(networks)

        if _networks:
            for network in _networks:
                self._log.info(f"Discovering network {network}")
                _res = await self.this_application.app.who_is(
                    low_limit=deviceInstanceRangeLowLimit,
                    high_limit=deviceInstanceRangeHighLimit,
                    # global_broadcast=global_broadcast, if not address -> global
                )
                for each in _res:
                    found.append(each)

        else:
            self._log.info(
                "No BACnet network found, attempting a simple whois using provided device instances limits ({} - {})".format(
                    deviceInstanceRangeLowLimit, deviceInstanceRangeHighLimit
                )
            )
            _res = await _app.who_is(
                low_limit=deviceInstanceRangeLowLimit,
                high_limit=deviceInstanceRangeHighLimit,
                # global_broadcast=global_broadcast,
            )
            for each in _res:
                found.append(each)
        for each in found:
            if not self.discoveredDevices:
                self.discoveredDevices = set()  # we can add device as we found some...
            device_address: Address = each.pduSource
            objid: ObjectIdentifier = each.iAmDeviceIdentifier
            print(f"{objid} @ {device_address}")
            self.discoveredDevices.add((objid, device_address))
        return found
