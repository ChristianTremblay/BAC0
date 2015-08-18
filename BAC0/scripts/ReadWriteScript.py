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

from bacpypes.debugging import bacpypes_debugging, ModuleLogger

from BAC0.scripts.BasicScript import BasicScript
from BAC0.core.io.Read import ReadProperty
from BAC0.core.io.Write import WriteProperty
from BAC0.core.io.Simulate import Simulation

# some debugging
_debug = 0
_log = ModuleLogger(globals())

@bacpypes_debugging
class ReadWriteScript(BasicScript,ReadProperty,WriteProperty,Simulation):
    """ 
    This class build a running bacnet application and will accept read ans write requests
    Whois and IAm function are also possible as they are implemented in the BasicScript class.
    
    Once created, the object will call a ``whois()`` function to build a list of controllers available.
    
    """
    def __init__(self, localIPAddr = '127.0.0.1', localObjName = 'name', Boid = '2015',maxAPDULengthAccepted = '1024',segmentationSupported = 'segmentedBoth', vendorId = '842' ):
        """
        Initialization requires information on the local device

        :param localObjName: Name of the local device (default is 'name')
        :param Boid: Bacnet object ID. Remember that there must be only 1 instance of this ID on the entire bacnet network (range 0 to 4194304 ; default : 2015)'
        :param maxAPDULengthAccepted: default '1024'
        :param segmentationSupported: default 'segmentedBoth'
        :param vendorId: default '842'
        :param localIPAddr: (str) '127.0.0.1'        
        
        Normally, the address must be in the same subnet than the bacnet network (if no BBMD or Foreign device is used)  
        Actual app doesn't support BBMD or FD
        
        You need to pass the args to the parent BasicScript
        
        """     
        if _debug: _log.debug("Configurating app")
        BasicScript.__init__(self, localIPAddr = localIPAddr, localObjName = localObjName, Boid = Boid,maxAPDULengthAccepted = maxAPDULengthAccepted,segmentationSupported = segmentationSupported, vendorId = vendorId )
        
        # Force and gloab whois to find all devices on the network
        self.whois()
   
            
#
#   __main__
#
if __name__ == '__main__':
    bacnet = ReadWriteScript()




