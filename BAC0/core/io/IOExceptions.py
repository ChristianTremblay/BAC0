#!/usr/bin/python
"""
Module : Reap.py
Author : Christian Tremblay, ing.
Inspired a lot by the work of Joel Bender (joel@carrickbender.com)
Email : christian.tremblay@servisys.com
"""

class WritePropertyException(Exception):
    """
    Write Exception
    """
    pass

class WritePropertyCastError(Exception):
    """
    Write Property Cast Exception
    """
    pass

class ReadPropertyException(Exception):
    """
    Read Property Exception
    """
    pass

class ReadPropertyMultipleException(Exception):
    """
    Read Property Multiple Exception
    """
    pass

