#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
BasicScript - implement the BAC0.core.app.ScriptApplication
Its basic function is to start and stop the bacpypes stack.
Stopping the stack, frees the IP socket used for BACnet communications. 
No communications will occur if the stack is stopped.

Bacpypes stack enables Whois and Iam functions, since this minimum is needed to be 
a BACnet device.  Other stack services can be enabled later (via class inheritance).
[see: see BAC0.scripts.ReadWriteScript]

Class::
    BasicScript(WhoisIAm)
        def startApp()
        def stopApp()
"""
#--- standard Python modules ---
from threading import Thread
import random
import sys

#--- 3rd party modules ---

from bacpypes.core import run as startBacnetIPApp
from bacpypes.core import stop as stopBacnetIPApp
from bacpypes.core import enable_sleeping
from bacpypes.local.device import LocalDeviceObject
from bacpypes.basetypes import ServicesSupported, DeviceStatus
from bacpypes.primitivedata import CharacterString

#--- this application's modules ---
from ..core.app.ScriptApplication import SimpleApplication, ForeignDeviceApplication
from .. import infos

from ..core.utils.notes import note_and_log

#------------------------------------------------------------------------------


@note_and_log
class Base():
    """
    Build a running BACnet/IP device that accepts WhoIs and IAm requests
    Initialization requires some minimial information about the local device.

    :param localIPAddr='127.0.0.1':
    :param localObjName='BAC0':
    :param DeviceId=None:
    :param maxAPDULengthAccepted='1024':
    :param maxSegmentsAccepted='1024':
    :param segmentationSupported='segmentedBoth':
    """

    def __init__(self, localIPAddr='127.0.0.1',
                 localObjName='BAC0', DeviceId=None,
                 maxAPDULengthAccepted='1024', maxSegmentsAccepted='1024',
                 segmentationSupported='segmentedBoth',
                 bbmdAddress=None, bbmdTTL=0):

        self._log.debug("Configurating app")

        self.response = None
        self._initialized = False
        self._started = False
        self._stopped = False

        self.localIPAddr = localIPAddr
        
        self.Boid = int(DeviceId) if DeviceId else (
            3056177 + int(random.uniform(0, 1000)))

        self.segmentationSupported = segmentationSupported
        self.maxSegmentsAccepted = maxSegmentsAccepted
        self.localObjName = localObjName

        self.maxAPDULengthAccepted = maxAPDULengthAccepted
        self.vendorId = 842
        self.vendorName = CharacterString('SERVISYS inc.')
        self.modelName = CharacterString('BAC0 Scripting Tool')

        self.discoveredDevices = None
        self.systemStatus = DeviceStatus(1)

        self.bbmdAddress = bbmdAddress
        self.bbmdTTL = bbmdTTL

        self.startApp()

    def startApp(self):
        """
        Define the local device, including services supported.
        Once defined, start the BACnet stack in its own thread.
        """
        self._log.debug("Create Local Device")
        try:
            # make a device object
            self.this_device = LocalDeviceObject(
                objectName=self.localObjName,
                objectIdentifier=self.Boid,
                maxApduLengthAccepted=int(self.maxAPDULengthAccepted),
                segmentationSupported=self.segmentationSupported,
                vendorIdentifier=self.vendorId,
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
#            pss = ServicesSupported()
#            pss['whoIs'] = 1
#            pss['iAm'] = 1
#            pss['readProperty'] = 1
#            pss['writeProperty'] = 1
#            pss['readPropertyMultiple'] = 1
#
#            # set the property value to be just the bits
#            self.this_device.protocolServicesSupported = pss.value

            # make an application
            if self.bbmdAddress and self.bbmdTTL > 0:

                self.this_application = ForeignDeviceApplication(self.this_device, self.localIPAddr,
                                                                 bbmdAddress=self.bbmdAddress, bbmdTTL=self.bbmdTTL)
                app_type = 'Foreign Device'
            else:
                self.this_application = SimpleApplication(
                    self.this_device, self.localIPAddr)
                app_type = 'Simple BACnet/IP App'
            self._log.debug("Starting")
            self._initialized = True
            try:
                self._startAppThread()
                self._log.info("Registered as {}".format(app_type))
            except:
                self._log.warning("Error opening socket")
                raise
            self._log.debug("Running")

        except Exception as error:
            self._log.error("an error has occurred: {}".format(error))
        finally:
            self._log.debug("finally")

    def register_foreign_device(self, addr=None, ttl=0):
        self.this_application.bip.register(addr, ttl)

    def unregister_foreign_device(self):
        self.this_application.bip.unregister()

    def disconnect(self):
        """
        Stop the BACnet stack.  Free the IP socket.
        """
        self._log.debug('Stopping BACnet stack')
        # Freeing socket
        try:
            self.this_application.mux.directPort.handle_close()
        except:
            self.this_application.mux.broadcastPort.handle_close()

        stopBacnetIPApp()           # Stop Core
        self._stopped = True        # Stop stack thread
        self.t.join()
        self._started = False
        self._log.info('BACnet stopped')

    def _startAppThread(self):
        """
        Starts the BACnet stack in its own thread so requests can be processed.
        As signal cannot be called in another thread than the main thread
        when calling startBacnetIPApp, we must pass None to both parameters
        """
        self._log.info('Starting app...')
        enable_sleeping(0.0005)
        self.t = Thread(target=startBacnetIPApp, kwargs={
                        'sigterm': None, 'sigusr1': None}, daemon=True)
        self.t.start()
        self._started = True
        self._log.info('BAC0 started')
