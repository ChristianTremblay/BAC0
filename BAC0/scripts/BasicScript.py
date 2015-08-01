#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
BasicScript is an object that will implement the BAC0.core.app.ScriptApplication
The object will also implement basic function to start and stop this application.
Stopping the app allows to free the socket used by the app.
No communication will occur if the app is stopped.

The basic script will be able to use basic Whois and Iam function. Those features
are allowed by inheritance as the class will extend WhoisIAm class.

Adding other features will work the same way (see BAC0.scripts.ReadWriteScript)

Class::

    BasicScript(WhoisIAm)
        def startApp()
        def stopApp()

"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.core import run as startBacnetIPApp
from bacpypes.core import stop as stopBacnetIPApp
from bacpypes.app import LocalDeviceObject
from bacpypes.basetypes import ServicesSupported

from threading import Thread

from queue import Queue

from ..core.functions.WhoisIAm import WhoisIAm
from ..core.app.ScriptApplication import ScriptApplication
#import BAC0.core.functions as fn
 

# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class BasicScript(WhoisIAm):
    """ 
    This class build a running bacnet application and will accept whois ans iam requests
    
    """
    def __init__(self, localIPAddr = None, localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorId = '842' ):
        """
        Initialization requires information about the local device
        Default values are localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorId = '842' )
        Local IP address must be given in a string.
        Normally, the address must be in the same subnet than the bacnet network (if no BBMD or Foreign device is used)
        Script doesn't support BBMD actually
        """     
        if _debug: _log.debug("Configurating app")
        self.response = None
        self._initialized = False
        self._started = False
        self._stopped = False
        if localIPAddr:
            self.localIPAddr = localIPAddr
        else:
            self.localIPAddr = '127.0.0.1'
        self.segmentationSupported = segmentationSupported
        self.localObjName = localObjName
        self.Boid = Boid
        self.maxAPDULengthAccepted = maxAPDULengthAccepted
        self.vendorId = vendorId
        self.discoveredDevices = None
        self.ResponseQueue = Queue()
        
                
        self.startApp()
            
            
    def startApp(self):
        """
        This function is used to define the local device, including services supported.
        Once the application is defined, calls the _startAppThread which will handle the thread creation
        """
        if _debug: _log.debug("App initialization")
        try:
            # make a device object
            self.this_device = LocalDeviceObject(
                objectName=self.localObjName,
                objectIdentifier=int(self.Boid),
                maxApduLengthAccepted=int(self.maxAPDULengthAccepted),
                segmentationSupported=self.segmentationSupported,
                vendorIdentifier=int(self.vendorId),
                )
        
            # build a bit string that knows about the bit names
            pss = ServicesSupported()
            pss['whoIs'] = 1
            pss['iAm'] = 1
            pss['readProperty'] = 1
            pss['writeProperty'] = 1
        
            # set the property value to be just the bits
            self.this_device.protocolServicesSupported = pss.value
        
            # make a simple application
            self.this_application = ScriptApplication(self.this_device, self.localIPAddr)
            
        
            if _debug: _log.debug("Starting")
            self._initialized = True
            self._startAppThread()
            if _debug: _log.debug("Running")
        except Exception as e:
            _log.exception("an error has occurred: %s", e)
        finally:
            _log.debug("finally")
    
            
    def stopApp(self):
        """
        Used to stop the application
        Free the socket using ``handle_close()`` function
        Stop the thread
        """
        print('Stopping app')
        # Freeing socket
        try:
            self.this_application.mux.directPort.handle_close()
        except:
            self.this_application.mux.broadcastPort.handle_close()
        
        # Stopping Core        
        stopBacnetIPApp()
        self._stopped = True        
        # Stopping thread
        #print(Thread.is_alive)
        self.t.join()
        self._started = False
        print('App stopped')
        
    def _startAppThread(self):
        """
        Starts the application in its own thread so requests can be processed.
        Once started, socket will be reserved.
        """
        print('Starting app...')
        self.t = Thread(target=startBacnetIPApp)
        self.t.start()
        self._started = True
        print('App started')
