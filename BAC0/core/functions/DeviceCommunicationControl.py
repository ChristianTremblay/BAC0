#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Reinitialize.py - creation of ReinitializeDeviceRequest

"""
# --- standard Python modules ---
import datetime as dt

# --- 3rd party modules ---
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.primitivedata import Date, Time, CharacterString, Unsigned16
from bacpypes.basetypes import DateTime
from bacpypes.apdu import (
    DeviceCommunicationControlRequest,
    DeviceCommunicationControlRequestEnableDisable,
    SimpleAckPDU,
)
from bacpypes.iocb import IOCB
from bacpypes.core import deferred

from ...core.io.Read import find_reason
from ..io.IOExceptions import (
    SegmentationNotSupported,
    ReadPropertyException,
    ReadPropertyMultipleException,
    NoResponseFromController,
    ApplicationNotStarted,
)

from ...core.utils.notes import note_and_log


@note_and_log
class DeviceCommunicationControl:
    """
    Mixin to support DeviceCommunicationControl from BAC0 to other devices
    """

    def dcc(self, address=None, duration=None, password=None, state=None):
        """
        Will send DeviceCommunicationControl request
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        if not address:
            raise ValueError("Provide address for request")

        if not state:
            raise ValueError("Provide state ('enable', 'disable', 'disableInitiation'")

        # build a request
        request = DeviceCommunicationControlRequest()
        request.enableDisable = DeviceCommunicationControlRequestEnableDisable.enumerations[
            state
        ]
        request.pduDestination = Address(address)
        if duration:
            request.duration = Unsigned16(duration)

        request.password = CharacterString(password)

        self._log.debug("{:>12} {}".format("- request:", request))

        iocb = IOCB(request)  # make an IOCB

        # pass to the BACnet stack
        deferred(self.this_application.request_io, iocb)

        # Unconfirmed request...so wait until complete
        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self._log.warning("Not an ack, see debug for more infos.")
                self._log.debug(
                    "Not an ack. | APDU : {} / {}".format((apdu, type(apdu)))
                )
                return

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController("APDU Abort Reason : {}".format(reason))

        self._log.info(
            "DeviceCommunicationControl request sent to device : {}".format(address)
        )
