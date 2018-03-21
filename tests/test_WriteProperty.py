#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Read Property
-------------------------
"""

from BAC0.core.io.Write import WriteProperty
from BAC0.core.app.ScriptApplication import SimpleApplication
from BAC0.core.io.IOExceptions import WritePropertyException, WritePropertyCastError, NoResponseFromController, ApplicationNotStarted

from mock import Mock, patch, call
import unittest

from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from bacpypes.object import get_object_class, get_datatype
from bacpypes.apdu import PropertyReference, ReadAccessSpecification, \
    WritePropertyRequest
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real
from bacpypes.constructeddata import Array, Any

from threading import Event, Lock
from queue import Queue, Empty


class TestSimpleApplication(SimpleApplication):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """
    @patch('bacpypes.app.BIPSimpleApplication.__init__')
    def __init__(self, *args):
        BIPSimpleApplication.__init__(Mock())
        self.elementService = Mock()
        self.ResponseQueue = Mock()
        self.ResponseQueue.get.return_value = (None, Event())
        self.request = Mock()
        self.value = None


class TestWritePropertyClass(WriteProperty):
    """
    This class replaces the __init__ method for testing purposes.
    This way, we can mock the behaviour.
    """

    def __init__(self):
        self.this_application = TestSimpleApplication()
        self.this_application._lock = Lock()


class TestWriteProperty(unittest.TestCase):
    """
    Test with mock
    """
    # def setUp(self):

    @patch('BAC0.core.io.Read.ReadProperty.this_application.ResponseQueue.get')
    @patch('BAC0.core.app.ScriptApplication.SimpleApplication.__init__')
    @patch('bacpypes.app.BIPSimpleApplication.__init__')
    @patch('bacpypes.service.device.LocalDeviceObject')
    @patch('BAC0.core.io.Read.ReadProperty')
    def setUp(self, mock_rp, mock_localDevice,
              mock_BIPSimpleApplication, mock_SimpleApplication, mock_ResponseQueueGet):
        self.req = '2:5 analogValue 1 presentValue 100 - 8'
        mock_SimpleApplication.return_value = TestSimpleApplication()
        mock_BIPSimpleApplication.return_value = None
        self.write_property = TestWritePropertyClass()
        self.write_property._started = True

#    def test_verify_return_value(self):
#        """
#        TestWriteProperty / Write 100@8 Value returned must be None
#        """
#        #self.write_property.this_application._lock = False
#        self.assertEqual(self.write_property.write(self.req), None)

#    def test_write_null(self):
#        """
#        TestWriteProperty / Write Null Value returned must be None
#        """
#        #self.write_property.this_application._lock = False
#        self.req = '2:5 analogValue 1 presentValue null'
#        self.assertEqual(self.write_property.write(self.req), None)

#    def test_request_is_correct(self):
#        """
#        TestWriteProperty / Request used for method call should be equivalent to base_request
#        """
#        #self.write_property.this_application._lock = False
#        self.write_property.write(self.req)
#        assert self.write_property.this_application.request.called
#        self.arg_used_in_call = (
#            self.write_property.this_application.request.call_args)[0][0]
#        self.base_request = call(create_WritePropertyRequest(self.req))[1][0]
#
#        self.assertEqual(
#            self.arg_used_in_call.debug_contents(),
#            self.base_request.debug_contents())

    def test_wrong_datatype(self):
        """
        TestWriteProperty / Wrong type or property should raise TypeError exception
        """
        #self.write_property.this_application._lock = False
        self.req = '2:5 analValue 1 presentValue 100'
        with self.assertRaises(TypeError):
            self.write_property.write(self.req)
        #self.write_property.this_application._lock = False
        self.req = '2:5 analValue 1 presValue 100'
        with self.assertRaises(TypeError):
            self.write_property.write(self.req)

#    def test_ReadPropertyException(self):
#        self.req = 'a very bad request'
#        with self.assertRaises(ReadPropertyException):
#            self.write_property.write(self.req)

    def test_no_prop(self):
        """
        TestWriteProperty / No type or property should raise ValueError exception
        """
        #self.write_property.this_application._lock = False
        self.req = '2:5 1 presentValue 100'
        with self.assertRaises(ValueError):
            self.write_property.write(self.req)
        self.req = '2:5 1 analogValue 100'
        with self.assertRaises(ValueError):
            self.write_property.write(self.req)

#    def test_no_response_from_controller(self):
#        self.req = '2:5 analogValue 1 presentValue'
#        self.write_property.this_application.ResponseQueue.get.side_effect = Empty
#        self.assertEqual(self.write_property.write(self.req),None)

    def test_not_started(self):
        """
        TestWriteProperty / If application not started, should raise ApplicationNotStarted exception
        """
        #self.write_property.this_application._lock = False
        self.req = '2:5 analValue 1 presentValue 100'
        self.write_property._started = False
        with self.assertRaises(ApplicationNotStarted):
            self.write_property.write(self.req)


def create_WritePropertyRequest(args):
    """
    Create a WritePropertyRequest from a string
    """
    args = args.split()

    addr, obj_type, obj_inst, prop_id = args[:4]
    if obj_type.isdigit():
        obj_type = int(obj_type)
    obj_inst = int(obj_inst)
    value = args[4]

    indx = None
    if len(args) >= 6:
        if args[5] != "-":
            indx = int(args[5])

    priority = None
    if len(args) >= 7:
        priority = int(args[6])

    # get the datatype
    datatype = get_datatype(obj_type, prop_id)

    # change atomic values into something encodeable, null is a special
    # case
    if value == 'null':
        value = Null()
    elif issubclass(datatype, Atomic):
        if datatype is Integer:
            value = int(value)
        elif datatype is Real:
            value = float(value)
        elif datatype is Unsigned:
            value = int(value)
        value = datatype(value)
    elif issubclass(datatype, Array) and (indx is not None):
        if indx == 0:
            value = Integer(value)
        elif issubclass(datatype.subtype, Atomic):
            value = datatype.subtype(value)
        elif not isinstance(value, datatype.subtype):
            raise TypeError(
                "invalid result datatype, expecting %s" %
                (datatype.subtype.__name__,))
    elif not isinstance(value, datatype):
        raise TypeError(
            "invalid result datatype, expecting %s" %
            (datatype.__name__,))

    # build a request
    request = WritePropertyRequest(
        objectIdentifier=(obj_type, obj_inst),
        propertyIdentifier=prop_id
    )
    request.pduDestination = Address(addr)

    # save the value
    request.propertyValue = Any()
    try:
        request.propertyValue.cast_in(value)
    except WritePropertyCastError as error:
        raise ValueError("WriteProperty cast error: %r", error)

    # optional array index
    if indx is not None:
        request.propertyArrayIndex = indx

    # optional priority
    if priority is not None:
        request.priority = priority
    return request
