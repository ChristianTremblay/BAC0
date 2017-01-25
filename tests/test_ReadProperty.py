#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Read Property
-------------------------
"""

from BAC0.core.io.Read import ReadProperty
from BAC0.core.app.ScriptApplication import ScriptApplication
from BAC0.core.io.IOExceptions import ReadPropertyException, ReadPropertyMultipleException, ApplicationNotStarted


from mock import Mock, patch, call
import unittest

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    ReadPropertyRequest, ReadPropertyMultipleRequest, ReadPropertyACK
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.iocb import IOCB
from bacpypes.constructeddata import Any
from bacpypes.primitivedata import Real


class TestScriptApplication(ScriptApplication):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """
    @patch('bacpypes.app.BIPSimpleApplication.__init__')
    def __init__(self, *args):
        BIPSimpleApplication.__init__(Mock())
        self.elementService = Mock()
        #self.value = None
        iocb = IOCB()
        
        # Forging apdu response        
        fake_apdu = ReadPropertyACK( 
            objectIdentifier=('analogInput', 0), 
            propertyIdentifier='presentValue', 
            propertyValue=Any(Real(32)), )
        iocb.complete(fake_apdu)
        self.request = Mock()
        self.request.return_value = iocb


class TestReadPropertyClass(ReadProperty):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """

    def __init__(self):
        self.this_application = TestScriptApplication()


class TestReadProperty(unittest.TestCase):
    """
    Test with mock
    """
    # def setUp(self):

    @patch('BAC0.core.io.Read.ReadProperty.this_application.request')
    @patch('BAC0.core.app.ScriptApplication.ScriptApplication.__init__')
    @patch('bacpypes.app.BIPSimpleApplication.__init__')
    @patch('bacpypes.service.device.LocalDeviceObject')
    @patch('BAC0.core.io.Read.ReadProperty')
    def setUp(self, mock_rp, mock_localDevice,
              mock_BIPSimpleApplication, mock_ScriptApplication, mock_request):
        self.req = '2:5 analogValue 1 presentValue'
        mock_ScriptApplication.return_value = TestScriptApplication()
        mock_BIPSimpleApplication.return_value = None
        
        self.read_property = TestReadPropertyClass()
        self.read_property._started = True

#    def test_verify_return_value(self):
#        """
#        TestReadProperty / Result should read 32 from fake value provided
#        """
#        self.assertEqual(self.read_property.read(self.req), 32)

#    def test_request_is_correct(self):
#        """
#        TestReadProperty / Request used for method call should be equivalent to base request
#        """
#        self.read_property.read(self.req)
#        assert self.read_property.this_application.request.called
#        self.arg_used_in_call = (
#            self.read_property.this_application.request.call_args)[0][0]
#        self.base_request = call(create_ReadPropertyRequest(self.req))[1][0]
#
#        self.assertEqual(
#            self.arg_used_in_call.debug_contents(),
#            self.base_request.debug_contents())

    def test_wrong_datatype(self):
        """
        TestReadProperty / Wrong type or property should raise ValueError exception
        """
        self.req = '2:5 analogVal 1 presentValue'
        with self.assertRaises(ValueError):
            self.read_property.read(self.req)
        self.req = '2:5 analogValue 1 presValue units'
        with self.assertRaises(ValueError):
            self.read_property.read(self.req)

    def test_no_prop(self):
        """
        TestReadProperty / No object type should raise ValueError exception
        """
        #self.read_property.this_application._lock = False
        self.req = '2:5 1 presentValue units'
        with self.assertRaises(ValueError):
            self.read_property.read(self.req)

#    def test_no_response_from_controller(self):
#        self.req = '2:5 analogValue 1 presentValue'
#        self.read_property.this_application.ResponseQueue.get.side_effect = Empty
#        self.assertEqual(self.read_property.read(self.req),None)

    def test_not_started(self):
        """
        TestReadProperty / When not started, application should raise ApplicationNotStarted exception
        """
        #self.read_property.this_application._lock = False
        self.req = '2:5 1 presentValue units'
        self.read_property._started = False
        with self.assertRaises(ApplicationNotStarted):
            self.read_property.read(self.req)


def create_ReadPropertyRequest(args):
    """
    Create a ReadPropertyRequest from a string
    """
    args = args.split()
    addr, obj_type, obj_inst, prop_id = args[:4]
    print(addr)

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

    return request


def create_ReadPropertyMultipleRequest(args):
    args = args.split()

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
    return request
