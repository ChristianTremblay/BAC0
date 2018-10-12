#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
ReadWriteScript - extended version of BasicScript.py

As everything is handled by the BasicScript, select the additional features you want::

    # Create a class that implements a basic script with read and write functions
    from BAC0.scripts.BasicScript import BasicScript
    from BAC0.core.io.Read import ReadProperty
    from BAC0.core.io.Write import WriteProperty
    class ReadWriteScript(BasicScript,ReadProperty,WriteProperty)

Once the class is created, create the local object and use it::

    bacnet = ReadWriteScript(localIPAddr = '192.168.1.10')
    bacnet.read('2:5 analogInput 1 presentValue)

'''
#--- standard Python modules ---
import time
from datetime import datetime
import weakref


#--- this application's modules ---
from ..scripts.Base import Base

from ..core.io.Read import ReadProperty
from ..core.io.Write import WriteProperty
from ..core.functions.GetIPAddr import HostIP
from ..core.functions.WhoisIAm import WhoisIAm
from ..core.io.Simulate import Simulation
from ..core.devices.Points import Point
from ..core.devices.Trends import TrendLog
from ..core.utils.notes import note_and_log
from ..core.io.IOExceptions import NoResponseFromController, UnrecognizedService


from ..infos import __version__ as version

from bacpypes.pdu import Address

#------------------------------------------------------------------------------


@note_and_log
class Lite(Base, WhoisIAm, ReadProperty, WriteProperty, Simulation):
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

    def __init__(self, ip=None, port=None, mask = None, bbmdAddress=None, bbmdTTL=0):
        self._log.info("Starting BAC0 version {} ({})".format(
            version, self.__module__.split('.')[-1]))
        self._log.debug("Configurating app")
        self._registered_devices = weakref.WeakValueDictionary()
        if ip is None:
            host = HostIP(port)
            ip_addr = host.address
        else:
            try:
                ip, subnet_mask_and_port = ip.split('/')
            except ValueError:
                ip = ip

            if not mask:
                mask = 24
            if not port:
                port = 47808
            
            ip_addr = Address('{}/{}:{}'.format(ip,mask, port))
        self._log.info('Using ip : {ip_addr}'.format(ip_addr=ip_addr))
        Base.__init__(self, localIPAddr=ip_addr,
                      bbmdAddress=bbmdAddress, bbmdTTL=bbmdTTL)

        self.bokehserver = False
        self._points_to_trend = weakref.WeakValueDictionary()
        # Force a global whois to find all devices on the network
        # This also allow to see devices quickly after creation of network
        # as a first read has already been done.
        self.whois_answer = self.update_whois()
        time.sleep(2)

    def update_whois(self):
        return (self.whois(), str(datetime.now()))

    def register_device(self, device):
        oid = id(device)
        self._registered_devices[oid] = device

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

    def add_trend(self, point_to_trend):
        """
        Add point to the list of histories that will be handled by Bokeh

        Argument provided must be of type Point or TrendLog
        ex. bacnet.add_trend(controller['point_name'])
        """
        if isinstance(point_to_trend, Point):
            oid = id(point_to_trend)
            self._points_to_trend[oid] = point_to_trend
        elif isinstance(point_to_trend, TrendLog):
            oid = id(point_to_trend)
            self._points_to_trend[oid] = point_to_trend        
        else:
            raise TypeError('Please provide point containing history')

    def remove_trend(self, point_to_remove):
        """
        Remove point from the list of histories that will be handled by Bokeh

        Argument provided must be of type Point or TrendLog
        ex. bacnet.remove_trend(controller['point_name'])
        """
        if isinstance(point_to_remove, Point):
            oid = id(point_to_remove)
        elif isinstance(point_to_remove, TrendLog):
            oid = id(point_to_remove)
        else:
            raise TypeError('Please provide point or trendLog containing history')
        if oid in self._points_to_trend.keys():
            del self._points_to_trend[oid]

    @property
    def devices(self):
        lst = []
        for device in list(self.discoveredDevices):
            try:
                deviceName, vendorName = self.readMultiple(
                    '{} device {} objectName vendorName'.format(device[0], device[1]))
            except UnrecognizedService:
                print(device[0])
                print(device[1])
                deviceName = self.read(
                    '{} device {} objectName'.format(device[0], device[1]))
                vendorName = self.read(
                    '{} device {} vendorName'.format(device[0], device[1]))
            except NoResponseFromController:
                self._log.warning('No response from {}'.format(device))
                continue
            lst.append((deviceName, vendorName, device[0], device[1]))
        return lst

    def find_devices_on_network(self, net=None):
        d = {}
        networks = set()
        all_devices = self.whois()
        for each in all_devices:
            address, devID = each
            try:
                network = address.split(':')[0]
                mac = int(address.split(':')[1])
            except (ValueError, IndexError):
                network = 'ip'
                mac = address
            networks.add(network)
            if not network in d.keys():
                d[network] = []
            d[network].append((mac, devID))
        if net:
            net = str(net)
            try:
                return d[net]
            except (ValueError, KeyError):
                self._log.warning('Nothing there...')
                return
        return (networks, d)

    @property
    def trends(self):
        """
        This will present a list of all registered trends used by Bokeh Server
        """
        return list(self._points_to_trend.values())

    def disconnect(self):
        super().disconnect()

    def __repr__(self):
        return 'Bacnet Network using ip %s with device id %s' % (self.localIPAddr, self.Boid)
