import asyncio
import os
from threading import Thread
import json

from bacpypes3.ipv4.app import NormalApplication, BBMDApplication, ForeignApplication
from bacpypes3.app import Application
import asyncio
import json
import sys
from bacpypes3.apdu import ErrorRejectAbortNack
from bacpypes3.basetypes import (
    DeviceStatus,
    IPv4OctetString,
    Segmentation,
    ServicesSupported,
    ProtocolLevel,
    NetworkType,
    IPMode,
    HostNPort,
    BDTEntry,
)
from bacpypes3.primitivedata import ObjectIdentifier, ObjectType
from bacpypes3.pdu import Address, IPv4Address
from bacpypes3.constructeddata import AnyAtomic
from bacpypes3.comm import bind
from bacpypes3.vendor import get_vendor_info

# for BVLL services
from bacpypes3.ipv4.bvll import Result as IPv4BVLLResult
from bacpypes3.ipv4.service import (
    BVLLServiceAccessPoint,
    BVLLServiceElement,
    BIPNormal,
    BIPForeign,
    BIPBBMD,
)
from bacpypes3.ipv4.link import NormalLinkLayer, BBMDLinkLayer, ForeignLinkLayer
from bacpypes3.ipv4 import IPv4DatagramServer

from BAC0.core.functions.GetIPAddr import HostIP

from typing import Coroutine
import asyncio
from asyncio import Future, AbstractEventLoop
from ...core.utils.notes import note_and_log


@note_and_log
class BAC0Application:
    """
    args.vendoridentifier
    args.instance
    args.name
    args.address
    args.foreign
    args.network
    args.ttl
    args.bbmd

    """

    _learnedNetworks = set()
    _cfg = None

    def __init__(self, cfg, addr, json_file=None):
        self._cfg = cfg  # backup what we wanted

        self.cfg = self.update_config(cfg, json_file)
        self.localIPAddr = addr
        self.bdt = self._cfg["BAC0"]["bdt"]
        self.device_cfg, self.networkport_cfg = self.cfg["application"]

        #self.foreign_bbmd()
        self._log.info(f"Configuration sent to build application : {self.cfg}")
        self.app = Application.from_json(self.cfg["application"])
        # asyncio.get_running_loop().run_until_complete()

        #self.bind_interface(self.localIPAddr)

    def bind_interface(self, addr):
        self.app.link_layers = {}

        self._log.info(f"Bind interface {addr} | {addr.netmask} | {addr.addrPort}")
        np = self.app.get_object_name("NetworkPort-1")
        print(type(np))
        link_address = np.address
        if self.get_bacnet_ip_mode() == IPMode.foreign:
            self.add_foreign_device_host(self._cfg["BAC0"]["bbmdAddress"])
            link_layer = ForeignLinkLayer(link_address)
            # start the registration process
            self.app.link_layers[np.objectIdentifier] = link_layer
            link_layer.register(np.fdBBMDAddress.address, np.fdSubscriptionLifetime)
            # let the NSAP know about this link layer
            self.app.nsap.bind(link_layer, address=link_address)
        elif self.get_bacnet_ip_mode() == IPMode.bbmd:
            link_layer = BBMDLinkLayer(link_address)
            self.app.link_layers[np.objectIdentifier] = link_layer
            for bdt_entry in np.bbmdBroadcastDistributionTable:
                link_layer.add_peer(bdt_entry.address)
            # let the NSAP know about this link layer
            self.app.nsap.bind(link_layer, address=link_address)
        else:
            link_layer = NormalLinkLayer(link_address)
            # let the NSAP know about this link layer
            if np.networkNumber == 0:
                self.app.nsap.bind(link_layer, address=link_address)
            else:
                self.app.nsap.bind(
                    link_layer, net=np.networkNumber, address=link_address
                )

        """
        # pick out the BVLL service access point from the local adapter
        local_adapter = self.app.nsap.local_adapter

        assert local_adapter
        bvll_sap = local_adapter.clientPeer
        

        # only IPv4 for now
        if isinstance(bvll_sap, BVLLServiceAccessPoint):
            # create a BVLL application service element
            bvll_ase = BVLLServiceElement()
            bind(bvll_ase, bvll_sap)
        """

    def foreign_bbmd(self):
        # maybe this is a foreign device
        np = self.cfg["application"][1]
        if self._cfg["BAC0"]["bbmdAddress"] is not None:
            self._log.info("This application will act as a Foreign Device")
            np["bacnet-ip-mode"] = "foreign"
            _addr, _port = self._cfg["BAC0"]["bbmdAddress"].split(":")
            hnp = HostNPort(self._cfg["BAC0"]["bbmdAddress"])
            # np["fd-bbmd-address"] = {'host': {'ip-address': str(hnp.host.ipAddress)}, 'port': hnp.port}
            np["fd-subscription-lifetime"] = self._cfg["BAC0"]["ttl"]

        # maybe this is a BBMD
        if self._cfg["BAC0"]["bdt"] is not None:
            self._log.info("This application will act as a BBMD")
            np["bacnet-ip-mode"] = "bbmd"
            np["bbmd-accept-fd-registration"] = "true"
            np["bbmd-foreign-device-table"] = []

    def add_foreign_device_host(self, host):
        np = self.app.get_object_name("NetworkPort-1")
        hnp = HostNPort(host)
        np.fdBBMDAddress = hnp

    def populate_bdt(self):
        np = self.app.get_object_name("NetworkPort-1")
        # populate the BDT
        bdt = []
        for addr in self.bdt:
            bdt_entry = BDTEntry(addr)
            bdt.append(bdt_entry)
        np.bbmdBroadcastDistributionTable = bdt

    def get_bacnet_ip_mode(self):
        return self.app.get_object_name("NetworkPort-1").bacnetIPMode

    def unregister_from_bbmd(self):
        self.app.unregister()

    def update_config(self, cfg, json_file):
        if json_file is None:
            if os.path.exists(
                os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")
            ):
                json_file = os.path.join(
                    os.path.expanduser("~"), ".BAC0", "device.json"
                )
                self._log.info("Using JSON Stored in user folder ~/.BAC0")

            else:
                json_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "device.json"
                )
                self._log.info("Using default JSON configuration file")
        with open(json_file, "r") as file:
            base_cfg = json.load(file)

        base_cfg["application"][0].update(cfg["device"])
        base_cfg["application"][1].update(cfg["network-port"])
        print(base_cfg)
        return base_cfg
