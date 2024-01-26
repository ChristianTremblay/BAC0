#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Doc here
"""
import random
import sys
import typing as t
from collections import defaultdict

# --- standard Python modules ---
from bacpypes3.app import Application
from bacpypes3.basetypes import (
    BDTEntry,
    DeviceStatus,
    HostNPort,
    IPMode,
    NetworkType,
    ProtocolLevel,
    Segmentation,
    ServicesSupported,
    ObjectTypesSupported,
)
from bacpypes3.json.util import sequence_to_json
from bacpypes3.local.device import DeviceObject
from bacpypes3.local.networkport import NetworkPortObject
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import CharacterString
from bacpypes3.vendor import VendorInfo, get_vendor_info

# --- this application's modules ---
from .. import infos
from ..core.app.asyncApp import (
    BAC0Application,
)  # BAC0BBMDDeviceApplication,; BAC0ForeignDeviceApplication,
from ..core.functions.GetIPAddr import validate_ip_address
from ..core.functions.TimeSync import TimeHandler
from ..core.io.IOExceptions import InitializationError, UnknownObjectError
from ..core.utils.notes import note_and_log
from ..tasks.TaskManager import stopAllTasks

# --- 3rd party modules ---


try:
    import pandas

    _COMPLETE = True
except ImportError:
    _COMPLETE = False

# ------------------------------------------------------------------------------


@note_and_log
class LocalObjects(object):
    def __init__(self, device):
        self.device = device

    def __getitem__(self, obj):
        item = None
        if isinstance(obj, tuple):
            obj_type, instance = obj
            item = self.device.this_application.get_object_id((obj_type, instance))
        elif isinstance(obj, str):
            name = obj
            item = self.device.this_application.get_object_name(name)
        if item is None:
            raise UnknownObjectError("Can't find {} in local device".format(obj))
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
        localIPAddr="127.0.0.1",
        networkNumber=None,
        localObjName="BAC0",
        deviceId=None,
        firmwareRevision="".join(sys.version.split("|")[:2]),
        maxAPDULengthAccepted="1024",
        maxSegmentsAccepted="1024",
        segmentationSupported="segmentedBoth",
        bbmdAddress=None,
        bbmdTTL=0,
        bdtable=None,
        modelName="BAC0 Scripting Tool",
        vendorId=842,
        vendorName="SERVISYS inc.",
        description="http://christiantremblay.github.io/BAC0/",
        location="Bromont, Québec",
        spin=None,
    ):
        self._log.debug("Configurating app")

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

        self.timehandler = TimeHandler()

        if not _COMPLETE:
            self._log.debug(
                "To be able to run the web server, you must install pandas, bokeh, flask and flask_bootstrap"
            )
            self._log.debug(
                "Those are not all installed so BAC0 will work in Lite mode only."
            )

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

        try:
            self.startApp()
        except InitializationError as error:
            raise InitializationError(
                "Gros probleme : {}. Address requested : {}".format(error, localIPAddr)
            )

    def startApp(self):
        """
        Define the local device, including services supported.
        Once defined, start the BACnet stack in its own thread.
        """
        self._log.debug("Create Local Device")
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

            self.this_application = BAC0Application(config(cfg), self.localIPAddr)
            self._log.debug("Starting")
            self._initialized = True

            try:
                Base._used_ips.add(self.localIPAddr)
                self._log.info("Registered as {}".format(app_type))
                self._started = True
            except OSError as error:
                self._log.warning("Error opening socket: {}".format(error))
                raise InitializationError("Error opening socket: {}".format(error))
            self._log.debug("Running")
        except OSError as error:
            self._log.error("an error has occurred: {}".format(error))
            raise InitializationError("Error starting app: {}".format(error))
            self._log.debug("finally")

    def register_foreign_device(self, addr=None, ttl=0):
        # self.this_application.register_to_bbmd(addr, ttl)
        raise NotImplementedError()

    def unregister_foreign_device(self):
        self.this_application.unregister_from_bbmd()

    def disconnect(self):
        """
        Stop the BACnet stack.  Free the IP socket.
        """
        self._log.debug("Stopping All running tasks")
        stopAllTasks()
        self._log.debug("Stopping BACnet stack")
        # Freeing socket
        self.this_application.close()

        self._stopped = True  # Stop stack thread
        self.t.join()
        self._started = False
        Base._used_ips.discard(self.localIPAddr)
        self._log.info("BACnet stopped")

    @property
    def routing_table(self):
        """
        Routing Table will give all the details about routers and how they
        connect BACnet networks together.

        It's a decoded presentation of what bacpypes.router_info_cache contains.

        Returns a dict with the address of routers as key.
        """

        class Router:
            def __init__(self, router_info, index=None, path=None):
                self.source_network = router_info.snet
                self.address = router_info.address
                self.destination_networks = router_info.dnets
                self.index = index
                self.path = path

            def __repr__(self):
                return "Source Network: {} | Address: {} | Destination Networks: {} | Path: {}".format(
                    self.source_network,
                    self.address,
                    self.destination_networks,
                    self.path,
                )

        self._routers = {}

        self._ric = {}
        ric = self.this_application.app.nsap.router_info_cache

        for networks, routers in ric.routers.items():
            for address, router in routers.items():
                self._routers[str(address)] = Router(router, index=networks)
        for path, router in ric.path_info.items():
            self._routers[str(router.address)].path = path

        return self._routers
