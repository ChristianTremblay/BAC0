#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
ScriptApplication 
=================

A basic BACnet application (bacpypes BIPSimpleApplication) for interacting with 
the bacpypes BACnet stack.  It enables the base-level BACnet functionality 
(a.k.a. device discovery) - meaning it can send & receive WhoIs & IAm messages.

Additional functionality is enabled by inheriting this application, and then 
extending it with more functions. [See BAC0.scripts for more examples of this.]

'''
#--- standard Python modules ---
from collections import defaultdict
import logging

#--- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address

#--- this application's modules ---
from ..functions.debug import log_debug
from ..utils.notes import note_and_log

#------------------------------------------------------------------------------

@note_and_log
class ScriptApplication(BIPSimpleApplication):
    """
    Defines a basic BACnet/IP application to process BACnet requests.

    :param *args: local object device, local IP address
        See BAC0.scripts.BasicScript for more details.
        
    """
    def __init__(self, *args):        
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

    
    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        self.log(("do_WhoIsRequest %r", apdu))

        # build a key from the source and parameters
        key = (str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit )

        # count the times this has been received
        self.who_is_counter[key] += 1

        # continue with the default implementation
        BIPSimpleApplication.do_WhoIsRequest(self, apdu)


    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        self.log(("do_IAmRequest %r", apdu))

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource), apdu.iAmDeviceIdentifier[1] )
        self.i_am_counter[key] += 1

        # continue with the default implementation
        BIPSimpleApplication.do_IAmRequest(self, apdu)


