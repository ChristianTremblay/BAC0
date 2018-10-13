#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

from BAC0.core.functions.GetIPAddr import HostIP
import BAC0
import pytest

@pytest.fixture(scope='module')
def host_ip():
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split('/')
    if subnet == '32':
        # invalid mask given by Travis
        subnet = '24'
    return (ip,subnet)


def test_WithIPProvided(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip=ip,port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()

def test_WithIPAndMask(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip=ip, mask=subnet, port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()
    
def test_WithIPAndMaskAndPort(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip=ip, mask=subnet, port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()
    
def test_WithIPAndMaskInString(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip='{}/{}'.format(ip,subnet),port=47812)
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect()
    
def test_WithIPAndMaskAndPortInString(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip='{}/{}:47812'.format(ip,subnet))
    assert bacnet_with_ip.vendorId == 842
    bacnet_with_ip.disconnect() 
