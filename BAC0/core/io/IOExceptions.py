#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
IOExceptions.py - BAC0 application level exceptions 
"""


class WritePropertyException(Exception):
    """
    This exception is used when trying to write a property.
    """

    pass


class WritePropertyCastError(Exception):
    """
    This exception is used when trying to write to a property and a cast error occurs.
    """

    pass


class UnknownPropertyError(Exception):
    pass


class UnknownObjectError(Exception):
    pass


class ReadPropertyException(ValueError):
    """
    This exception is used when trying to read a property.
    """

    pass


class ReadPropertyMultipleException(ValueError):
    """
    This exception is used when trying to read multiple properties.
    """

    pass


class ReadRangeException(ValueError):
    """
    This exception is used when trying to read a property.
    """

    pass


class NoResponseFromController(Exception):
    """
    This exception is used when trying to read or write and there is not answer.
    """

    pass


class UnrecognizedService(Exception):
    """
    This exception is used when trying to read or write and there is not answer.
    """

    pass


class WriteAccessDenied(Exception):
    """
    This exception is used when trying to write and controller refuse it.
    """

    pass


class APDUError(Exception):
    pass


class OutOfServiceNotSet(Exception):
    """
    This exception is used when trying to simulate a point and the out of service property is false.
    """

    pass


class OutOfServiceSet(Exception):
    """
    This exception is used when trying to set the out of service property to
    false to release the simulation...and it doesn't work.
    """

    pass


class NetworkInterfaceException(Exception):
    """
    This exception covers different network related exc eption (like finding IP 
    or subnet mask...)
    """

    pass


class ApplicationNotStarted(Exception):
    """
    Application not started, no communication available.
    """

    pass


class BokehServerCantStart(Exception):
    """
    Raised if Bokeh Server can't be started automatically
    """

    pass


class SegmentationNotSupported(Exception):
    pass


class BadDeviceDefinition(Exception):
    pass


class InitializationError(Exception):
    pass


class Timeout(Exception):
    pass


class RemovedPointException(Exception):
    """
    When defining a device from DB it may not be identical to the 
    actual device.
    """

    pass


class BufferOverflow(Exception):
    """
    Buffer capacity of device exceeded.
    """

    pass


# For devices
class DeviceNotConnected(Exception):
    pass


class WrongParameter(Exception):
    pass
