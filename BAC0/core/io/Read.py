#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module allows the creation of ReadProperty and ReadPropertyMultiple
requests by and app

    Must be used while defining an app
    Example::

        class BasicScript(WhoisIAm, ReadProperty)

    Class::

        ReadProperty()
            def read()
            def readMultiple()
"""

from bacpypes.debugging import bacpypes_debugging

from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyRequest, ReadPropertyMultipleRequest
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.apdu import ReadPropertyMultipleACK, ReadPropertyACK
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.iocb import IOCB

from queue import Queue, Empty
import time

from .IOExceptions import SegmentationNotSupported, ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController, ApplicationNotStarted
from ..functions.debug import log_debug, log_exception

# some debugging
_DEBUG = 0


@bacpypes_debugging
class ReadProperty():
    """
    This class defines functions to read bacnet messages.
    It handles readProperty, readPropertyMultiple
    Data exchange is made via a Queue object
    A timeout of 5 seconds allow detection of invalid device or communciation
    errors.
    """
    _TIMEOUT = 10

#    def __init__(self, *args):
#        """ This function is a fake one so spyder can see local variables
#        """
#        #self.this_application = None
#        #self.this_application.ResponseQueue = Queue()
#        #self.this_application._lock = False
#        self._started = False

    def read(self, args, arr_index = None):
        """ This function build a read request wait for the answer and
        return the value

        :param args: String with <addr> <type> <inst> <prop> [ <indx> ]
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10'
            bacnet = BAC0.ReadWriteScript(localIPAddr = myIPAddr)
            bacnet.read('2:5 analogInput 1 presentValue')

        will read controller with a MAC address of 5 in the network 2
        Will ask for the present Value of analog input 1 (AI:1)
        """
        if not self._started:
            raise ApplicationNotStarted('App not running, use startApp() function')
        #with self.this_application._lock:
            #time.sleep(0.5)
            #self.this_application._lock = True
        args = args.split()
        #self.this_application.value is None
        log_debug(ReadProperty, "do_read %r", args)

        try:
            iocb = IOCB(self.build_rp_request(args, arr_index))
            # give it to the application
            self.this_application.request_io(iocb)
            #print('iocb : ', iocb)
            log_debug(ReadProperty,"    - iocb: %r", iocb)
            

        except ReadPropertyException as error:
            # error in the creation of the request
            log_exception("exception: %r", error)
            
        # Wait for the response
        iocb.wait()
        
        # do something for success
        if iocb.ioResponse:
            apdu = iocb.ioResponse

            # should be an ack
            if not isinstance(apdu, ReadPropertyACK):
                log_debug(ReadProperty,"    - not an ack")
                return

            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            log_debug(ReadProperty,"    - datatype: %r", datatype)
            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
            log_debug(ReadProperty,"    - value: %r", value)


            return value

        # do something for error/reject/abort
        if iocb.ioError:
            raise NoResponseFromController()
    
            # Share response with Queue
#            data = None
#            while True:
#                try:
#                    data, evt = self.this_application.ResponseQueue.get(
#                        timeout=self._TIMEOUT)
#                    evt.set()             
#                    if data == 'err_seg':
#                        raise SegmentationNotSupported
#                    #self.this_application._lock = False
#                    return data
#                except SegmentationNotSupported:
#                    raise
#                except Empty as error:
#                    #log_exception(ReadProperty, 'No response from controller')
#                    #self.this_application._lock = False
#                    raise NoResponseFromController()

    def readMultiple(self, args):
        """ This function build a readMultiple request wait for the answer and
        return the value

        :param args: String with <addr> ( <type> <inst> ( <prop> [ <indx> ] )... )...
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10'
            bacnet = BAC0.ReadWriteScript(localIPAddr = myIPAddr)
            bacnet.readMultiple('2:5 analogInput 1 presentValue units')

        will read controller with a MAC address of 5 in the network 2
        Will ask for the present Value and the units of analog input 1 (AI:1)
        """
        if not self._started:
            raise ApplicationNotStarted('App not running, use startApp() function')

        args = args.split()
        values = []
        log_debug(ReadProperty, "readMultiple %r", args)

        try:
            iocb = IOCB(self.build_rpm_request(args))
            # give it to the application
            self.this_application.request_io(iocb)

        except ReadPropertyMultipleException as error:
            log_exception(ReadProperty, "exception: %r", error)

        iocb.wait()

        # do something for success
        if iocb.ioResponse:
            apdu = iocb.ioResponse

            # should be an ack
            if not isinstance(apdu, ReadPropertyMultipleACK):
                log_debug(ReadProperty,"    - not an ack")
                return

            # loop through the results
            for result in apdu.listOfReadAccessResults:
                # here is the object identifier
                objectIdentifier = result.objectIdentifier
                log_debug(ReadProperty,"    - objectIdentifier: %r", objectIdentifier)

                # now come the property values per object
                for element in result.listOfResults:
                    # get the property and array index
                    propertyIdentifier = element.propertyIdentifier
                    log_debug(ReadProperty,"    - propertyIdentifier: %r", propertyIdentifier)
                    propertyArrayIndex = element.propertyArrayIndex
                    log_debug(ReadProperty,"    - propertyArrayIndex: %r", propertyArrayIndex)

                    # here is the read result
                    readResult = element.readResult

                    if propertyArrayIndex is not None:
                        print("[" + str(propertyArrayIndex) + "]")

                    # check for an error
                    if readResult.propertyAccessError is not None:
                        print(" ! " + str(readResult.propertyAccessError))

                    else:
                        # here is the value
                        propertyValue = readResult.propertyValue

                        # find the datatype
                        datatype = get_datatype(objectIdentifier[0], propertyIdentifier)
                        log_debug(ReadProperty,"    - datatype: %r", datatype)
                        if not datatype:
                            raise TypeError("unknown datatype")

                        # special case for array parts, others are managed by cast_out
                        if issubclass(datatype, Array) and (propertyArrayIndex is not None):
                            if propertyArrayIndex == 0:
                                value = propertyValue.cast_out(Unsigned)
                            else:
                                value = propertyValue.cast_out(datatype.subtype)
                        else:
                            value = propertyValue.cast_out(datatype)
                        log_debug(ReadProperty,"    - value: %r", value)

                        values.append(value)
            return values
                    

        # do something for error/reject/abort
        if iocb.ioError:
            raise NoResponseFromController()
    
#            data = None
#            while True:
#                try:
#                    data, evt = self.this_application.ResponseQueue.get(
#                        timeout=self._TIMEOUT)
#                    evt.set()
#                    #self.this_application._lock = False
#                    return data
#                except SegmentationNotSupported:
#                    raise
#                except Empty:
#                    print('No response from controller')
#                    #self.this_application._lock = False
#                    raise NoResponseFromController
#                    #return None
                
    def build_rp_request(self, args, arr_index = None):
        addr, obj_type, obj_inst, prop_id = args[:4]

        if obj_type.isdigit():
            obj_type = int(obj_type)
        elif not get_object_class(obj_type):
            raise ValueError("unknown object type")

        obj_inst = int(obj_inst)

        datatype = get_datatype(obj_type, prop_id)
        if not datatype:
            raise ValueError("invalid property for object type")

        # build a request
        request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id,
            propertyArrayIndex=arr_index,
        )
        request.pduDestination = Address(addr)

        if len(args) == 5:
            request.propertyArrayIndex = int(args[4])
        log_debug(ReadProperty, "    - request: %r", request)

        return request              
                
    def build_rpm_request(self, args):
        """
        Build request from args
        """
        i = 0
        addr = args[i]
        i += 1

        read_access_spec_list = []
        while i < len(args):
            obj_type = args[i]
            i += 1

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif not get_object_class(obj_type):
                raise ValueError("unknown object type")

            obj_inst = int(args[i])
            i += 1

            prop_reference_list = []
            while i < len(args):
                prop_id = args[i]
                if prop_id not in PropertyIdentifier.enumerations:
                    break

                i += 1
                if prop_id in ('all', 'required', 'optional'):
                    pass
                else:
                    datatype = get_datatype(obj_type, prop_id)
                    if not datatype:
                        raise ValueError(
                            "invalid property for object type : %s | %s" %
                            (obj_type, prop_id))

                # build a property reference
                prop_reference = PropertyReference(
                    propertyIdentifier=prop_id,
                )

                # check for an array index
                if (i < len(args)) and args[i].isdigit():
                    prop_reference.propertyArrayIndex = int(args[i])
                    i += 1

                # add it to the list
                prop_reference_list.append(prop_reference)

            # check for at least one property
            if not prop_reference_list:
                raise ValueError("provide at least one property")

            # build a read access specification
            read_access_spec = ReadAccessSpecification(
                objectIdentifier=(obj_type, obj_inst),
                listOfPropertyReferences=prop_reference_list,
            )

            # add it to the list
            read_access_spec_list.append(read_access_spec)

        # check for at least one
        if not read_access_spec_list:
            raise RuntimeError(
                "at least one read access specification required")

        # build the request
        request = ReadPropertyMultipleRequest(
            listOfReadAccessSpecs=read_access_spec_list,
        )
        request.pduDestination = Address(addr)
        log_debug(ReadProperty, "    - request: %r", request)
            
        return request
