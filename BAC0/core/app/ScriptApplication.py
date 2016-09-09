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
from bacpypes.apdu import IAmRequest, WhoIsRequest
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

    def request(self, apdu):
        """
        Reset class variables to None for the present request
        Sends the apdu to the application request

        :param apdu: apdu
        """
        log_debug(ScriptApplication, "request %r", apdu)

        # save a copy of the request
        self._request = apdu
#        self.value = None
#        self.error = None
#        self.values = []
#        
        # Will store responses to IAm and Whois
        self.i_am_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)

        # forward it along
        return BIPSimpleApplication.request(self, apdu)

    def indication(self, apdu):
        """
        Indication will treat unconfirmed messages on the stack

        :param apdu: apdu
        """
        log_debug(ScriptApplication, "do_IAmRequest %r" % apdu)

#        if _DEBUG:
#            if apdu.pduSource == self.local_unicast_tuple[0]:
#                log_debug("indication:received broadcast from self\n")
#            else:
#                log_debug("indication:received broadcast from %s (local:%s|source:%s)\n" %
#                          (apdu.pduSource, self.local_unicast_tuple, apdu.pduSource))
#        else:
#            log_debug("cannot test broadcast")

        # Given an I-Am request, cache it.
        if isinstance(apdu, IAmRequest):
            # build a key from the source, just use the instance number
            key = (str(apdu.pduSource),
                   apdu.iAmDeviceIdentifier[1],)
            # count the times this has been received
            self.i_am_counter[key] += 1

        # Given an Who Is request, cache it.
        if isinstance(apdu, WhoIsRequest):
            # build a key from the source and parameters
            key = (str(apdu.pduSource),
                   apdu.deviceInstanceRangeLowLimit,
                   apdu.deviceInstanceRangeHighLimit,
                   )

            # count the times this has been received
            self.who_is_counter[key] += 1
            
        # pass back to the default implementation
        return BIPSimpleApplication.indication(self, apdu)

