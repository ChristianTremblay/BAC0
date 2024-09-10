#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Lite is the base class to create a BACnet network
It uses provided args to register itself as a device in the network
and allow communication with other devices.

"""
import asyncio
import typing as t

# --- standard Python modules ---
import weakref

from bacpypes3 import __version__ as bacpypes_version
from bacpypes3.app import Application
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier

from BAC0.core.app.asyncApp import BAC0Application
from BAC0.scripts.Base import Base

from ..core.devices.Device import RPDeviceConnected, RPMDeviceConnected
from ..core.devices.Points import Point
from ..core.devices.Trends import TrendLog
from ..core.devices.Virtuals import VirtualPoint
from ..core.functions.Alias import Alias

# from ..core.functions.legacy.cov import CoV
# from ..core.functions.legacy.DeviceCommunicationControl import (
#    DeviceCommunicationControl,
# )
from ..core.functions.Discover import Discover
from ..core.functions.EventEnrollment import EventEnrollment
from ..core.functions.GetIPAddr import HostIP
from ..core.functions.Reinitialize import Reinitialize

# from ..core.functions.legacy.Reinitialize import Reinitialize
from ..core.functions.Schedule import Schedule
from ..core.functions.Text import TextMixin
from ..core.functions.TimeSync import TimeSync
from ..core.io.IOExceptions import (
    NoResponseFromController,
    NumerousPingFailures,
    Timeout,
    UnrecognizedService,
)
from ..core.io.Read import ReadProperty
from ..core.io.Simulate import Simulation
from ..core.io.Write import WriteProperty
from ..core.utils.lookfordependency import influxdb_if_available, rich_if_available

# from ..core.io.asynchronous.Write import WriteProperty
from ..core.utils.notes import note_and_log
from ..infos import __version__ as version

# --- this application's modules ---
from ..tasks.RecurringTask import RecurringTask
from ..tasks.TaskManager import Task

INFLUXDB, _ = influxdb_if_available()
if INFLUXDB:
    from ..db.influxdb import InfluxDB
RICH, rich = rich_if_available()
if RICH:
    from rich import pretty
    from rich.console import Console
    from rich.table import Table

    pretty.install()


# ------------------------------------------------------------------------------


@note_and_log
class Lite(
    Base,
    Discover,
    Alias,
    EventEnrollment,
    ReadProperty,
    WriteProperty,
    Simulation,
    TimeSync,
    Reinitialize,
    # DeviceCommunicationControl,
    # CoV,
    Schedule,
    # Calendar,
    TextMixin,
):
    """
    Build a BACnet application to accept read and write requests.
    [Basic Whois/IAm functions are implemented in parent BasicScript class.]
    Once created, execute a whois() to build a list of available controllers.
    Initialization requires information on the local device.

    :param ip='127.0.0.1': Address must be in the same subnet as the BACnet network
        [BBMD and Foreign Device - not supported]

    """

    def __init__(
        self,
        ip: t.Optional[str] = None,
        port: t.Optional[int] = None,
        mask: t.Optional[int] = None,
        bbmdAddress=None,
        bbmdTTL: int = 0,
        bdtable=None,
        ping: bool = True,
        ping_delay: int = 300,
        db_params: t.Optional[t.Dict[str, t.Any]] = None,
        **params,
    ) -> None:
        self._initialized = False
        self.log(
            f"Starting Asynchronous BAC0 version {version} ({self.__module__.split('.')[-1]})",
            level="info",
        )
        self.log(f"Using bacpypes3 version {bacpypes_version}", level="info")
        self.log("Use BAC0.log_level to adjust verbosity of the app.", level="info")
        self.log(
            "Ex. BAC0.log_level('silence') or BAC0.log_level('error')", level="info"
        )

        self.log("Configurating app", level="debug")
        self._registered_devices = weakref.WeakValueDictionary()

        # Ping task will deal with all registered device and disconnect them if they do not respond.

        self._ping_task = RecurringTask(
            self.ping_registered_devices, delay=ping_delay, name="Ping Task"
        )
        if ping:
            self._ping_task.start()

        if ip is None:
            host = HostIP(port)
            mask = host.mask
            ip_addr = host.address
        else:
            try:
                ip, subnet_mask_and_port = ip.split("/")
                try:
                    mask_s, port_s = subnet_mask_and_port.split(":")
                    mask = int(mask_s)
                    port = int(port_s)
                except ValueError:
                    mask = int(subnet_mask_and_port)
            except ValueError:
                ip = ip

            if not mask:
                mask = 24
            if not port:
                port = 47808
            ip_addr = Address(f"{ip}/{mask}:{port}")
        self._log.info(
            f"Using ip : {ip_addr}/{mask} on port {ip_addr.addrPort} | broadcast : {ip_addr.addrBroadcastTuple[0]}"
        )

        Base.__init__(
            self,
            localIPAddr=ip_addr,
            bbmdAddress=bbmdAddress,
            bbmdTTL=bbmdTTL,
            bdtable=bdtable,
            **params,
        )
        self.log(f"Device instance (id) : {self.Boid}", level="info")
        self.bokehserver = False
        self._points_to_trend = weakref.WeakValueDictionary()

        # Do what's needed to support COV
        # self._update_local_cov_task = namedtuple(
        #    "_update_local_cov_task", ["task", "running"]
        # )
        # self._update_local_cov_task.task = Update_local_COV(
        #    self, delay=1, name="Update Local COV Task"
        # )
        # self._update_local_cov_task.task.start()
        # self._update_local_cov_task.running = True
        # self.log("Update Local COV Task started (required to support COV)", level="info")

        # Activate InfluxDB if params are available
        if db_params and INFLUXDB:
            try:
                self.database = (
                    InfluxDB(db_params)
                    if db_params["name"].lower() == "influxdb"
                    else None
                )
                asyncio.create_task(
                    asyncio.wait_for(self.database._health(), timeout=5)
                )
            except TimeoutError:
                self._log.error(
                    "Unable to connect to InfluxDB. Please validate parameters"
                )
        if self.database:
            self.create_save_to_influxdb_task(delay=20)

        # Announce yourself

        self.i_am()

    def i_am(self):
        loop = asyncio.get_running_loop()
        loop.create_task(self._i_am())

    async def _i_am(self) -> None:
        while self.this_application.app is None or not asyncio.iscoroutinefunction(
            self.this_application.app.i_am
        ):
            await asyncio.sleep(0.01)
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app

        _res = await self.this_application.app.i_am()
        self._initialized = True

    def create_save_to_influxdb_task(self, delay: int = 60) -> None:
        self._write_to_db = RecurringTask(
            self.save_registered_devices_to_db,
            delay=60,
            name="Write to InfluxDB Task",
        )
        self._write_to_db.start()

    async def save_registered_devices_to_db(self):
        if len(self.registered_devices) > 0:
            for each in self.registered_devices:
                try:
                    await self.database.write_points_lastvalue_to_db(each.points)
                except Exception as error:
                    self._log.error(
                        f"Error writing points of {each} to InfluxDB : {error}. Stopping task."
                    )
                    await self._write_to_db.stop()
                    self.log(
                        "Write to InfluxDB Task stopped. Restarting", level="warning"
                    )
                    self.create_save_to_influxdb_task(delay=20)

    def register_device(
        self, device: t.Union[RPDeviceConnected, RPMDeviceConnected]
    ) -> None:
        oid = id(device)
        self._registered_devices[oid] = device

    async def ping_registered_devices(self) -> None:
        """
        Registered device on a network (self) are kept in a list (registered_devices).
        This function will allow pinging thoses device regularly to monitor them. In case
        of disconnected devices, we will disconnect the device (which will save it). Then
        we'll ping again until reconnection, where the device will be bring back online.

        To permanently disconnect a device, an explicit device.disconnect(unregister=True [default value])
        will be needed. This way, the device won't be in the registered_devices list and
        BAC0 won't try to ping it.
        """
        for each in self.registered_devices:
            if isinstance(each, RPDeviceConnected) or isinstance(
                each, RPMDeviceConnected
            ):
                try:
                    self._log.debug(
                        f"Ping {each.properties.name}|{each.properties.address}"
                    )
                    await each.ping()
                    if each.properties.ping_failures > 3:
                        raise NumerousPingFailures

                except NumerousPingFailures:
                    self._log.warning(
                        "{}|{} is offline, disconnecting it.".format(
                            each.properties.name, each.properties.address
                        )
                    )
                    await each._disconnect(unregister=False)

            else:
                device_id = each.properties.device_id
                addr = each.properties.address
                name = await self.read(f"{addr} device {device_id} objectName")
                if name == each.properties.name:
                    each.properties.ping_failures = 0
                    self._log.info(
                        "{}|{} is back online, reconnecting.".format(
                            each.properties.name, each.properties.address
                        )
                    )
                    each.connect(network=self)
                    each.poll(delay=each.properties.pollDelay)

    @property
    def registered_devices(self):
        """
        Devices that have been created using BAC0.device(args)
        """
        return list(self._registered_devices.values())

    def unregister_device(self, device):
        """
        Remove from the registered list
        """
        oid = id(device)
        try:
            del self._registered_devices[oid]
        except KeyError:
            pass

    def add_trend(self, point_to_trend: t.Union[Point, TrendLog, VirtualPoint]) -> None:
        """
        Add point to the list of histories that will be handled by Bokeh

        Argument provided must be of type Point or TrendLog
        ex. bacnet.add_trend(controller['point_name'])
        """
        if (
            isinstance(point_to_trend, Point)
            or isinstance(point_to_trend, TrendLog)
            or isinstance(point_to_trend, VirtualPoint)
        ):
            oid = id(point_to_trend)
            self._points_to_trend[oid] = point_to_trend
        else:
            raise TypeError("Please provide point containing history")

    def remove_trend(
        self, point_to_remove: t.Union[Point, TrendLog, VirtualPoint]
    ) -> None:
        """
        Remove point from the list of histories that will be handled by Bokeh

        Argument provided must be of type Point or TrendLog
        ex. bacnet.remove_trend(controller['point_name'])
        """
        if (
            isinstance(point_to_remove, Point)
            or isinstance(point_to_remove, TrendLog)
            or isinstance(point_to_remove, VirtualPoint)
        ):
            oid = id(point_to_remove)
        else:
            raise TypeError("Please provide point or trendLog containing history")
        if oid in self._points_to_trend.keys():
            del self._points_to_trend[oid]

    @property
    async def devices(self):
        await self._devices(_return_list=False)

    async def _devices(
        self, _return_list: bool = False
    ) -> t.List[t.Tuple[str, str, str, int]]:
        """
        This property will create a good looking table of all the discovered devices
        seen on the network.

        For that, some requests will be sent over the network to look for name,
        manufacturer, etc and in big network, this could be a long process.
        """

        lst = []
        if self.discoveredDevices is not None:
            for k, v in self.discoveredDevices.items():
                objid, device_address, network_number, vendor_id, vendor_name = (
                    v["object_instance"],
                    v["address"],
                    v["network_number"],
                    v["vendor_id"],
                    v["vendor_name"],
                )
                devId = objid[1]
                try:
                    deviceName, vendorName = await self.readMultiple(
                        f"{device_address} device {devId} objectName vendorName"
                    )
                except (UnrecognizedService, ValueError):
                    self._log.warning(
                        f"Unrecognized service for {devId} | {device_address}"
                    )
                    try:
                        deviceName = await self.read(
                            f"{device_address} device {devId} objectName"
                        )
                        vendorName = await self.read(
                            f"{device_address} device {devId} vendorName"
                        )
                    except NoResponseFromController:
                        self.log(f"No response from {k}", level="warning")
                        continue
                except (NoResponseFromController, Timeout):
                    self.log(f"No response from {k}", level="warning")
                    continue
                lst.append(
                    (deviceName, vendorName, devId, device_address, network_number)
                )
            if RICH:
                console = Console()
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Network_number")
                table.add_column("Device Name")
                table.add_column("Address")
                table.add_column("Device Instance")
                table.add_column("Vendor Name")
                for each in lst:
                    deviceName, vendorName, devId, device_address, network_number = each
                    table.add_row(
                        f"{network_number}",
                        f"{deviceName}",
                        f"{device_address}",
                        f"{devId}",
                        f"{vendorName}",
                    )
                console.print(table)
        if _return_list:
            return lst  # type: ignore[return-value]

    @property
    def trends(self) -> t.List[t.Any]:
        """
        This will present a list of all registered trends used by Bokeh Server
        """
        return list(self._points_to_trend.values())

    @property
    def tasks(self) -> t.List[Task]:
        """
        This will present a list of all registered tasks
        """
        return Task.tasks

    def disconnect(self) -> None:
        asyncio.create_task(self._disconnect())

    async def _disconnect(self) -> None:
        self.log("Disconnecting", level="debug")
        for each in self.registered_devices:
            await each._disconnect()
        await super()._disconnect()
        self._initialized = False

    def __repr__(self) -> str:
        return f"Bacnet Network using ip {self.localIPAddr} with device id {self.Boid}"

    def __getitem__(self, boid_or_localobject: t.Union[str, ObjectIdentifier, tuple]):
        """
        Retrieve an item from the application by its name or identifier.

        Args:
            boid_or_localobject (Union[str, ObjectIdentifier]): The name (as a string) or identifier (as an ObjectIdentifier) of the object to retrieve.

        Returns:
            Union[YourObjectType, None]: The object corresponding to the given name or identifier, or a registered device if the identifier matches a device ID. Returns None if the object or device is not found.

        Raises:
            KeyError: If the object or device is not found and logging is not enabled.
        """
        if isinstance(boid_or_localobject, str):
            item = self.this_application.app.objectName[boid_or_localobject]
        elif isinstance(boid_or_localobject, ObjectIdentifier):
            item = self.this_application.app.objectIdentifier[boid_or_localobject]
        elif isinstance(boid_or_localobject, tuple):
            _objId = ObjectIdentifier(boid_or_localobject)
            item = self.this_application.app.objectIdentifier[_objId]
        if item is None:
            for device in self._registered_devices:
                if str(device.properties.device_id) == str(boid_or_localobject):
                    return device
            self.log(f"{boid_or_localobject} not found", level="error")
        else:
            return item

    async def __aenter__(self):
        while not self._initialized:
            await asyncio.sleep(0.1)
        self._log.info(
            f"{self.localObjName}|{self.Boid} connected. Entering context manager."
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._disconnect()
        while self._initialized:
            await asyncio.sleep(0.1)
        self._log.info(
            f"{self.localObjName}|{self.Boid} disconnected. Exiting context manager."
        )

    def get_device_by_id(self, id):
        for each in self.registered_devices:
            if each.properties.device_id == id:
                return each
        self._log.error(f"Device {id} not found")
        raise ValueError("Device not found")
