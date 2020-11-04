#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Match.py - verify a point's status matches its commanded value.

Example:
    Is a fan commanded to 'On' actually 'running'?
"""

# --- standard Python modules ---
# --- 3rd party modules ---

# --- this application's modules ---
from .TaskManager import Task
from ..core.io.IOExceptions import BadDeviceDefinition
from ..core.devices.Device import Device
from ..core.utils.notes import note_and_log

"""
A way to define a BAC0.device using a task, so it won't block the Notebook or the REPL
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

        name = "Adding_Device_{}|{}".format(self.address, self.boid)
        self.callback = callback
        self._kwargs["address"] = self.address
        self._kwargs["device_id"] = self.boid
        self._kwargs["network"] = network
        super().__init__(name=name, delay=0)
        # self.start()

    def find_address(self, address, boid):
        if self.network.discoveredDevices is None:
            self._log.error(
                "Device cannot be created yet, use bacnet.discover() or provide both address and Boid"
            )
            raise DeviceNotFoundError(
                "Device cannot be created yet, use bacnet.discover() or provide both address and Boid"
            )
        else:
            for each in self.network.discoveredDevices:
                address, boid = each
                if address in str(address) or boid in str(boid):
                    self._log.info("Found {}".format(each))
                    return each
        self._log.error(
            "Device not discovered yet, use bacnet.discover() or provide both address and Boid"
        )

    def task(self, **kwargs):
        try:
            self._log.info(kwargs)
            dev = Device(kwargs)
            self._log.info(
                "Device named {} ({}/{}) created. Retrieve it using bacnet[boid]".format(
                    dev.properties.name,
                    dev.properties.address,
                    dev.properties.device_id,
                )
            )
            if self.callback is not None:
                self._log.info("Executing callback for {}".format(dev.properties.name))
                self.callback()
        except BadDeviceDefinition as error:
            self._log.error("Bad device definition ({})".format(error))


class DeviceNotFoundError(Exception):
    pass
