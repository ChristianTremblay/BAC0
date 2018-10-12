#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

from BAC0.core.functions.GetIPAddr import HostIP
import BAC0

def test_WithIPProvided():
    # Disconnect conftest ?
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split('/')
    bacnet_with_ip = BAC0.lite(ip=ip,port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()

def test_WithIPAndMask():
    # Disconnect conftest ?
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split('/')
    bacnet_with_ip = BAC0.lite(ip=ip, mask=subnet, port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()
    
def test_WithIPAndMaskAndPort():
    # Disconnect conftest ?
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split('/')
    bacnet_with_ip = BAC0.lite(ip=ip, mask=subnet, port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()
    
def test_WithIPAndMaskInString():
    # Disconnect conftest ?
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split('/')
    bacnet_with_ip = BAC0.lite(ip='{}/{}'.format(ip,subnet),port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()
    
def test_WithIPAndMaskAndPortInString():
    # Disconnect conftest ?
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split('/')
    bacnet_with_ip = BAC0.lite(ip='{}/{}:47812'.format(ip,subnet))
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect() 