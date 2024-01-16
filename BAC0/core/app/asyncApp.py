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
from bacpypes3.ipv4.service import BVLLServiceAccessPoint, BVLLServiceElement, BIPNormal, BIPForeign
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
        self.cfg = cfg
        self.localIPAddr = addr
        self.app = self.create_from_json(json_file)
        self.foreign_bbmd()
        self.bind_interface(self.localIPAddr)

    def bind_interface(self, addr):
        print(f"Bind interface to {addr}")

        if self.cfg['network-port']["foreign"] is not None:
            print("foreign link layer")
            linklayer = ForeignLinkLayer(addr)
        elif self.cfg['network-port']["bdt"] is not None:
            print("bbmd link layer")
            linklayer = BBMDLinkLayer(addr)
        else:
            print("normal link layer")
            linklayer = NormalLinkLayer(addr)

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
        if self.cfg['network-port']["foreign"] is not None:
            print("Foreign")
            np.bacnetIPMode = IPMode.foreign
            np.fdBBMDAddress = HostNPort(self.cfg['network-port']["foreign"])
            np.fdSubscriptionLifetime = self.cfg['network-port']["ttl"]

        # maybe this is a BBMD
        if self.cfg['network-port']["bdt"] is not None:
            print("BBMD")
            np.bacnetIPMode = IPMode.bbmd
            np.bbmdAcceptFDRegistrations = True  # Boolean
            np.bbmdForeignDeviceTable = []  # ListOf(FDTEntry)

            # populate the BDT
            bdt = []
            for addr in self.cfg['network-port']["bdt"]:
                bdt_entry = BDTEntry(addr)
                bdt.append(bdt_entry)
            np.bbmdBroadcastDistributionTable = bdt



    def create_from_json(self,json_file=None):
        if not json_file:
            if os.path.exists(os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")):
                json_file = os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")
                
            else:
                json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device.json")
        with open(json_file, 'r') as file:
            _cfg = json.load(file)
        
        self.device_config = _cfg['application'][0].update(self.cfg)
        self.network_port_config = _cfg['application'][1].update(self.cfg)
        updated_cfg = json.dumps(_cfg)
        print(updated_cfg)

        return Application.from_json(_cfg['application'])


    def create_app(self):   
        vendor_info = get_vendor_info(self.cfg.vendoridentifier)
        if vendor_info.vendor_identifier == 0:
            raise RuntimeError(f"missing vendor info: {self.cfg.vendoridentifier}")

        # get the device object class and make an instance
        device_object_class = vendor_info.get_object_class(ObjectType.device)
        if not device_object_class:
            raise RuntimeError(
                f"vendor indentifier {self.cfg.vendoridentifier} missing device object class"
            )
        device_object = device_object_class(
            objectIdentifier=("device", int(self.cfg.instance)), objectName=self.cfg.name
        )

        # get the network port object class and make an instance
        network_port_object_class = vendor_info.get_object_class(ObjectType.networkPort)
        if not network_port_object_class:
            raise RuntimeError(
                f"vendor indentifier {self.cfg.vendoridentifier} missing network port object class"
            )

        # default address is 'host' or 'host:0' for a foreign device
        address = self.cfg.address
        if not address:
            address = "host:0" if self.cfg.foreign else "host"

        # make a network port object
        network_port_object = network_port_object_class()
        network_port_object.address = address
        network_port_object.objectIdentifier=("network-port", 1)
        network_port_object.objectName="NetworkPort-1"
        network_port_object.networkNumber=self.cfg.network
        network_port_object.networkNumberQuality="configured" if self.cfg.network else "unknown"
        network_port_object.max_apdu_length_accepted = self.cfg["max-apdu-length-accepted"]
        

        # maybe this is a foreign device
        if self.cfg.foreign is not None:
            network_port_object.bacnetIPMode = IPMode.foreign
            network_port_object.fdBBMDAddress = HostNPort(self.cfg.foreign)
            network_port_object.fdSubscriptionLifetime = self.cfg.ttl

        # maybe this is a BBMD
        if self.cfg.bbmd is not None:
            network_port_object.bacnetIPMode = IPMode.bbmd
            network_port_object.bbmdAcceptFDRegistrations = True  # Boolean
            network_port_object.bbmdForeignDeviceTable = []  # ListOf(FDTEntry)

            # populate the BDT
            bdt = []
            for addr in self.cfg.bbmd:
                bdt_entry = BDTEntry(addr)
                bdt.append(bdt_entry)
            network_port_object.bbmdBroadcastDistributionTable = bdt

        # continue the build process
        return Application.from_object_list(
            [device_object, network_port_object],
            device_info_cache=None,
            router_info_cache=None,
            aseID=None,
        )   




    
    