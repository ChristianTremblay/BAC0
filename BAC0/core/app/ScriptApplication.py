#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
ScriptApplication
=================
Built around a simple BIPSimpleApplication this module deals with requests
created by a child app. It will prepare the requests and give them back to the
stack.

This module will also listen for responses to requests (indication or confirmation).

Response will be added to a Queue, we'll wait for the response to be processed
by the caller, then resume.

This object will be added to script objects and will be runned as thread

See BAC0.scripts for more details.

"""

from bacpypes.debugging import bacpypes_debugging

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address

from collections import defaultdict
import logging

from ..functions.debug import log_debug

@bacpypes_debugging
class ScriptApplication(BIPSimpleApplication):
    """
    This class defines the bacnet application that process requests
    """

    def __init__(self, *args):
        """
        Creation of the application. Adding properties to basic B/IP App.

        :param *args: local object device, local IP address
        See BAC0.scripts.BasicScript for more details.
        """
        logging.getLogger("comtypes").setLevel(logging.INFO)
        
        self.localAddress = None

        super().__init__(*args)
        
        self._request = None

        self.i_am_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)

        if isinstance(self.localAddress, Address):
            self.local_unicast_tuple = self.localAddress.addrTuple
            self.local_broadcast_tuple = self.localAddress.addrBroadcastTuple
        else:
            self.local_unicast_tuple = ('', 47808)
            self.local_broadcast_tuple = ('255.255.255.255', 47808)
            
        #log_debug(ScriptApplication, "__init__ %r" % args)

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        if self._debug: ScriptApplication._debug("do_WhoIsRequest %r", apdu)

        # build a key from the source and parameters
        key = (str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
            )

        # count the times this has been received
        self.who_is_counter[key] += 1

        # continue with the default implementation
        BIPSimpleApplication.do_WhoIsRequest(self, apdu)

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        if self._debug: ScriptApplication._debug("do_IAmRequest %r", apdu)

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource),
            apdu.iAmDeviceIdentifier[1],
            )

        # count the times this has been received
        self.i_am_counter[key] += 1

        # continue with the default implementation
        BIPSimpleApplication.do_IAmRequest(self, apdu)

