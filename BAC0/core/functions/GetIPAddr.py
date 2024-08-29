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
import ipaddress
import socket
import typing as t
import platform
import subprocess
import re

import struct

# from bacpypes.pdu import Address as legacy_Address
from bacpypes3.pdu import Address

from ...core.utils.notes import note_and_log
from ..io.IOExceptions import NetworkInterfaceException

DEFAULT_PORT = 47808


@note_and_log
class HostIP:
    """
    Special class to identify host IP informations
    """

    def __init__(self, port: t.Optional[int] = None) -> None:
        ip = self._findIPAddr()
        mask = self._findSubnetMask(ip)
        if port is not None:
            self._port = port
        else:
            self._port = DEFAULT_PORT
        self.interface = ipaddress.IPv4Interface(f"{ip}/{mask}")

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
        return f"{self.interface.ip.compressed}"

    @property
    def address(self) -> Address:
        """
        IP Address using bacpypes Address format
        """
        port = ""
        if self._port:
            port = f":{self._port}"
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

    def _findIPAddr(self) -> str:
        """
        Retrieve the IP address connected to internet... used as
        a default IP address when defining Script

        :returns: IP Adress as String
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("google.com", 443))
            addr = s.getsockname()[0]
            s.close()
        except socket.error:
            raise NetworkInterfaceException(
                "Impossible to retrieve IP, please provide one manually"
            )
        return addr

    def _old_findSubnetMask(self, ip: str) -> str:
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
                "Netifaces not installed on your system. BAC0 can't detect the subnet.\nPlease provide subnet for now, "
                "we'll consider 255.255.255.0 (/24).\nYou can install netifaces using 'pip install netifaces'."
            )
            return "255.255.255.0"

    def _findSubnetMask(self, ip: str) -> str:
        """
        Retrieve the broadcast IP address connected to internet... used as
        a default IP address when defining Script

        :param ip: (str) optional IP address. If not provided, default to getIPAddr()

        :returns: broadcast IP Address as String
        """
        if platform.system() == "Windows":
            try:
                # Run the ipconfig command
                result = subprocess.run(["ipconfig"], capture_output=True, text=True)
                output = result.stdout

                # Regular expression to match IP and subnet mask
                ip_pattern = re.compile(r"IPv4 Address[. ]*: ([\d.]+)")
                mask_pattern = re.compile(r"Subnet Mask[. ]*: ([\d.]+)")

                # Parse the output
                lines = output.splitlines()
                for i, line in enumerate(lines):
                    ip_match = ip_pattern.search(line)
                    if ip_match:
                        found_ip = ip_match.group(1)
                        if ip is None or found_ip == ip:
                            # Look for the subnet mask in the next few lines
                            for j in range(i + 1, i + 6):
                                mask_match = mask_pattern.search(lines[j])
                                if mask_match:
                                    return mask_match.group(1)

                return "255.255.255.255"
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
        elif platform.system() == "Linux":
            import fcntl

            def get_interface_info(ifname):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                return fcntl.ioctl(
                    s.fileno(),
                    0x891B,  # SIOCGIFNETMASK
                    struct.pack("256s", ifname[:15].encode("utf-8")),
                )

            try:
                interfaces = socket.if_nameindex()
                for ifindex, ifname in interfaces:
                    try:
                        netmask = socket.inet_ntoa(get_interface_info(ifname)[20:24])
                        ip_address = socket.inet_ntoa(
                            fcntl.ioctl(
                                socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                                0x8915,  # SIOCGIFADDR
                                struct.pack("256s", ifname[:15].encode("utf-8")),
                            )[20:24]
                        )
                        if ip is None or ip_address == ip:
                            return netmask
                    except IOError:
                        pass

                return "255.255.255.255"
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
        else:
            print("Unsupported platform")
            return None


def validate_ip_address(ip: Address) -> bool:
    result = True
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if not isinstance(ip, Address):
            raise ValueError("Provide Address as bacpypes.Address object")
        s.bind(ip.addrTuple)
    except OSError:
        result = False
    finally:
        s.close()
    return result
