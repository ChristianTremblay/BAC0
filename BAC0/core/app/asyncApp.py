import asyncio
import os
from threading import Thread

loop = asyncio.new_event_loop()
import nest_asyncio
from bacpypes3.ipv4.app import NormalApplication
from bacpypes3.app import Application
import asyncio
import json
import sys
from bacpypes3.apdu import ErrorRejectAbortNack
from bacpypes3.basetypes import IPv4OctetString
from bacpypes3.primitivedata import ObjectIdentifier
from bacpypes3.pdu import Address, IPv4Address
from bacpypes3.constructeddata import AnyAtomic
from bacpypes3.comm import bind

# for BVLL services
from bacpypes3.ipv4.bvll import Result as IPv4BVLLResult
from bacpypes3.ipv4.service import BVLLServiceAccessPoint, BVLLServiceElement, BIPNormal
from bacpypes3.ipv4.link import NormalLinkLayer

from BAC0.core.functions.GetIPAddr import HostIP

from typing import Coroutine
import asyncio
from asyncio import Future, AbstractEventLoop
from threading import Thread

loop = None


def create_event_loop_thread() -> AbstractEventLoop:
    """
    From https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058
    """

    def start_background_loop(loop: AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    eventloop = asyncio.new_event_loop()
    thread = Thread(target=start_background_loop, args=(eventloop,), daemon=True)
    thread.start()
    global loop
    loop = eventloop
    return eventloop, thread


def run(coro: Coroutine, loop) -> Future:
    """
    From https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058
    """
    return asyncio.run_coroutine_threadsafe(coro, loop)


class BAC0Application(Application):
    _learnedNetworks = set()

    def __init__(self, json_file=None):
        if not json_file:
            json_file = os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")
        # self.eventloop, self.loop_thread = create_event_loop_thread()
        try:
            # nest_asyncio.apply()
            # run(self.create_app(json_file), self.eventloop)
            self.create_app(json_file)
        except RuntimeError:
            pass

    def create_app(self, json_file):
        with open(json_file, "r") as file:
            config = json.load(file)

        cfg = config["application"]
        self.app = Application.from_json(cfg)
        np = self.app.get_object_name("NetworkPort-1")
        addr = HostIP().address
        print(addr)
        normal = NormalLinkLayer(addr)

        self.app.nsap.bind(normal, address=addr)

        # pick out the BVLL service access point from the local adapter
        local_adapter = self.app.nsap.local_adapter

        assert local_adapter
        bvll_sap = local_adapter.clientPeer

        # only IPv4 for now
        if isinstance(bvll_sap, BVLLServiceAccessPoint):
            # create a BVLL application service element
            bvll_ase = BVLLServiceElement()
            bind(bvll_ase, bvll_sap)
