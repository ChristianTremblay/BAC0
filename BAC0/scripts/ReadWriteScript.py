#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
ReadWriteScript - extended version of BasicScript.py

As everything is handled by the BasicScript, select the additional features you want::

    # Create a class that implements a basic script with read and write functions
    from BAC0.scripts.BasicScript import BasicScript
    from BAC0.core.io.Read import ReadProperty
    from BAC0.core.io.Write import WriteProperty
    class ReadWriteScript(BasicScript,ReadProperty,WriteProperty)

Once the class is created, create the local object and use it::

    bacnet = ReadWriteScript(localIPAddr = '192.168.1.10')
    bacnet.read('2:5 analogInput 1 presentValue)

'''
#--- standard Python modules ---
import requests
import time
import logging

#--- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging

#--- this application's modules ---
from ..scripts.BasicScript import BasicScript

from ..core.io.Read import ReadProperty
from ..core.io.Write import WriteProperty
from ..core.functions.GetIPAddr import HostIP
from ..core.functions.WhoisIAm import WhoisIAm
from ..core.io.Simulate import Simulation
from ..core.io.IOExceptions import BokehServerCantStart

from ..bokeh.BokehRenderer import BokehSession, BokehDocument
from ..bokeh.BokehServer import BokehServer

#------------------------------------------------------------------------------

# some debugging
_DEBUG = 0


@bacpypes_debugging
class ReadWriteScript(BasicScript, WhoisIAm, ReadProperty, WriteProperty, Simulation):
    """
    Build a BACnet application to accept read and write requests.
    [Basic Whois/IAm functions are implemented in parent BasicScript class.]
    Once created, execute a whois() to build a list of available controllers.
    Initialization requires information on the local device.

    :param ip='127.0.0.1': Address must be in the same subnet as the BACnet network 
        [BBMD and Foreign Device - not supported] 
    """
    def __init__(self, ip=None):
        self._log = logging.getLogger('BAC0.script.%s' \
                    % self.__class__.__name__)
        self._log.debug("Configurating app")
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
            self._log.info('Starting Bokeh Serve')
            
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
            self._log.error('[bokeh serve] required for trending (controller.chart) features')
            self._log.error(error)

        except RuntimeError as rterror:
            self.bokehserver = False
            self._log.error('Server already running')

        except BokehServerCantStart:
            self.bokehserver = False
            self._log.error('No Bokeh Server - controller.chart not available')


    def new_bokeh_session(self):
        self.bokeh_session = BokehSession(self.bokeh_document.document)

    def __repr__(self):
        return 'Bacnet Network using ip %s with device id %s' % (self.localIPAddr, self.Boid)


def log_debug(txt, *args):
    """ Helper function to log debug messages
    """
    if _DEBUG:
        msg= (txt % args) if args else txt
        BasicScript._debug(msg)


def log_exception(txt, *args):
    """ Helper function to log debug messages
    """
    msg= (txt % args) if args else txt
    BasicScript._exception(msg)
