#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
debug.py - Helper functions to log debug and exception messages

'''

#--- standard Python modules ---
from functools import wraps, partial
import logging
import inspect

#--- 3rd party modules ---
#--- this application's modules ---

#------------------------------------------------------------------------------

_DEBUG = 1

def debug(func):
    if 'debug' in inspect.getargspec(func).args:
        raise TypeError('debug argument already defined')
        
    @wraps(func)
    def wrapper(*args, debug=False, **kwargs):
        if debug:
            print('Calling', func.__name__)
        return func(*args, **kwargs)

    
    sig = inspect.signature(func)
    parms = list(sig.parameters.values())
    parms.append(inspect.Parameter('debug',
                                   inspect.Parameter.KEYWORD_ONLY,
                                   default=False))
    wrapper.__signature__ = sig.replace(parameters=parms)                              
    return wrapper                            


def log_debug(cls,txt, *args):
    """
    Helper function to log debug messages
    """
    if _DEBUG:
        msg= (txt % args) if args else txt
        # pylint: disable=E1101,W0212
        cls._debug(msg)

def log_warning(cls,txt, *args):
    """
    Helper function to log debug messages
    """
    if _DEBUG:
        msg= (txt % args) if args else txt
        # pylint: disable=E1101,W0212
        cls._warning(msg)

def log_exception(cls,txt, *args):
    """
    Helper function to log debug messages
    """
    msg= (txt % args) if args else txt
    # pylint: disable=E1101,W0212
    cls._exception(msg)

# This has been taken in Python Cookbook, chapter 9.5
def attach_wrapper(obj, func=None):
    if func is None:
        return partial(attach_wrapper, obj)
    setattr(obj, func.__name__, func)
    return func

def _logged(level, name=None, message=None):
    """
    Add loging to a function. Level is the logging level, name is the
    logger name, and message is the log message.
    If name and message are not specified, they default
    to function's default module and name
    """
    def decorate(func):
        logname = name if name else func.__module__
        log = logging.getLogger(logname)
        logmsg = message if message else func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            log.log(level, logmsg)
            return func(*args, **kwargs)
        
        # Attach setter functions
        @attach_wrapper(wrapper)
        def set_level(newlevel):
            nonlocal level
            level = newlevel
            
        @attach_wrapper(wrapper)
        def set_message(newmsg):
            nonlocal logmsg
            logmsg = newmsg
            
        return wrapper
    return decorate

def logged(func=None, *, level=logging.DEBUG, name=None, message=None):
    if func is None:
        return partial(logged, level=level, name = name, message = message)
    
    logname = name if name else func.__module__
    log = logging.getLogger(logname)
    logmsg = message if message else func.__name__
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        log.log(level, logmsg)
        return func(*args, **kwargs)
    return wrapper