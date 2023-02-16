#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest

import BAC0
from BAC0.core.functions.GetIPAddr import HostIP

VENDOR_ID = 842


@pytest.fixture(scope="session")
def host_ip():
    hip = HostIP()
    ip, subnet = hip.ip_address_subnet.split("/")
    if subnet == "32":
        # invalid mask given by Travis
        subnet = "24"
    return (ip, subnet)


@pytest.mark.skip("Works locally but not in Travis")
def test_WithIPProvided(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip=ip, port=47812)
    assert bacnet_with_ip.vendorId == VENDOR_ID
    bacnet_with_ip.disconnect()


@pytest.mark.skip("Works locally but nt in Travis")
def test_WithIPAndMask(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip=ip, mask=subnet, port=47812)
    assert bacnet_with_ip.vendorId == VENDOR_ID
    bacnet_with_ip.disconnect()


@pytest.mark.skip("Works locally but not in Travis")
def test_WithIPAndMaskAndPort(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip=ip, mask=subnet, port=47812)
    assert bacnet_with_ip.vendorId == VENDOR_ID
    bacnet_with_ip.disconnect()


@pytest.mark.skip("Works locally but not in Travis")
def test_WithIPAndMaskInString(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip="{}/{}".format(ip, subnet), port=47812)
    assert bacnet_with_ip.vendorId == VENDOR_ID
    bacnet_with_ip.disconnect()


@pytest.mark.skip("Works locally but not in Travis")
def test_WithIPAndMaskAndPortInString(host_ip):
    ip, subnet = host_ip
    bacnet_with_ip = BAC0.lite(ip="{}/{}:47812".format(ip, subnet))
    assert bacnet_with_ip.vendorId == VENDOR_ID
    bacnet_with_ip.disconnect()
