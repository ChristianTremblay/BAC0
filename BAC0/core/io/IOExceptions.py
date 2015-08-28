#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Definition of exceptions
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

class ReadPropertyException(Exception):
    """
    This exception is used when trying to read a property.
    """
    pass

class ReadPropertyMultipleException(Exception):
    """
    This exception is used when trying to read multiple properties.
    """
    pass

class NoResponseFromController(Exception):
    """
    This exception is used when trying to read or write and there is not answer.
    """
    pass 

class OutOfServiceNotSet(Exception):
    """
    This exception is used when trying to simulate a point and the out of service property is false.
    """
    pass 

class OutOfServiceSet(Exception):
    """
    This exception is used when trying to set the out of service property to false to release the simulation...and it doesn't work.
    """
    pass 