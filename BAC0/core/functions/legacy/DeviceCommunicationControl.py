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

from bacpypes.apdu import (
    DeviceCommunicationControlRequest,
    DeviceCommunicationControlRequestEnableDisable,
    SimpleAckPDU,
)
from bacpypes.core import deferred
from bacpypes.iocb import IOCB

# --- 3rd party modules ---
from bacpypes.pdu import Address
from bacpypes.primitivedata import CharacterString, Unsigned16

from ...io.IOExceptions import ApplicationNotStarted, NoResponseFromController
from ...io.legacy.Read import find_reason
from ...utils.notes import note_and_log


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
        request.enableDisable = (
            DeviceCommunicationControlRequestEnableDisable.enumerations[state]
        )
        request.pduDestination = Address(address)
        if duration:
            request.duration = Unsigned16(duration)

        request.password = CharacterString(password)

        self.log(f"{'- request:':>12} {request}", level="debug")

        iocb = IOCB(request)  # make an IOCB

        # pass to the BACnet stack
        deferred(self.this_application.request_io, iocb)

        # Unconfirmed request...so wait until complete
        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, SimpleAckPDU):  # expect an ACK
                self.log("Not an ack, see debug for more infos.", level="warning")
                self.log(f"Not an ack. | APDU : {apdu} / {type(apdu)}", level="debug")
                return

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            raise NoResponseFromController(f"APDU Abort Reason : {reason}")

        self.log(
            f"DeviceCommunicationControl request sent to device : {address}",
            level="info",
        )
