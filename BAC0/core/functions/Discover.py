import asyncio
import typing as t

from bacpypes3.app import Application
from bacpypes3.pdu import Address, LocalBroadcast
from bacpypes3.primitivedata import ObjectIdentifier

from BAC0.core.app.asyncApp import BAC0Application

from ...core.utils.notes import note_and_log

try:
    from rich.table import Table
    from rich.console import Console

    RICH = True
except ImportError:
    RICH = False


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
        timeout: int = 3,
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
            self.discoveredDevices = {}
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

        if _networks and not global_broadcast:
            for each_network in _networks:
                self._log.info(f"Discovering network {each_network}")
                _res = await self.this_application.app.who_is(
                    low_limit=deviceInstanceRangeLowLimit,
                    high_limit=deviceInstanceRangeHighLimit,
                    address=Address(f"{each_network}:*"),
                    timeout=timeout,
                )
                for each in _res:
                    found.append((each, each_network))

        else:
            msg = (
                "Global braodacast required"
                if global_broadcast
                else "No BACnet network found"
            )
            self._log.info(
                f"{msg}, attempting a simple whois using provided device instances limits ({deviceInstanceRangeLowLimit} - {deviceInstanceRangeHighLimit})"
            )
            if global_broadcast is True:
                self._log.warning(
                    "Issuing a global Broadcast can create network flood. Use with care."
                )
            else:
                self._log.info("Issuing a local broadcast whois request.")
            _address = None if global_broadcast is True else LocalBroadcast()
            _res = await _app.who_is(
                low_limit=deviceInstanceRangeLowLimit,
                high_limit=deviceInstanceRangeHighLimit,
                address=_address,
                timeout=timeout,
            )
            for each in _res:
                found.append((each, _this_network))

        for iam_request, network_number in found:
            self._log.debug(f"Found device {iam_request} on network {network_number}")
            if not self.discoveredDevices:
                self.discoveredDevices = {}  # we can add device as we found some...
            device_address: Address = iam_request.pduSource
            objid: ObjectIdentifier = iam_request.iAmDeviceIdentifier
            self._log.debug(str(objid))
            self._log.debug(self.discoveredDevices.keys())
            key = str(objid)
            if key in self.discoveredDevices:
                self._log.debug(
                    f"{objid} already in discovered devices. Adding network number {network_number} to the list."
                )
                self.discoveredDevices[key]["network_number"].add(network_number)
            else:
                self._log.debug(
                    f"Adding {objid} to discovered devices in network {network_number}."
                )
                self.discoveredDevices[key] = {
                    "object_instance": objid,
                    "address": device_address,
                    "network_number": {network_number},
                    "vendor_id": iam_request.vendorID,
                    "vendor_name": "unknown",
                }

        self._log.info(
            f"Discovery done. Found {len(self.discoveredDevices)} devices on {len(_networks)} BACnet networks."
        )
