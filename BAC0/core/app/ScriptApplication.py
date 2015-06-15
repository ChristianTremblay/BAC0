#!/usr/bin/python

"""
Built around a simple BIPSimpleApplication this class allows to create read and write
requests and store read responses in a variables

For 'read' commands it will create ReadPropertyRequest PDUs, then lines up the
coorresponding ReadPropertyACK and return the value. 

For 'write' commands it will create WritePropertyRequst PDUs and prints out a simple acknowledgement.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_datatype

from bacpypes.apdu import Error, AbortPDU, SimpleAckPDU,ReadPropertyRequest, ReadPropertyACK, ReadPropertyMultipleRequest, ReadPropertyMultipleACK, IAmRequest

from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array


from collections import defaultdict


# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class ScriptApplication(BIPSimpleApplication):
    """
    This class define the bacnet application that process requests
    """

    def __init__(self, *args):
        if _debug: ScriptApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None
        self.value = None
        self.error = None
        self.values = []
        self.i_am_counter = defaultdict(int)

    def request(self, apdu):
        """
        Initialize class variables to None for the present request
        Sends the apdu to the application request
        """
        if _debug: ScriptApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu
        self.value = None
        self.error = None
        self.values = []
        self.i_am_counter = defaultdict(int)

        # forward it along
        BIPSimpleApplication.request(self, apdu)
        
    def indication(self, apdu):
        """Given an I-Am request, cache it."""
        if _debug: ScriptApplication._debug("do_IAmRequest %r", apdu)
        if isinstance(apdu,IAmRequest):
            # build a key from the source, just use the instance number
            key = (str(apdu.pduSource),
                apdu.iAmDeviceIdentifier[1],
                )
    
            # count the times this has been received
            self.i_am_counter[key] += 1
        # pass back to the default implementation
        BIPSimpleApplication.indication(self, apdu)


    def confirmation(self, apdu):
        """
        This function process answers from the stack and look for a returned value or an error.
        """
        if _debug: ScriptApplication._debug("confirmation %r", apdu)
        if isinstance(apdu, Error):
            self.error = "%s" % (apdu.errorCode,)          
            #sys.stdout.write("error: %s\n" % (apdu.errorCode,))
            #sys.stdout.flush()

        elif isinstance(apdu, AbortPDU):
            self.error = apdu.debug_contents()
            

        if isinstance(apdu, SimpleAckPDU):
            self.value = apdu.debug_contents()           
            #sys.stdout.write("ack\n")
            #sys.stdout.flush() 

        elif (isinstance(self._request, ReadPropertyRequest)) and (isinstance(apdu, ReadPropertyACK)):
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

            if _debug: ScriptApplication._debug("    - value: %r", self.value)
            
        elif (isinstance(self._request, ReadPropertyMultipleRequest)) and (isinstance(apdu, ReadPropertyMultipleACK)):
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

                    #sys.stdout.write(propertyIdentifier)
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
                        #sys.stdout.write(" = " + str(value) + '\n')
                    #sys.stdout.flush()


            
                        #sys.stdout.write(" = " + str(value) + '\n')
                    #sys.stdout.flush()
            #sys.stdout.write(str(self.value) + '\n')
            #sys.stdout.flush()
            
