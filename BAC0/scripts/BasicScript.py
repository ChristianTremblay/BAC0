#!/usr/bin/python

"""
Built around a simple BIPSimpleApplication this class allows to create read and write
requests and store read responses in a variables

For 'read' commands it will create ReadPropertyRequest PDUs, then lines up the
coorresponding ReadPropertyACK and return the value. 

For 'write' commands it will create WritePropertyRequst PDUs and prints out a simple acknowledgement.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.core import run as startBacnetIPApp
from bacpypes.core import stop as stopBacnetIPApp
from bacpypes.app import LocalDeviceObject
from bacpypes.basetypes import ServicesSupported


from threading import Thread

from ..core.functions.WhoisIAm import WhoisIAm
from ..core.app.ScriptApplication import ScriptApplication
 

# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class BasicScript(WhoisIAm):
    """ 
    This class build a running bacnet application and will accept whois ans iam requests
    
    """
    def __init__(self, localIPAddr = '127.0.0.1', localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorID = '15' ):
        """
        Initialization requires information on the local device
        Default values are localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorID = '15' )
        Local IP address must be given in a string.
        Normally, the address must be in the same subnet than the bacnet network (if no BBMD or Foreign device is used)        
        """     
        if _debug: _log.debug("Configurating app")
        self.response = None
        self._initialized = False
        self._started = False
        self._stopped = False
        self.localIPAddr = localIPAddr
        self.segmentationSupported = segmentationSupported
        self.localObjName = localObjName
        self.Boid = Boid
        self.maxAPDULengthAccepted = maxAPDULengthAccepted
        self.vendorID = vendorID
        self.discoveredDevices = None
        
                
        self.startApp()
            
            
    def startApp(self):
        if _debug: _log.debug("App initialization")
        try:
            # make a device object
            self.this_device = LocalDeviceObject(
                objectName=self.localObjName,
                objectIdentifier=int(self.Boid),
                maxApduLengthAccepted=int(self.maxAPDULengthAccepted),
                segmentationSupported=self.segmentationSupported,
                vendorIdentifier=int(self.vendorID),
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
            
        
            _log.debug("running")
            self._initialized = True
            self._startAppThread()
        except Exception as e:
            _log.exception("an error has occurred: %s", e)
        finally:
            _log.debug("finally")
    
            
    def stopApp(self):
        """
        Used to stop the application
        Not working actually
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
        """
        print('Starting app...')
        self.t = Thread(target=startBacnetIPApp)
        self.t.start()
        self._started = True
        print('App started')


