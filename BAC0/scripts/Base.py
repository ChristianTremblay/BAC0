#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
BasicScript - implement the BAC0.core.app.ScriptApplication
Its basic function is to start and stop the bacpypes stack.
Stopping the stack, frees the IP socket used for BACnet communications.
No communications will occur if the stack is stopped.

Bacpypes stack enables Whois and Iam functions, since this minimum is needed to be
a BACnet device.  Other stack services can be enabled later (via class inheritance).
[see: see BAC0.scripts.ReadWriteScript]

Class::
    BasicScript(WhoisIAm)
        def startApp()
        def stopApp()
"""
# --- standard Python modules ---
from threading import Thread
import random
import sys

# --- 3rd party modules ---

from bacpypes.core import run as startBacnetIPApp
from bacpypes.core import stop as stopBacnetIPApp
from bacpypes.core import enable_sleeping
from bacpypes.local.device import LocalDeviceObject
from bacpypes.basetypes import ServicesSupported, DeviceStatus
from bacpypes.primitivedata import CharacterString

# --- this application's modules ---
from ..core.app.ScriptApplication import (
    BAC0Application,
    BAC0ForeignDeviceApplication,
    BAC0BBMDDeviceApplication,
)
from .. import infos
from ..core.io.IOExceptions import InitializationError, UnknownObjectError
from ..core.functions.GetIPAddr import validate_ip_address
from ..tasks.TaskManager import stopAllTasks

from ..core.utils.notes import note_and_log

try:
    import pandas
    import bokeh
    import flask
    import flask_bootstrap

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

    _used_ips = set()

    def __init__(
        self,
        localIPAddr="127.0.0.1",
        localObjName="BAC0",
        deviceId=None,
        firmwareRevision="".join(sys.version.split("|")[:2]),
        maxAPDULengthAccepted="1024",
        maxSegmentsAccepted="1024",
        segmentationSupported="segmentedBoth",
        bbmdAddress=None,
        bbmdTTL=0,
        bdtable=None,
        modelName=CharacterString("BAC0 Scripting Tool"),
        vendorId=842,
        vendorName=CharacterString("SERVISYS inc."),
        description=CharacterString("http://christiantremblay.github.io/BAC0/"),
    ):

        self._log.debug("Configurating app")

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

        self.Boid = (
            int(deviceId) if deviceId else (3056177 + int(random.uniform(0, 1000)))
        )

        self.segmentationSupported = segmentationSupported
        self.maxSegmentsAccepted = maxSegmentsAccepted
        self.localObjName = localObjName
        self.local_objects = LocalObjects(device=self)

        self.maxAPDULengthAccepted = maxAPDULengthAccepted
        self.vendorId = vendorId
        self.vendorName = vendorName
        self.modelName = modelName
        self.description = description

        self.discoveredDevices = None
        self.systemStatus = DeviceStatus(1)

        self.bbmdAddress = bbmdAddress
        self.bbmdTTL = bbmdTTL
        self.bdtable = bdtable

        self.firmwareRevision = firmwareRevision
        self._ric = {}
        self.subscription_contexts = {}

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
            # make a device object
            self.this_device = LocalDeviceObject(
                objectName=self.localObjName,
                objectIdentifier=self.Boid,
                maxApduLengthAccepted=int(self.maxAPDULengthAccepted),
                segmentationSupported=self.segmentationSupported,
                vendorIdentifier=self.vendorId,
                vendorName=self.vendorName,
                modelName=self.modelName,
                systemStatus=self.systemStatus,
                description=self.description,
                firmwareRevision=self.firmwareRevision,
                applicationSoftwareVersion=infos.__version__,
                protocolVersion=1,
                protocolRevision=0,
            )

            # make an application
            if self.bdtable:
                self.this_application = BAC0BBMDDeviceApplication(
                    self.this_device,
                    self.localIPAddr,
                    bdtable=self.bdtable,
                    iam_req=self._iam_request(),
                    subscription_contexts=self.subscription_contexts,
                )
                app_type = "BBMD Device"
            elif self.bbmdAddress and self.bbmdTTL > 0:

                self.this_application = BAC0ForeignDeviceApplication(
                    self.this_device,
                    self.localIPAddr,
                    bbmdAddress=self.bbmdAddress,
                    bbmdTTL=self.bbmdTTL,
                    iam_req=self._iam_request(),
                    subscription_contexts=self.subscription_contexts,
                )
                app_type = "Foreign Device"
            else:
                self.this_application = BAC0Application(
                    self.this_device,
                    self.localIPAddr,
                    iam_req=self._iam_request(),
                    subscription_contexts=self.subscription_contexts,
                )
                app_type = "Simple BACnet/IP App"
            self._log.debug("Starting")
            self._initialized = True
            try:
                self._startAppThread()
                Base._used_ips.add(self.localIPAddr)
                self._log.info("Registered as {}".format(app_type))
            except OSError as error:
                self._log.warning("Error opening socket: {}".format(error))
                raise InitializationError("Error opening socket: {}".format(error))
            self._log.debug("Running")
        except OSError as error:
            self._log.error("an error has occurred: {}".format(error))
            raise InitializationError("Error starting app: {}".format(error))
        finally:
            self._log.debug("finally")

    def register_foreign_device(self, addr=None, ttl=0):
        self.this_application.bip.register(addr, ttl)

    def unregister_foreign_device(self):
        self.this_application.bip.unregister()

    def disconnect(self):
        """
        Stop the BACnet stack.  Free the IP socket.
        """
        self._log.debug("Stopping All running tasks")
        stopAllTasks()
        self._log.debug("Stopping BACnet stack")
        # Freeing socket
        try:
            self.this_application.mux.directPort.handle_close()
        except:
            self.this_application.mux.broadcastPort.handle_close()

        stopBacnetIPApp()  # Stop Core
        self._stopped = True  # Stop stack thread
        self.t.join()
        self._started = False
        Base._used_ips.remove(self.localIPAddr)
        self._log.info("BACnet stopped")

    def _startAppThread(self):
        """
        Starts the BACnet stack in its own thread so requests can be processed.
        As signal cannot be called in another thread than the main thread
        when calling startBacnetIPApp, we must pass None to both parameters
        """
        self._log.info("Starting app...")
        enable_sleeping(0.0005)
        self.t = Thread(
            target=startBacnetIPApp,
            kwargs={"sigterm": None, "sigusr1": None},
            daemon=True,
        )
        try:
            self.t.start()
            self._started = True
            self._log.info("BAC0 started")
        except OSError:
            stopBacnetIPApp()
            self.t.join()
            raise

    @property
    def discoveredNetworks(self):
        return self.this_application.nse._learnedNetworks or set()

    #    @property
    #    def routing_table(self):
    #        return self.this_application.nse._routing_table or {}

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
        ric = self.this_application.nsap.router_info_cache

        for networks, routers in ric.routers.items():
            for address, router in routers.items():
                self._routers[str(address)] = Router(router, index=networks)
        for path, router in ric.path_info.items():
            self._routers[str(router.address)].path = path

        return self._routers
