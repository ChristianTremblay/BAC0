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

class HostIP():
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
        return ('{}/{}'.format(self.interface.ip.compressed,
                           self.interface.exploded.split('/')[-1]))
    @property    
    def ip_address(self):
        """
        IP Address/subnet
        """
        return '{}'.format(self.interface.ip.compressed)


    @property
    def address(self):
        """
        IP Address using bacpypes Address format
        """
        port = ''
        if self._port:
            port = ':{}'.format(self._port)
        return (Address('{}/{}{}'.format(self.interface.ip.compressed,
                                   self.interface.exploded.split('/')[-1],
                                   port)))

    @property
    def mask(self):
        """
        Subnet mask
        """
        return self.interface.exploded.split('/')[-1]

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
            s.connect(('google.com', 0))
            addr = s.getsockname()[0]
            #print('Using ip : {addr}'.format(addr=addr))
            s.close()
        except socket.error:
            raise NetworkInterfaceException(
                'Impossible to retrieve IP, please provide one manually')
        return addr

    def _findSubnetMask(self, ip):
        """
        Retrieve the broadcast IP address connected to internet... used as
        a default IP address when defining Script

        :param ip: (str) optionnal IP address. If not provided, default to getIPAddr()
        :param mask: (str) optionnal subnet mask. If not provided, will try to find one using ipconfig (Windows) or ifconfig (Linux or MAC)

        :returns: broadcast IP Adress as String
        """
        ip = ip

        if 'win32' in sys.platform:
            try:
                proc = subprocess.Popen('ipconfig', stdout=subprocess.PIPE)
                while True:
                    line = proc.stdout.readline()
                    if ip.encode() in line:
                        break
                mask = proc.stdout.readline().rstrip().split(
                    b':')[-1].replace(b' ', b'').decode()
            except:
                raise NetworkInterfaceException('Cannot read IP parameters from OS')
        else:
            """
            This procedure could use more direct way of obtaining the broadcast IP
            as it is really simple in Unix
            ifconfig gives Bcast directly for example
            or use something like :
            iface = "eth0"
            socket.inet_ntoa(fcntl.ioctl(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), 35099, struct.pack('256s', iface))[20:24])
            """
            pattern = re.compile(r"(255.\d{1,3}.\d{1,3}.\d{1,3})")

            try:
                proc = subprocess.Popen('ifconfig', stdout=subprocess.PIPE)
                while True:
                    line = proc.stdout.readline()
                    if ip.encode() in line:
                        break
                mask = re.findall(pattern,line.decode())[0]
            except:
                mask = '255.255.255.255'
        #self._log.debug('Mask found : %s' %  mask)
        return mask

