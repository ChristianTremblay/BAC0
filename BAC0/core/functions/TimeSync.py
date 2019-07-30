#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
TimeSync.py - creation of time synch requests

"""
from ...core.io.Read import find_reason
from ..io.IOExceptions import (
    SegmentationNotSupported,
    ReadPropertyException,
    ReadPropertyMultipleException,
    NoResponseFromController,
    ApplicationNotStarted,
)
from ...core.utils.notes import note_and_log

# --- standard Python modules ---

# --- 3rd party modules ---
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.primitivedata import Date, Time
from bacpypes.basetypes import DateTime
from bacpypes.apdu import TimeSynchronizationRequest
from bacpypes.iocb import IOCB


@note_and_log
class TimeSync:
    """
    Mixin to support Time Synchronisation from BAC0 to other devices
    """

    def time_sync(self, *args):
        """
        Take local time and send it to devices
        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        if args:
            args = args[0].split()
        msg = args if args else "everyone"

        self._log.debug("time sync {!r}".format(msg))

        # build a request
        request = TimeSynchronizationRequest(
            time=DateTime(date=Date().now().value, time=Time().now().value)
        )
        if len(args) == 1:
            request.pduDestination = Address(args[0])
            del args[0]
        else:
            request.pduDestination = GlobalBroadcast()

        self._log.debug("{:>12} {}".format("- request:", request))

        iocb = IOCB(request)  # make an IOCB

        # pass to the BACnet stack
        self.this_application.request_io(iocb)

        iocb.wait()  # Wait for BACnet response

        if iocb.ioResponse:  # successful response
            apdu = iocb.ioResponse

        if iocb.ioError:  # unsuccessful: error/reject/abort
            apdu = iocb.ioError
            reason = find_reason(apdu)
            self._log.error("An error occured : {}".format(reason))
