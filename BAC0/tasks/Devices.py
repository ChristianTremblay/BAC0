#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#

# --- standard Python modules ---
# --- 3rd party modules ---

from ..core.devices.Device import Device
from ..core.io.IOExceptions import BadDeviceDefinition

# --- this application's modules ---
from .TaskManager import Task

"""
A way to define a BAC0.device using a task, so it won't block the Notebook or the REPL
TODO : check if still required, maybe deprecated
"""


class AddDevice(Task):
    def __init__(self, address=None, boid=None, network=None, callback=None, **kwargs):
        if network is None:
            raise ValueError("Please provide network")
        else:
            self.network = network
        self._kwargs = kwargs

        if address is not None and boid is not None:
            self.address = address
            self.boid = boid
        else:
            self.address, self.boid = self.find_address(address, boid)

        name = f"Adding_Device_{self.address}|{self.boid}"
        self.callback = callback
        self._kwargs["address"] = self.address
        self._kwargs["device_id"] = self.boid
        self._kwargs["network"] = network
        super().__init__(name=name, delay=0)
        # self.start()

    def find_address(self, address, boid):
        if self.network.discoveredDevices is None:
            self.log(
                "Device cannot be created yet, use bacnet.discover() or provide both address and Boid",
                level="error",
            )
            raise DeviceNotFoundError(
                "Device cannot be created yet, use bacnet.discover() or provide both address and Boid"
            )
        else:
            for each in self.network.discoveredDevices:
                address, boid = each
                if address in str(address) or boid in str(boid):
                    self.log(f"Found {each}", level="info")
                    return each
        self.log(
            "Device not discovered yet, use bacnet.discover() or provide both address and Boid",
            level="error",
        )

    def task(self, **kwargs):
        try:
            self.log(kwargs, level="info")
            dev = Device(kwargs)
            self.log(
                f"Device named {dev.properties.name} ({dev.properties.address}/{dev.properties.device_id}) created. Retrieve it using bacnet[boid]",
                level="info",
            )
            if self.callback is not None:
                self.log(f"Executing callback for {dev.properties.name}", level="info")
                self.callback()
        except BadDeviceDefinition as error:
            self.log(f"Bad device definition ({error})", level="error")


class DeviceNotFoundError(Exception):
    pass
