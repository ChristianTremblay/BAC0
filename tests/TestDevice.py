#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Device
-------------------------
"""

from BAC0.core.devices.Device import Device
from BAC0.core.app.ScriptApplication import ScriptApplication

from mock import Mock, patch, call
import unittest

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyMultipleRequest
from bacpypes.basetypes import PropertyIdentifier

from threading import Event
from queue import Empty


class TestDevice(ScriptApplication):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """
    def setUp(self):
        pass