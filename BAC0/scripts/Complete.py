#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Complete Script - extended version of Lite Script

As everything is handled by the BasicScript, select the additional features you want::

    # Create a class that implements a basic script with read and write functions
    from BAC0.scripts.BasicScript import BasicScript
    from BAC0.core.io.Read import ReadProperty
    from BAC0.core.io.Write import WriteProperty
    class ReadWriteScript(BasicScript,ReadProperty,WriteProperty)

Once the class is created, create the local object and use it::

    bacnet = ReadWriteScript(localIPAddr = '192.168.1.10')
    bacnet.read('2:5 analogInput 1 presentValue)

"""
# --- standard Python modules ---
from datetime import datetime
import logging
import pandas as pd
import time


# --- 3rd party modules ---
from bokeh.application import Application

# --- this application's modules ---
from ..scripts.Lite import Lite

from ..core.io.IOExceptions import (
    BokehServerCantStart,
    NoResponseFromController,
    UnrecognizedService,
)
from ..core.utils.notes import note_and_log, update_log_level

from ..web.BokehRenderer import (
    DevicesTableHandler,
    DynamicPlotHandler,
    NotesTableHandler,
)
from ..web.BokehServer import Bokeh_Worker
from ..web.FlaskServer import FlaskServer

# ------------------------------------------------------------------------------


class Stats_Mixin:
    """
    Statistics used by Flask App
    """

    @property
    def number_of_devices(self):
        if not self.discoveredDevices:
            return 0
        s = []
        [s.append(x) for x in self.discoveredDevices.items() if x[1] > 0]
        return len(s)

    @property
    def number_of_registered_trends(self):
        if self.trends:
            return len(self.trends)
        else:
            return 0

    def number_of_devices_per_network(self):
        total = float(self.number_of_devices)
        if total == 0:
            return (["No Devices"], ["0"], ["0%%"])
        labels = ["IP"]
        series_pct = ["%.2f %%" % (len(self.network_stats["ip_devices"]) / total * 100)]
        series = [len(self.network_stats["ip_devices"]) / total * 100]
        for each in self.network_stats["mstp_map"].keys():
            labels.append("MSTP #{}".format(each))
            series_pct.append(
                "%.2f %%" % (len(self.network_stats["mstp_map"][each]) / total * 100)
            )
            series.append(len(self.network_stats["mstp_map"][each]) / total * 100)
        return (labels, series, series_pct)

    def print_list(self, lst):
        s = ""
        try:
            s += lst[0]
        except IndexError:
            return s
        try:
            for each in lst[1:]:
                s = s + ", " + each
        except IndexError:
            pass
        return s

    @property
    def network_stats(self):
        """
        Used by Flask to show informations on the network
        """
        statistics = {}
        mstp_networks = []
        mstp_map = {}
        ip_devices = []
        bacoids = []
        mstp_devices = []
        if self.discoveredDevices:
            for address, bacoid in self.discoveredDevices.keys():
                if ":" in address:
                    net, mac = address.split(":")
                    mstp_networks.append(net)
                    mstp_devices.append(mac)
                    try:
                        mstp_map[net].append(mac)
                    except KeyError:
                        mstp_map[net] = []
                        mstp_map[net].append(mac)
                else:
                    net = "ip"
                    mac = address
                    ip_devices.append(address)
                bacoids.append((bacoid, address))
        mstpnetworks = sorted(set(mstp_networks))
        statistics["mstp_networks"] = mstpnetworks
        statistics["ip_devices"] = sorted(ip_devices)
        statistics["bacoids"] = sorted(bacoids)
        statistics["mstp_map"] = mstp_map
        statistics["timestamp"] = str(datetime.now())
        statistics["number_of_devices"] = self.number_of_devices
        statistics["number_of_registered_devices"] = len(self.registered_devices)
        statistics["print_mstpnetworks"] = self.print_list(mstpnetworks)
        return statistics


@note_and_log
class Complete(Lite, Stats_Mixin):
    """
    Build a BACnet application to accept read and write requests.
    [Basic Whois/IAm functions are implemented in parent BasicScript class.]
    Once created, execute a whois() to build a list of available controllers.
    Initialization requires information on the local device.

    :param ip='127.0.0.1': Address must be in the same subnet as the BACnet network
        [BBMD and Foreign Device - not supported]

    :param bokeh_server: (boolean) If set to false, will prevent Bokeh server
        from being started. Can help troubleshoot issues with Bokeh. By default,
        set to True.
    """

    def __init__(
        self,
        ip=None,
        mask=None,
        port=None,
        bbmdAddress=None,
        bbmdTTL=0,
        ping=True,
        bokeh_server=True,
        flask_port=8111,
        **params
    ):
        Lite.__init__(
            self,
            ip=ip,
            mask=mask,
            port=port,
            bbmdAddress=bbmdAddress,
            bbmdTTL=bbmdTTL,
            ping=ping,
            **params
        )
        self.flask_port = flask_port
        if bokeh_server:
            self.start_bokeh()
            self.FlaskServer.start()
        else:
            self._log.warning("Bokeh server not started. Trend feature will not work")
        self.discover()

    @property
    def devices(self):
        lst = []
        for device in list(self.discoveredDevices):
            try:
                deviceName, vendorName = self.readMultiple(
                    "{} device {} objectName vendorName".format(device[0], device[1])
                )
            except UnrecognizedService:
                deviceName = self.read(
                    "{} device {} objectName".format(device[0], device[1])
                )
                vendorName = self.read(
                    "{} device {} vendorName".format(device[0], device[1])
                )
            except NoResponseFromController:
                self._log.info("No response from {}".format(device))
                continue
            lst.append((deviceName, vendorName, device[0], device[1]))
        df = pd.DataFrame(
            lst, columns=["Name", "Manufacturer", "Address", " Device ID"]
        ).set_index("Name")
        try:
            return df.sort_values("Address")
        except AttributeError:
            return df

    def start_bokeh(self):
        try:
            self.note("Starting Bokeh Serve")
            # Need to create the device document here
            devHandler = DevicesTableHandler(self)
            dev_app = Application(devHandler)
            trendHandler = DynamicPlotHandler(self)
            notesHandler = NotesTableHandler(self)
            self.trend_app = Application(trendHandler)
            self.notes_app = Application(notesHandler)
            self.bk_worker = Bokeh_Worker(
                dev_app, self.trend_app, self.notes_app, self.localIPAddr.addrTuple[0]
            )
            self.FlaskServer = FlaskServer(
                network=self, port=self.flask_port, ip=self.localIPAddr.addrTuple[0]
            )
            self.bk_worker.start()
            self.bokehserver = True
            time.sleep(1)
            try:
                logging.getLogger().handlers[0].setLevel(logging.CRITICAL)
            except IndexError:
                # Possibly in Jupyter Notebook... root logger not defined
                pass
            update_log_level("default", log_this=False)
            self._log.info(
                "Server started : http://{}:{}".format(
                    self.localIPAddr.addrTuple[0], self.flask_port
                )
            )

        except OSError as error:
            self.bokehserver = False
            self._log.error(
                "[bokeh serve] required for trending (controller.chart) features"
            )
            self._log.error(error)

        except RuntimeError as rterror:
            self.bokehserver = False
            self._log.warning("Server already running")

        except BokehServerCantStart:
            self.bokehserver = False
            self._log.error("No Bokeh Server - controller.chart not available")

    def __repr__(self):
        return "Bacnet Network using ip {} with device id {} | Featuring Bokeh and Pandas".format(
            self.localIPAddr, self.Boid
        )
