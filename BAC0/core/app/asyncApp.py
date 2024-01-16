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
from bacpypes3.ipv4.service import BVLLServiceAccessPoint, BVLLServiceElement, BIPNormal, BIPForeign, BIPBBMD
from bacpypes3.ipv4.link import NormalLinkLayer, BBMDLinkLayer, ForeignLinkLayer
from bacpypes3.ipv4 import IPv4DatagramServer

from BAC0.core.functions.GetIPAddr import HostIP

from typing import Coroutine
import asyncio
from asyncio import Future, AbstractEventLoop


class BAC0Application():
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

    def __init__(self, cfg, addr, json_file=None):
        #self._log.info(f"Configuring app with {cfg}")
        print(cfg)
        self.cfg = self.create_config(cfg, json_file)
        self.localIPAddr = addr
        self.device_cfg, self.networkport_cfg = self.cfg['application']
        self.foreign_bvll_sap = None

        self._required_class = Application

        self.app = self.create_from_json(self.cfg)
        asyncio.get_running_loop().run_until_complete()
        self.foreign_bbmd()
        self.bind_interface(self.localIPAddr)
        if isinstance(self.foreign_bvll_sap, BIPForeign):
            self.register_to_bbmd()

    def bind_interface(self, addr):
        print(f"Bind interface to {addr} | {addr.netmask} | {addr.addrPort}")

        if self.networkport_cfg["foreign"] is not None:
            print("foreign link layer")
            linklayer = NormalLinkLayer(addr)
            self.foreign_bvll_sap = BIPForeign()
        elif self.networkport_cfg["bdt"] is not None:
            print("bbmd link layer")
            linklayer = NormalLinkLayer(addr)
            self.foreign_bvll_sap = BIPBBMD()
        else:
            print("normal link layer")
            linklayer = NormalLinkLayer(addr)

        
        if self.foreign_bvll_sap:
            self.app.nsap.bind(self.foreign_bvll_sap, address=addr)
        else:
            self.app.nsap.bind(linklayer, address=addr)

        # pick out the BVLL service access point from the local adapter
        local_adapter = self.app.nsap.local_adapter

        assert local_adapter
        bvll_sap = local_adapter.clientPeer
        

        # only IPv4 for now
        if isinstance(bvll_sap, BVLLServiceAccessPoint):
            # create a BVLL application service element
            bvll_ase = BVLLServiceElement()
            bind(bvll_ase, bvll_sap)
            

    def foreign_bbmd(self):
        print("Foreign or BBMD ?")
        # maybe this is a foreign device
        np = self.app.get_object_name("NetworkPort-1")
        print(f"Netowrk port : {np}")
        if self.networkport_cfg["foreign"] is not None:
            print("Foreign")
            np.bacnetIPMode = IPMode.foreign
            np.fdBBMDAddress = HostNPort(self.networkport_cfg["foreign"])
            np.fdSubscriptionLifetime = self.networkport_cfg["ttl"]


        # maybe this is a BBMD
        if self.networkport_cfg["bdt"] is not None:
            print("BBMD")
            np.bacnetIPMode = IPMode.bbmd
            np.bbmdAcceptFDRegistrations = True  # Boolean
            np.bbmdForeignDeviceTable = []  # ListOf(FDTEntry)

            # populate the BDT
            bdt = []
            for addr in self.networkport_cfg["bdt"]:
                bdt_entry = BDTEntry(addr)
                bdt.append(bdt_entry)
            np.bbmdBroadcastDistributionTable = bdt

    def register_to_bbmd(self):
        np = self.app.get_object_name("NetworkPort-1")
        self.foreign_bvll_sap.register(self.localIPAddr, np.fdSubscriptionLifetime)

    def unregister_from_bbmd(self):
        self.foreign_bvll_sap.unregister()

    def create_from_json(self,cfg):
        return self._required_class.from_json(cfg['application'])
        
    def create_config(self, cfg, json_file):
        if not json_file:
            if os.path.exists(os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")):
                json_file = os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")
                
            else:
                json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device.json")
        with open(json_file, 'r') as file:
            base_cfg = json.load(file)

        base_cfg['application'][0].update(cfg['device'])
        base_cfg['application'][1].update(cfg['network-port'])
        print(base_cfg)
        return base_cfg

        


    