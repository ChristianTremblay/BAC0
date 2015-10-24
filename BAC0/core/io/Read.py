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


    Functions::

        print_debug()

"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyRequest, ReadPropertyMultipleRequest
from bacpypes.basetypes import PropertyIdentifier

from queue import Queue, Empty

from .IOExceptions import ReadPropertyException, ReadPropertyMultipleException

# some debugging
_debug = 0
_LOG = ModuleLogger(globals())


@bacpypes_debugging
class ReadProperty():
    """
    This class defines functions to read bacnet messages.
    It handles readProperty, readPropertyMultiple
    Data exchange is made via a Queue object
    A timeout of 5 seconds allow detection of invalid device or communciation
    errors.
    """
    _TIMEOUT = 5

    def __init__(self):
        """ This function is a fake one so spyder can see local variables
        """
        self.this_application = None
        self.this_application.ResponseQueue = Queue()

    def read(self, args):
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
            raise Exception('App not running, use startApp() function')
        args = args.split()
        self.this_application.value is None
        print_debug("do_read %r", args)

        try:
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
            )
            request.pduDestination = Address(addr)

            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            print_debug("    - request: %r", request)

            # give it to the application
            self.this_application.request(request)

        except ReadPropertyException as error:
            ReadProperty._exception("exception: %r", error)

        # Share response with Queue
        data = None
        while True:
            try:
                data, evt = self.this_application.ResponseQueue.get(
                    timeout=self._TIMEOUT)
                evt.set()
                return data
            except Empty:
                print('No response from controller')
                return None

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
        args = args.split()
        print_debug("readMultiple %r", args)

        try:
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
            print_debug("    - request: %r", request)

            # give it to the application
            self.this_application.request(request)

        except ReadPropertyMultipleException as error:
            ReadProperty._exception("exception: %r", error)

        data = None
        while True:
            try:
                data, evt = self.this_application.ResponseQueue.get(
                    timeout=self._TIMEOUT)
                evt.set()
                return data
            except Empty:
                print('No response from controller')
                return None


def print_debug(msg, *args):
    """
    Used to print info to console when debug mode active
    """
    if _debug:
        ReadProperty._debug(msg, args)
