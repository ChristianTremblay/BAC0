# -*- coding: utf-8 -*-
"""
[Ref] : http://zeth.net/archive/2007/11/24/how-to-find-out-ip-address-in-python/

"""

import socket

def getIPAddr():
    """
    Retrieve the IP address connected to internet... used as
    a default IP address when defining Script
    
    :returns: IP Adress as String
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:    
        s.connect(('google.com', 0))
        addr = s.getsockname()[0]
        print('Using ip : {addr}'.format(addr=addr))
        s.close()
    except socket.error :
        print('Not connected to internet, using default IP Addr : 127.0.0.1')
        addr = '127.0.0.1'
    return addr
    