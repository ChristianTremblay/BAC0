#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Utility function to retrieve a functionnal IP and a correct broadcast IP
address.
Goal : not use 255.255.255.255 as a broadcast IP address as it is not
accepted by every devices (>3.8.38.1 bacnet.jar of Tridium Jace for example)

"""
from bacpypes.pdu import Address

from ..io.IOExceptions import NetworkInterfaceException

import socket
import subprocess
import ipaddress
import sys
import re
from ...core.utils.notes import note_and_log


@note_and_log
class HostIP:
    """
    Special class to identify host IP informations
    """

    def __init__(self, port=47808):
        ip = self._findIPAddr()
        mask = self._findSubnetMask(ip)
        self._port = port
        self.interface = ipaddress.IPv4Interface("{}/{}".format(ip, mask))

    @property
    def ip_address_subnet(self):
        """
        IP Address/subnet
        """
        return "{}/{}".format(
            self.interface.ip.compressed, self.interface.exploded.split("/")[-1]
        )

    @property
    def ip_address(self):
        """
        IP Address/subnet
        """
        return "{}".format(self.interface.ip.compressed)

    @property
    def address(self):
        """
        IP Address using bacpypes Address format
        """
        port = ""
        if self._port:
            port = ":{}".format(self._port)
        return Address(
            "{}/{}{}".format(
                self.interface.ip.compressed,
                self.interface.exploded.split("/")[-1],
                port,
            )
        )

    @property
    def mask(self):
        """
        Subnet mask
        """
        return self.interface.exploded.split("/")[-1]

    @property
    def port(self):
        """
        IP Port used
        """
        return self._port

    def _findIPAddr(self):
        """
        Retrieve the IP address connected to internet... used as
        a default IP address when defining Script

        :returns: IP Adress as String
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("google.com", 0))
            addr = s.getsockname()[0]
            s.close()
        except socket.error:
            raise NetworkInterfaceException(
                "Impossible to retrieve IP, please provide one manually"
            )
        return addr

    def _findSubnetMask(self, ip):
        """
        Retrieve the broadcast IP address connected to internet... used as
        a default IP address when defining Script

        :param ip: (str) optionnal IP address. If not provided, default to getIPAddr()
        
        :returns: broadcast IP Adress as String
        """
        try:
            import netifaces

            interfaces = netifaces.interfaces()
            for nic in interfaces:
                addresses = netifaces.ifaddresses(nic)
                try:
                    for address in addresses[netifaces.AF_INET]:
                        if address["addr"] == ip:
                            return address["netmask"]
                except KeyError:
                    pass

            return "255.255.255.255"
        except ImportError:
            self._log.warning(
                "Netifaces not installed on your system. BAC0 can't detect the subnet.\nPlease provide subnet for now, we'll consider 255.255.255.0 (/24).\nYou can install netifaces using 'pip install netifaces'."
            )
            return "255.255.255.0"


def validate_ip_address(ip):
    result = True
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if not isinstance(ip, Address):
            raise ValueError("Provide Address as bacpypes.Address object")
        s.bind(ip.addrTuple)
    except OSError as error:
        result = False
    finally:
        s.close()
    return result
