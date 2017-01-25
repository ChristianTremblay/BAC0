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
from bacpypes.core import enable_sleeping
from bacpypes.service.device import LocalDeviceObject
from bacpypes.basetypes import ServicesSupported, DeviceStatus
from bacpypes.primitivedata import CharacterString
from threading import Thread
import pandas as pd

from queue import Queue
import random
import sys


from ..core.app.ScriptApplication import ScriptApplication
from .. import infos
from ..core.io.IOExceptions import NoResponseFromController
#import BAC0.core.functions as fn


# some debugging
_DEBUG = 0


@bacpypes_debugging
class BasicScript():
    """
    This class build a running bacnet application and will accept whois ans iam requests

    """

    def __init__(self, localIPAddr=None, localObjName='BAC0', Boid=None,
                 maxAPDULengthAccepted='1024', segmentationSupported='segmentedBoth'):
        """
        Initialization requires information about the local device
        Default values are localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorId = '842' )
        Local IP address must be given in a string.
        Normally, the address must be in the same subnet than the bacnet network (if no BBMD or Foreign device is used)
        Script doesn't support BBMD actually
        """
        log_debug("Configurating app")

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
        if Boid:
            self.Boid = int(Boid)
        else:
            self.Boid = int('3056177') + int(random.uniform(0, 1000))
        self.maxAPDULengthAccepted = maxAPDULengthAccepted
        self.vendorId = '842'
        self.vendorName = CharacterString('SERVISYS inc.')
        self.modelName = CharacterString('BAC0 Scripting Tool')
        self.discoveredDevices = None
        #self.ResponseQueue = Queue()
        self.systemStatus = DeviceStatus(1)
        #self.this_application = None

        self.startApp()

    def startApp(self):
        """
        This function is used to define the local device, including services supported.
        Once the application is defined, calls the _startAppThread which will handle the thread creation
        """
        log_debug("App initialization")
        try:
            # make a device object
            self.this_device = LocalDeviceObject(
                objectName=self.localObjName,
                objectIdentifier=int(self.Boid),
                maxApduLengthAccepted=int(self.maxAPDULengthAccepted),
                segmentationSupported=self.segmentationSupported,
                vendorIdentifier=int(self.vendorId),
                vendorName=self.vendorName,
                modelName=self.modelName,
                systemStatus=self.systemStatus,
                description='http://christiantremblay.github.io/BAC0/',
                firmwareRevision=''.join(sys.version.split('|')[:2]),
                applicationSoftwareVersion=infos.__version__,
                protocolVersion=1,
                protocolRevision=0,

            )

            # build a bit string that knows about the bit names
            pss = ServicesSupported()
            pss['whoIs'] = 1
            pss['iAm'] = 1
            pss['readProperty'] = 1
            pss['writeProperty'] = 1
            pss['readPropertyMultiple'] = 1

            # set the property value to be just the bits
            self.this_device.protocolServicesSupported = pss.value

            # make a simple application
            self.this_application = ScriptApplication(
                self.this_device, self.localIPAddr)

            log_debug("Starting")
            self._initialized = True
            self._startAppThread()
            log_debug("Running")
        except Exception as error:
            log_exception("an error has occurred: %s", error)
        finally:
            log_debug("finally")

    def disconnect(self):
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
        # print(Thread.is_alive)
        self.t.join()
        self._started = False
        print('App stopped')

    def _startAppThread(self):
        """
        Starts the application in its own thread so requests can be processed.
        Once started, socket will be reserved.
        """
        print('Starting app...')
        enable_sleeping(0.0005)
        self.t = Thread(target=startBacnetIPApp, daemon = True)
        self.t.start()
        self._started = True
        print('App started')
        
    @property
    def devices(self):
        lst = []
        #self.whois()
        #print(self.discoveredDevices)
        for device in self.discoveredDevices:
            try:
                deviceName, vendorName = self.readMultiple('%s device %s objectName vendorName' % (device[0], device[1]))
                lst.append((deviceName, vendorName, device[0], device[1]))
            except NoResponseFromController:
                #print('No response from %s' % device)
                continue
        return pd.DataFrame(lst, columns=['Name', 'Manufacturer', 'Address',' Device ID']).set_index('Name').sort_values('Address')



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
