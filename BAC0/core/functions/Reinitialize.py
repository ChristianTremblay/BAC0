#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Reinitialize.py - creation of ReinitializeDeviceRequest

"""
from bacpypes3.apdu import (
    ReinitializeDeviceRequest,
    ReinitializeDeviceRequestReinitializedStateOfDevice,
)


# --- 3rd party modules ---
from bacpypes3.pdu import Address
from bacpypes3.app import Application
from bacpypes3.primitivedata import CharacterString

from ..io.IOExceptions import ApplicationNotStarted
from ..utils.notes import note_and_log
from ...core.app.asyncApp import BAC0Application

# --- standard Python modules ---


@note_and_log
class Reinitialize:
    """
    Mixin to support Reinitialize from BAC0 to other devices
    """

    def reinitialize(self, address=None, password=None, state="coldstart"):
        """
        Will send reinitialize request
        """
        _this_application: BAC0Application = self.this_application
        _app: Application = _this_application.app
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        if not address:
            raise ValueError("Provide address for request")

        # build a request
        request = ReinitializeDeviceRequest()
        request.reinitializedStateOfDevice = getattr(
            ReinitializeDeviceRequestReinitializedStateOfDevice, state
        )
        request.pduDestination = Address(address)
        request.password = CharacterString(password)

        self.log(f"{'- request:':>12} {request}", level="debug")
        _app.request(request)

        self.log(f"Reinitialize request sent to device : {address}", level="info")
