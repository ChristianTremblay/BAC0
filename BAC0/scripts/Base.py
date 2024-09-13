#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Doc here
"""
import asyncio
import random
import sys
import typing as t
from collections import defaultdict

# --- standard Python modules ---
from bacpypes3.basetypes import DeviceStatus, HostNPort, ObjectTypesSupported
from bacpypes3.json.util import sequence_to_json
from bacpypes3.local.device import DeviceObject
from bacpypes3.local.networkport import NetworkPortObject
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import CharacterString
from bacpypes3.vendor import VendorInfo, get_vendor_info

# --- this application's modules ---
from ..core.app.asyncApp import (
    BAC0Application,
)  # BAC0BBMDDeviceApplication,; BAC0ForeignDeviceApplication,
from ..core.functions.GetIPAddr import validate_ip_address
from ..core.functions.TimeSync import TimeHandler
from ..core.io.IOExceptions import InitializationError, UnknownObjectError
from ..core.utils.notes import note_and_log
from ..tasks.TaskManager import stopAllTasks

# --- 3rd party modules ---

# ------------------------------------------------------------------------------


@note_and_log
class LocalObjects(object):
    def __init__(self, device):
        self.device = device

    def __getitem__(self, obj):
        item = None
        if isinstance(obj, tuple):
            obj_type, instance = obj
            item = self.device.this_application.app.get_object_id((obj_type, instance))
        elif isinstance(obj, str):
            name = obj
            item = self.device.this_application.app.get_object_name(name)
        if item is None:
            raise UnknownObjectError(f"Can't find {obj} in local device")
        else:
            return item


def charstring(val):
    return CharacterString(val) if isinstance(val, str) else val


@note_and_log
class Base:
    """
    Build a running BACnet/IP device that accepts WhoIs and IAm requests
    Initialization requires some minimial information about the local device.

    :param localIPAddr='127.0.0.1':
    :param localObjName='BAC0':
    :param deviceId=None:
    :param maxAPDULengthAccepted='1024':
    :param maxSegmentsAccepted='1024':
    :param segmentationSupported='segmentedBoth':
    """

    _used_ips: t.Set[Address] = set()

    def __init__(
        self,
        localIPAddr: Address = Address("127.0.0.1/24"),
        networkNumber: int = None,
        localObjName: str = "BAC0",
        deviceId: int = None,
        firmwareRevision: str = "".join(sys.version.split("|")[:2]),
        maxAPDULengthAccepted: str = "1024",
        maxSegmentsAccepted: str = "1024",
        segmentationSupported: str = "segmentedBoth",
        bbmdAddress: str = None,
        bbmdTTL: int = 0,
        bdtable: list = None,
        modelName: str = "BAC0 Scripting Tool",
        vendorId: int = 842,
        vendorName: str = "SERVISYS inc.",
        description: str = "http://christiantremblay.github.io/BAC0/",
        location: str = "Bromont, Québec",
        timezone: str = "America/Montreal",
        json_file: str = None,
    ):
        self.log("Configurating app", level="debug")

        # Register Servisys
        try:
            _BAC0_vendor = VendorInfo(vendorId)
        except RuntimeError:
            pass  # we are re-running the script... forgive us
            _BAC0_vendor = get_vendor_info(vendorId)
        _BAC0_vendor.register_object_class(
            ObjectTypesSupported.networkPort, NetworkPortObject
        )
        _BAC0_vendor.register_object_class(ObjectTypesSupported.device, DeviceObject)

        self.timehandler = TimeHandler(tz=timezone)

        self.response = None
        self._initialized = False
        self._started = False
        self._stopped = False

        if localIPAddr in Base._used_ips:
            raise InitializationError(
                "IP Address provided ({}) already used by BAC0. Check if another software is using port 47808 on this network interface. If so, you can define multiple IP per interface. Or specify another IP using BAC0.lite(ip='IP/mask')".format(
                    localIPAddr
                )
            )

        if validate_ip_address(localIPAddr):
            self.localIPAddr = localIPAddr
        else:
            raise InitializationError(
                "IP Address provided ({}) invalid. Check if another software is using port 47808 on this network interface. If so, you can define multiple IP per interface. Or specify another IP using BAC0.lite(ip='IP/mask')".format(
                    localIPAddr
                )
            )
        self.networkNumber = networkNumber

        self.Boid = (
            int(deviceId) if deviceId else (3056177 + int(random.uniform(0, 1000)))
        )

        self.segmentationSupported = segmentationSupported
        self.maxSegmentsAccepted = maxSegmentsAccepted
        self.localObjName = localObjName
        self.local_objects = LocalObjects(device=self)

        self.maxAPDULengthAccepted = maxAPDULengthAccepted
        self.vendorId = vendorId
        self.vendorName = charstring(vendorName)
        self.modelName = charstring(modelName)
        self.description = charstring(description)
        self.location = charstring(location)

        self.discoveredDevices: t.Optional[t.Dict[t.Tuple[str, int], int]] = None
        self.systemStatus = DeviceStatus(1)

        self.bbmdAddress = bbmdAddress
        self.bbmdTTL = bbmdTTL
        self.bdtable = bdtable

        self.firmwareRevision = firmwareRevision
        self._ric = {}
        self.subscription_contexts = {}
        self.database = None
        self.json_file = json_file

        try:
            self.startApp()
        except InitializationError as error:
            raise InitializationError(
                f"Gros probleme : {error}. Address requested : {localIPAddr}"
            )

    def startApp(self):
        """
        Define the local device, including services supported.
        Once defined, start the BACnet stack in its own thread.
        """
        self.log("Create Local Device", level="debug")
        try:
            app_type = "BACnet/IP App"

            class config(defaultdict):
                "Simple class to mimic args dot retrieval"

                def __init__(self, cfg):
                    for k, v in cfg.items():
                        self[k] = v

                def __getattr__(self, key):
                    return self[key]

            if self.bbmdAddress is not None:
                mode = "foreign"
            elif self.bdtable:
                mode = "bbmd"
            else:
                mode = "normal"
            cfg = {
                "BAC0": {
                    "bbmdAddress": self.bbmdAddress,
                    "bdt": self.bdtable,
                    "ttl": self.bbmdTTL,
                },
                "device": {
                    "object-name": self.localObjName,
                    # "firmware-revision": self.firmwareRevision,
                    "vendor-identifier": self.vendorId,
                    "vendor-name": "Servisys inc.",
                    "object-identifier": f"device,{self.Boid}",
                    "object-list": [f"device,{self.Boid}", "network-port,1"],
                    "model-name": self.modelName,
                    # "max-apdu-length-accepted": self.maxAPDULengthAccepted,
                    # "max-segments-accepted": self.maxSegmentsAccepted,
                    # "location": self.location,
                    # "description": self.description
                },
                "network-port": {
                    "ip-address": str(self.localIPAddr),
                    "ip-subnet-mask": str(self.localIPAddr.netmask),
                    "bacnet-ip-udp-port": self.localIPAddr.addrPort,
                    "network-number": None,
                    "fd-bbmd-address": sequence_to_json(HostNPort(self.bbmdAddress)),
                    "fd-subscription-lifetime": self.bbmdTTL,
                    "bacnet-ip-mode": mode,
                },
            }
            if mode == "bbmd":
                # bdt_json_seq = [f"BDTEntry({addr})" for addr in self.bdtable]
                cfg["network-port"]["bbmdBroadcastDistributionTable"] = self.bdtable

            _cfg = config(cfg)

            self.this_application = BAC0Application(
                _cfg, self.localIPAddr, json_file=self.json_file
            )
            if mode == "bbmd":
                self._log.info(f"Populating BDT with {self.bdtable}")
                self.this_application.populate_bdt()

            if mode == "foreign":
                self._log.info(
                    f"Registering as a foreign device to host {self.bbmdAddress} for {self.bbmdTTL} seconds"
                )
                self.this_application.register_as_foreign_device_to(
                    host=self.bbmdAddress, lifetime=self.bbmdTTL
                )

            self.log("Starting", level="debug")
            self._initialized = True

            try:
                Base._used_ips.add(self.localIPAddr)
                self.log(f"Registered as {app_type} | mode {mode}", level="info")
                self._started = True
            except OSError as error:
                self.log(f"Error opening socket: {error}", level="warning")
                raise InitializationError(f"Error opening socket: {error}")
            self.log("Running", level="debug")
        except OSError as error:
            self.log(f"an error has occurred: {error}", level="error")
            raise InitializationError(f"Error starting app: {error}")
            self.log("finally", level="debug")

    def register_foreign_device(self, addr=None, ttl=0):
        # self.this_application.register_to_bbmd(addr, ttl)
        raise NotImplementedError()

    def unregister_foreign_device(self):
        self.this_application.unregister_from_bbmd()

    def disconnect(self) -> asyncio.Task:
        task = asyncio.create_task(self._disconnect())
        return task

    async def _disconnect(self):
        """
        Stop the BACnet stack.  Free the IP socket.
        """
        self.log("Stopping All running tasks", level="debug")
        await stopAllTasks()
        self.log("Stopping BACnet stack", level="debug")
        # Freeing socket
        self.this_application.app.close()

        self._stopped = True  # Stop stack thread
        # self.t.join()
        self._started = False
        Base._used_ips.discard(self.localIPAddr)
        self.log("BACnet stopped", level="info")

    @property
    def routing_table(self):
        """
        Routing Table will give all the details about routers and how they
        connect BACnet networks together.

        It's a decoded presentation of what bacpypes.router_info_cache contains.

        Returns a dict with the address of routers as key.
        """

        class Router:
            def __init__(self, snet, address, dnets, path=None):
                self.source_network: int = snet
                self.address: Address = address
                self.destination_networks: set = dnets
                self.path: list = path

            def __repr__(self):
                return "Source Network: {} | Address: {} | Destination Networks: {} | Path: {}".format(
                    self.source_network,
                    self.address,
                    self.destination_networks,
                    self.path,
                )

        self._routers = {}

        self._ric = self.this_application.app.nsap.router_info_cache

        for router, dnets in self._ric.router_dnets.items():
            snet, address = router
            self._routers[str(address)] = Router(snet, address, dnets, path=[])
        for path, router_info in self._ric.path_info.items():
            router_address, router_status = router_info
            snet, dnet = path
            self._routers[str(router_address)].path.append((path, router_status))

        return self._routers
