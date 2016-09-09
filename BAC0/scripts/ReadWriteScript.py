#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This Script object is an extended version of the basicScript.
As everything is handled by the BasicScript, you only need to select the features
you want::

    # Create a class that will implement a basic script with read and write functions
    from BAC0.scripts.BasicScript import BasicScript
    from BAC0.core.io.Read import ReadProperty
    from BAC0.core.io.Write import WriteProperty
    class ReadWriteScript(BasicScript,ReadProperty,WriteProperty)

Once the class is created, create the object and use it::

    bacnet = ReadWriteScript(localIPAddr = '192.168.1.10')
    bacnet.read('2:5 analogInput 1 presentValue)

"""

from bacpypes.debugging import bacpypes_debugging

from ..scripts.BasicScript import BasicScript
from ..core.io.Read import ReadProperty
from ..core.io.Write import WriteProperty
from ..core.functions.GetIPAddr import HostIP
from ..core.functions.WhoisIAm import WhoisIAm
from ..core.io.Simulate import Simulation
from ..core.io.IOExceptions import BokehServerCantStart
from ..bokeh.BokehRenderer import BokehSession, BokehDocument
from ..bokeh.BokehServer import BokehServer


import requests
import time
import logging

# some debugging
_DEBUG = 0


@bacpypes_debugging
class ReadWriteScript(BasicScript, WhoisIAm, ReadProperty, WriteProperty, Simulation):
    """
    This class build a running bacnet application and will accept read ans write requests
    Whois and IAm function are also possible as they are implemented in the BasicScript class.

    Once created, the object will call a ``whois()`` function to build a list of controllers available.

    """

    def __init__(self, ip=None):
        """
        Initialization requires information on the local device

        :param ip: (str) '127.0.0.1'

        Normally, the address must be in the same subnet than the bacnet network (if no BBMD or Foreign device is used)
        Actual app doesn't support BBMD or FD

        You need to pass the args to the parent BasicScript

        """
        log_debug("Configurating app")
        if ip is None:
            host = HostIP()
            ip_addr = host.address
        else:
            ip_addr = ip
        BasicScript.__init__(self, localIPAddr=ip_addr)
        self.bokehserver = False
        # Force and global whois to find all devices on the network
        self.whois()
        self.start_bokeh()
        
    def start_bokeh(self):
        try:
            print('Starting Bokeh Serve')
            logging.getLogger("requests").setLevel(logging.INFO)
            self.BokehServer = BokehServer()
            self.BokehServer.start()
            attemptedConnections = 0
            while True:
                try:
                    requests.get('http://localhost:5006')
                    break
                except requests.exceptions.ConnectionError:                 
                    attemptedConnections += 1
                    if attemptedConnections > 10:
                        raise BokehServerCantStart
                time.sleep(1)                

            self.bokehserver = True
            self.bokeh_document = BokehDocument(title = 'BAC0 - Live Trending')
            self.new_bokeh_session()
            self.bokeh_session.loop()
        except OSError as error:
            self.bokehserver = False
            print('Please start bokeh serve to use trending features')
            print('controller.chart will not work')
            print(error)
        except RuntimeError as rterror:
            self.bokehserver = False
            print('Server already running')
        except BokehServerCantStart:
            self.bokehserver = False
            print("Can't start Bokeh Server")
            print('controller.chart will not work')

    def new_bokeh_session(self):
        self.bokeh_session = BokehSession(self.bokeh_document.document)

    def __repr__(self):
        return 'Bacnet Network using ip %s with device id %s' % (self.localIPAddr, self.Boid)


def log_debug(txt, *args):
    """
    Helper function to log debug messages
    """
    if _DEBUG:
        if args:
            msg = txt % args
        else:
            msg = txt
        # pylint: disable=E1101,W0212
        BasicScript._debug(msg)


def log_exception(txt, *args):
    """
    Helper function to log debug messages
    """
    if args:
        msg = txt % args
    else:
        msg = txt
    # pylint: disable=E1101,W0212
    BasicScript._exception(msg)
