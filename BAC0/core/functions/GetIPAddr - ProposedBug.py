#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
GetIPAddr.py - Utility functions to retrieve local host's IP information.
'''

#--- standard Python modules ---
import subprocess
import ipaddress
import sys

#--- 3rd party modules ---
from bacpypes.pdu import Address

#--- this application's modules ---

#------------------------------------------------------------------------------

class HostIP():
    """
    Identify host's  IP information
    """
    def __init__(self, ip=None, mask = None):
        if 'win' in sys.platform:
            proc = subprocess.Popen('ipconfig', stdout=subprocess.PIPE)
            for l in proc.stdout:
                line= str(l)
                if 'Address' in line:
                    ip= line.split(':')[-1]
                if 'Mask' in line:
                    mask= line.split(':')[-1]

            self.interface = ipaddress.IPv4Interface('%r/%s' % (ip, mask))
        else:
            proc = subprocess.Popen('ifconfig', stdout=subprocess.PIPE)
            for l in proc.stdout:
                line= l.decode('utf-8')
                if 'Bcast' in line:
                    _,ipaddr,bcast,mask= line.split()
                    _,ip= ipaddr.split(':')
                    _,mask= mask.split(':')

                    self.interface = ipaddress.IPv4Interface('{}/{}'.format(ip, mask))
                    break 
        self.interface = ipaddress.IPv4Interface('{}/{}'.format(ip, mask))
    
    @property    
    def ip_address(self):
        return str(self.interface)              # IP Address/subnet

    @property
    def address(self):
        return (Address(str(self.interface)))   # bacpypes format: ip


if __name__ == '__main__':
    h = HostIP()
    print('Localhost IP address= ',h.ip_address)
