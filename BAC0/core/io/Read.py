#!/usr/bin/python

"""
Built around a simple BIPSimpleApplication this class allows to create read and write
requests and store read responses in a variables

For 'read' commands it will create ReadPropertyRequest PDUs, then lines up the
coorresponding ReadPropertyACK and return the value. 

For 'write' commands it will create WritePropertyRequst PDUs and prints out a simple acknowledgement.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference,ReadAccessSpecification,ReadPropertyRequest, ReadPropertyACK, ReadPropertyMultipleRequest, ReadPropertyMultipleACK
from bacpypes.basetypes import PropertyIdentifier

import time


from queue import Queue, Empty
from threading import Event

# some debugging
_debug = 0
_log = ModuleLogger(globals())



@bacpypes_debugging
class ReadProperty():
    def __init__(self):
        self.this_application = None
        self.this_application.ResponseQueue = Queue()
        
    def read(self, args):
        """
        Given arguments, will process a read request, wait for the answer and return the value
        Arguments are
        <addr> <type> <inst> <prop> [ <indx> ]
        ex. '2:5 analogInput 1 presentValue' will read controller with a MAC address of 5 in the network 2
        Will ask for the present Value of analog input 1 (AI:1)
        """
        if not self._started : raise Exception('App not running, use startApp() function')
        args = args.split()
        self.this_application.value == None
        if _debug: ReadProperty._debug("do_read %r", args)

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
            if _debug: ReadProperty._debug("    - request: %r", request)

            # give it to the application
            self.this_application.request(request)

        except Exception as e:
            ReadProperty._exception("exception: %r", e)

        """
        Wait for the answer and return the value
        A 5sec timeout will terminate the request 
        """        
        #timeout = time.time() + 5   # 5 secondes from now   
        ##val = None
        #while self.this_application.value == None:
        #    if self.this_application.value != None or time.time() > timeout or self.this_application.error != None:
        #        break
        #return self.this_application.value
        
        # Test with Queue
        data = None
        while True:
            try:
                data, evt = self.this_application.ResponseQueue.get(timeout=2)    
                evt.set()
                return data
            except Empty:
                print('No response from controller')
                return None
        
    def readMultiple(self, args):
        """read <addr> ( <type> <inst> ( <prop> [ <indx> ] )... )..."""
        args = args.split()
        if _debug: ReadProperty._debug("readMultiple %r", args)

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
                            raise ValueError("invalid property for object type")

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
                raise RuntimeError("at least one read access specification required")

            # build the request
            request = ReadPropertyMultipleRequest(
                listOfReadAccessSpecs=read_access_spec_list,
                )
            request.pduDestination = Address(addr)
            if _debug: ReadProperty._debug("    - request: %r", request)

            # give it to the application
            self.this_application.request(request)

        except Exception as e:
            ReadProperty._exception("exception: %r", e)
        """
        Wait for the answer and return the value
        A 5sec timeout will terminate the request 
        """        
        #timeout = time.time() + 5   # 5 secondes from now   
        ##val = None
        #while self.this_application.values == []:
        #    if self.this_application.values != [] or time.time() > timeout or self.this_application.error != None:
        #        break
        #return self.this_application.values
        data = None
        while True:
            try:
                data, evt = self.this_application.ResponseQueue.get(timeout=2)    
                evt.set()
                return data
            except Empty:
                print('No response from controller')
                return None
            