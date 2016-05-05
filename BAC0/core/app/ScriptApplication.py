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
from bacpypes.object import get_datatype
from bacpypes.apdu import Error, AbortPDU, SimpleAckPDU, ReadPropertyRequest, \
    ReadPropertyACK, ReadPropertyMultipleRequest, ReadPropertyMultipleACK, \
    IAmRequest, WhoIsRequest, AbortReason
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.pdu import Address
from bacpypes.object import PropertyError
from bacpypes.basetypes import ErrorCode

from collections import defaultdict
from threading import Event, Lock
from queue import Queue
import logging

from ..io.IOExceptions import WriteAccessDenied, NoResponseFromController, SegmentationNotSupported, APDUError

# some debugging
_DEBUG = 0


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
        log_debug("__init__ %r", args)
        self.localAddress = None

        BIPSimpleApplication.__init__(self, *args)
        
        # _lock will be used by read/write operation to wait for answer before 
        # making another request
        self._lock = Lock()
        
        self._request = None
        self.value = None
        self.error = None
        self.values = []
        self.i_am_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)
        self.ResponseQueue = Queue()

        if isinstance(self.localAddress, Address):
            self.local_unicast_tuple = self.localAddress.addrTuple
            self.local_broadcast_tuple = self.localAddress.addrBroadcastTuple
        else:
            self.local_unicast_tuple = ('', 47808)
            self.local_broadcast_tuple = ('255.255.255.255', 47808)

    def request(self, apdu):
        """
        Reset class variables to None for the present request
        Sends the apdu to the application request

        :param apdu: apdu
        """
        log_debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu
        self.value = None
        self.error = None
        self.values = []
        
        # Will store responses to IAm and Whois
        self.i_am_counter = defaultdict(int)
        self.who_is_counter = defaultdict(int)

        # forward it along
        BIPSimpleApplication.request(self, apdu)

    def indication(self, apdu):
        """
        Indication will treat unconfirmed messages on the stack

        :param apdu: apdu
        """
        log_debug("do_IAmRequest %r", apdu)

        if _DEBUG:
            if apdu.pduSource == self.local_unicast_tuple[0]:
                log_debug("indication:received broadcast from self\n")
            else:
                log_debug("indication:received broadcast from %s (local:%s|source:%s)\n" %
                          (apdu.pduSource, self.local_unicast_tuple, apdu.pduSource))
        else:
            log_debug("cannot test broadcast")

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
        log_debug("confirmation from %r", apdu.pduSource)

        if isinstance(apdu, Error):
            self.error = "%s" % (apdu.errorCode,)
            #print('Error : %s' % self.error)
            
            if self.error == "writeAccessDenied":
                print('%s : Try writing to relinquish default.' % self.error)
                evt = Event()
                self.ResponseQueue.put((None, evt))
                evt.wait()
                raise WriteAccessDenied('Cannot write to point')
            
            elif self.error == "unknownProperty":
                #print('%s : Unknow property.' % self.error)
                evt = Event()
                self.ResponseQueue.put(('', evt))
                evt.wait()
                #raise UnknownPropertyError('Cannot find property on point')
                

        elif isinstance(apdu, AbortPDU):
            
            self.abort_pdu_reason = apdu.apduAbortRejectReason
            #print('Abort PDU : %s' % self.abort_pdu_reason)  
            # UNCOMMENT STRING
            if self.abort_pdu_reason == AbortReason.segmentationNotSupported:
                #print('Segment Abort PDU : %s' % self.abort_pdu_reason)                
                evt = Event()
                self.ResponseQueue.put(('err_seg', evt))
                evt.wait()
                # probably because of thread... the raise do not seem
                # to be fired.... putting err_seg to raise from caller...
                #raise SegmentationNotSupported('Segmentation problem with device')
            
            else:
                #print('Abort PDU : %s' % self.abort_pdu_reason)                
                #evt = Event()
                self.ResponseQueue.put((None, evt))
                evt.wait()
                #raise NoResponseFromController('Abort PDU received')

        if isinstance(apdu, SimpleAckPDU):
            evt = Event()
            self.ResponseQueue.put((self.value, evt))
            evt.wait()

        elif (isinstance(self._request, ReadPropertyRequest)) \
                and (isinstance(apdu, ReadPropertyACK)):

            # find the datatype
            datatype = get_datatype(
                apdu.objectIdentifier[0],
                apdu.propertyIdentifier)
            log_debug("    - datatype: %r", datatype)

            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (
                    apdu.propertyArrayIndex is not None):
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

            log_debug("    - value: %r", self.value)

        elif (isinstance(self._request, ReadPropertyMultipleRequest)) \
                and (isinstance(apdu, ReadPropertyMultipleACK)):

            # loop through the results
            for result in apdu.listOfReadAccessResults:
                # here is the object identifier
                objectIdentifier = result.objectIdentifier
                log_debug("    - objectIdentifier: %r", objectIdentifier)

                # now come the property values per object
                for element in result.listOfResults:
                    # get the property and array index
                    propertyIdentifier = element.propertyIdentifier
                    log_debug(
                        "    - propertyIdentifier: %r",
                        propertyIdentifier)

                    propertyArrayIndex = element.propertyArrayIndex
                    log_debug(
                        "    - propertyArrayIndex: %r",
                        propertyArrayIndex)

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
                        datatype = get_datatype(
                            objectIdentifier[0], propertyIdentifier)
                        log_debug("    - datatype: %r", datatype)

                        if not datatype:
                            raise TypeError("unknown datatype")

                        # special case for array parts, others are managed by
                        # cast_out
                        if issubclass(datatype, Array) and (
                                propertyArrayIndex is not None):
                            if propertyArrayIndex == 0:
                                self.values.append(
                                    propertyValue.cast_out(Unsigned))
                            else:
                                self.values.append(
                                    propertyValue.cast_out(datatype.subtype))
                        else:
                            value = propertyValue.cast_out(datatype)
                        log_debug("    - value: %r", value)

                        self.values.append(value)
            # Use a queue to store the response, wait for it to be used then
            # resume
            evt = Event()
            self.ResponseQueue.put((self.values, evt))
            evt.wait()

def log_debug(txt, *args):
    """
    Helper function to log debug messages
    """
    if _DEBUG:
        if args:
            msg = txt % args
        else:
            msg = txt
        # pylint: disable=E1101,W0212
        ScriptApplication._debug(msg)
