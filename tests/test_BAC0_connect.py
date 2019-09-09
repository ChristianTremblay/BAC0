#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test BAC0.connect
"""

import pytest
import time
import BAC0


def test_bac0_connect_ok():
    fake_bac0_obj = "my_test_bac0"
    fake_device_id = 666
    fake_firmware_revision = "0.1.0"
    fake_max_apdu_length = "2048"
    fake_max_segments = "2048"
    fake_bbmd_ttl = 10
    fake_model_name = "Raspberry Pi"
    fake_vendor_id = 999
    fake_vendor_name = "Innotrode"

    bacnet = BAC0.connect(
        ip="127.0.2.1",
        localObjName=fake_bac0_obj,
        deviceId=fake_device_id,
        firmwareRevision=fake_firmware_revision,
        maxAPDULengthAccepted=fake_max_apdu_length,
        maxSegmentsAccepted=fake_max_segments,
        bbmdTTL=fake_bbmd_ttl,
        modelName=fake_model_name,
        vendorId=fake_vendor_id,
        vendorName=fake_vendor_name,
    )

    assert bacnet.localObjName == fake_bac0_obj
    assert bacnet.Boid == fake_device_id
    assert bacnet.firmwareRevision == fake_firmware_revision
    assert bacnet.maxAPDULengthAccepted == fake_max_apdu_length
    assert bacnet.maxSegmentsAccepted == fake_max_segments
    assert bacnet.bbmdTTL == fake_bbmd_ttl
    assert bacnet.modelName == fake_model_name
    assert bacnet.vendorId == fake_vendor_id
    assert bacnet.vendorName == fake_vendor_name

    bacnet.disconnect()
    time.sleep(1)
