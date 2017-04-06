#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Read.py - creation of ReadProperty and ReadPropertyMultiple requests

    Used while defining an app:
    Example::

        class BasicScript(WhoisIAm, ReadProperty)

    Class::

        ReadProperty()
            def read()
            def readMultiple()

'''

#--- standard Python modules ---
from queue import Queue, Empty
import time

#--- 3rd party modules ---
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

#--- this application's modules ---
from .IOExceptions import SegmentationNotSupported, ReadPropertyException, ReadPropertyMultipleException, NoResponseFromController, ApplicationNotStarted
from ..functions.debug import log_debug, log_exception

#------------------------------------------------------------------------------

# some debugging
_DEBUG = 0


@bacpypes_debugging
class ReadProperty():
    """
    Defines BACnet Read functions: readProperty and readPropertyMultiple.
    Data exchange is made via a Queue object
    A timeout of 10 seconds allows detection of invalid device or communciation errors.
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
        """
        Build a ReadProperty request, wait for the answer and return the value

        :param args: String with <addr> <type> <inst> <prop> [ <indx> ]
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10'
            bacnet = BAC0.ReadWriteScript(localIPAddr = myIPAddr)
            bacnet.read('2:5 analogInput 1 presentValue')

        Requests the controller at (Network 2, address 5) for the presentValue of 
        its analog input 1 (AI:1).
        """
        if not self._started:
            raise ApplicationNotStarted('BACnet stack not running - use startApp()')
        #with self.this_application._lock:
            #time.sleep(0.5)
            #self.this_application._lock = True

        args = args.split()
        log_debug(ReadProperty, "do_read %r", args)

        try:
            iocb = IOCB(self.build_rp_request(args, arr_index))     # build ReadProperty request
            self.this_application.request_io(iocb)                  # pass to the BACnet stack
            log_debug(ReadProperty,"    - iocb: %r", iocb)

        except ReadPropertyException as error:
            log_exception("exception: %r", error)                   # construction error

        iocb.wait()             # Wait for BACnet response

        if iocb.ioResponse:     # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, ReadPropertyACK):               # expecting an ACK
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

        if iocb.ioError:        # unsuccessful: error/reject/abort
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
        """ Build a ReadPropertyMultiple request, wait for the answer and return the values

        :param args: String with <addr> ( <type> <inst> ( <prop> [ <indx> ] )... )...
        :returns: data read from device (str representing data like 10 or True)

        *Example*::

            import BAC0
            myIPAddr = '192.168.1.10'
            bacnet = BAC0.ReadWriteScript(localIPAddr = myIPAddr)
            bacnet.readMultiple('2:5 analogInput 1 presentValue units')

        Requests the controller at (Network 2, address 5) for the (presentValue and units) of 
        its analog input 1 (AI:1).
        """
        if not self._started:
            raise ApplicationNotStarted('BACnet stack not running - use startApp()')

        args = args.split()
        values = []
        log_debug(ReadProperty, "readMultiple %r", args)

        try:
            iocb = IOCB(self.build_rpm_request(args))               # build an ReadPropertyMultiple request
            self.this_application.request_io(iocb)                  # pass to the BACnet stack

        except ReadPropertyMultipleException as error:
            log_exception("exception: %r", error)                   # construction error


        iocb.wait()             # Wait for BACnet response

        if iocb.ioResponse:     # successful response
            apdu = iocb.ioResponse

            if not isinstance(apdu, ReadPropertyMultipleACK):       # expecting an ACK
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

                    readResult = element.readResult

                    if propertyArrayIndex is not None:
                        print("[" + str(propertyArrayIndex) + "]")

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
                    

        if iocb.ioError:        # unsuccessful: error/reject/abort
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
                prop_reference = PropertyReference(propertyIdentifier=prop_id)

                # check for an array index
                if (i < len(args)) and args[i].isdigit():
                    prop_reference.propertyArrayIndex = int(args[i])
                    i += 1

                prop_reference_list.append(prop_reference)

            if not prop_reference_list:
                raise ValueError("provide at least one property")

            # build a read access specification
            read_access_spec = ReadAccessSpecification(
                objectIdentifier=(obj_type, obj_inst),
                listOfPropertyReferences=prop_reference_list )

            read_access_spec_list.append(read_access_spec)

        if not read_access_spec_list:
            raise RuntimeError(
                "at least one read access specification required")

        # build the request
        request = ReadPropertyMultipleRequest(listOfReadAccessSpecs=read_access_spec_list )
        request.pduDestination = Address(addr)
        log_debug(ReadProperty, "    - request: %r", request)

        return request
