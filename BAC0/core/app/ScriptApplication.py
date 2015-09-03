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

This module will also listen for responses to requests (indication or 
confirmation).

Response will be added to a Queue, we'll wait for the response to be processed
by the caller, then resume.

This object will be added to script objects and will be runned as thread

See BAC0.scripts for more details.

"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_datatype
from bacpypes.apdu import Error, AbortPDU, SimpleAckPDU, ReadPropertyRequest, \
    ReadPropertyACK, ReadPropertyMultipleRequest, ReadPropertyMultipleACK, \
    IAmRequest,WhoIsRequest
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array

from collections import defaultdict
from threading import Event
from queue import Queue

# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class ScriptApplication(BIPSimpleApplication):
    """
    This class defines the bacnet application that process requests
    """

    def __init__(self, *args):
        """Creation of the application. Adding properties to basic B/IP App.
        
        :param *args: local object device, local IP address
        
        See BAC0.scripts.BasicScript for more details.
        """
        if _debug: ScriptApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None
        self.value = None
        self.error = None
        self.values = []
        self.i_am_counter = defaultdict(int)
        self.ResponseQueue = Queue()

    def request(self, apdu):
        """
        Reset class variables to None for the present request
        Sends the apdu to the application request
        
        :param apdu: apdu
        """
        if _debug: ScriptApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu
        self.value = None
        self.error = None
        self.values = []
        self.i_am_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)
        #self.ResponseQueue = Queue()

        # forward it along
        BIPSimpleApplication.request(self, apdu)

    def indication(self, apdu):
        """Given an I-Am request, cache it.
        Indication will treat unconfirmed messages on the stack
        
        :param apdu: apdu
        """
        if _debug: ScriptApplication._debug("do_IAmRequest %r", apdu)
        if isinstance(apdu, IAmRequest):
            # build a key from the source, just use the instance number
            key = (str(apdu.pduSource),
                   apdu.iAmDeviceIdentifier[1],
            )
            # count the times this has been received
            self.i_am_counter[key] += 1
        
        if isinstance(apdu, WhoIsRequest):        
        # build a key from the source and parameters
            key = (str(apdu.pduSource),
                apdu.deviceInstanceRangeLowLimit,
                apdu.deviceInstanceRangeHighLimit,
                )

        # count the times this has been received
            self.who_is_counter[key] += 1
            BIPSimpleApplication.do_WhoIsRequest(self, apdu)
        # pass back to the default implementation
        BIPSimpleApplication.indication(self, apdu)


    def confirmation(self, apdu):
        """
        This function process confirmed answers from the stack and looks for a returned 
        value or an error.
        If a valid value is found, it's stored in the ResponseQueue. We'll wait for the
        response to be used by the caller then resume the function.
        
        How we deal with the Queue::
            
            # Creation of an event
            evt = Event()
            # Store the value and the event in the Queue
            self.ResponseQueue.put((self.value, evt))
            # Wait until the event is set by the caller (read function for example)
            evt.wait()
            
        :param apdu: apdu
        """
        if _debug: ScriptApplication._debug("confirmation %r", apdu)
        if isinstance(apdu, Error):
            self.error = "%s" % (apdu.errorCode,)   

        elif isinstance(apdu, AbortPDU):
            pass

        if isinstance(apdu, SimpleAckPDU):
            evt = Event()
            self.ResponseQueue.put((self.value, evt))
            evt.wait()

        elif (isinstance(self._request, ReadPropertyRequest)) \
            and (isinstance(apdu, ReadPropertyACK)):

            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug: ScriptApplication._debug("    - datatype: %r", datatype)
            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    self.value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    self.value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                self.value = apdu.propertyValue.cast_out(datatype)

            # Share data with script
            evt = Event()
            self.ResponseQueue.put((self.value, evt))
            evt.wait()

            if _debug: ScriptApplication._debug("    - value: %r", self.value)

        elif (isinstance(self._request, ReadPropertyMultipleRequest)) \
            and (isinstance(apdu, ReadPropertyMultipleACK)):

            # loop through the results
            for result in apdu.listOfReadAccessResults:
                # here is the object identifier
                objectIdentifier = result.objectIdentifier
                if _debug: ScriptApplication._debug("    - objectIdentifier: %r", objectIdentifier)

                # now come the property values per object
                for element in result.listOfResults:
                    # get the property and array index
                    propertyIdentifier = element.propertyIdentifier
                    if _debug: ScriptApplication._debug("    - propertyIdentifier: %r", propertyIdentifier)
                    propertyArrayIndex = element.propertyArrayIndex
                    if _debug: ScriptApplication._debug("    - propertyArrayIndex: %r", propertyArrayIndex)

                    # here is the read result
                    readResult = element.readResult

                    if propertyArrayIndex is not None:
                        #sys.stdout.write("[" + str(propertyArrayIndex) + "]")
                        pass

                    # check for an error
                    if readResult.propertyAccessError is not None:
                        #sys.stdout.write(" ! " + str(readResult.propertyAccessError) + '\n')
                        pass

                    else:
                        # here is the value
                        propertyValue = readResult.propertyValue

                        # find the datatype
                        datatype = get_datatype(objectIdentifier[0], propertyIdentifier)
                        if _debug: ScriptApplication._debug("    - datatype: %r", datatype)
                        if not datatype:
                            raise TypeError("unknown datatype")

                        # special case for array parts, others are managed by cast_out
                        if issubclass(datatype, Array) and (propertyArrayIndex is not None):
                            if propertyArrayIndex == 0:
                                self.values.append(propertyValue.cast_out(Unsigned))
                            else:
                                self.values.append(propertyValue.cast_out(datatype.subtype))
                        else:
                            value = propertyValue.cast_out(datatype)
                        if _debug: ScriptApplication._debug("    - value: %r", value)
                        self.values.append(value)
            # Use a queue to store the response, wait for it to be used then resume
            evt = Event()
            self.ResponseQueue.put((self.values, evt))
            evt.wait()
