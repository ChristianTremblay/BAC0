#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
from ..functions.discoverPoints import discoverPoints

from .Points import NumericPoint, BooleanPoint, EnumPoint

class Device():
    """
    Bacnet device
    This class represents a controller. When defined, it allows
    the use of read, write, sim, release functions to communicate
    with the device on the network
    """
    def __init__(self,addr,devId,bacnetApp):
        """
        Initialization require address, device id and bacnetApp (the script itself)
        :param addr: address of the device (ex. '2:5')
        :param devId: bacnet device ID (boid)
        :param bacnetApp: the script itself
        """
        self.addr = addr
        self.deviceID = devId
        self.bacnetApp = bacnetApp
        self.points = []
        self.name = ''
        self.discover()
        self.simPoints = []

        
    def discover(self):
        """
        Read all points of the device and creates a dataframe (Pandas) to store
        the list and allow quick access.
        This list will be used to access variables based on point name
        """
        result = discoverPoints(self.bacnetApp,(self.addr),self.deviceID)
        self.points = result[3]
        self.name = result[0]
        
    def read(self,args):
        """
        Read a point from a device
        
        :param args: point name
        :returns: value read
        """
        pointName = args
        try:
            val = self.bacnetApp.read('%s %s %s presentValue' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

        if 'multiState' in self.points.ix[pointName].pointType:
            return EnumPoint(val,self.points.ix[pointName].units_state)
        elif 'binary' in self.points.ix[pointName].pointType:
            return BooleanPoint(val,self.points.ix[pointName].units_state)
        else:
            return NumericPoint(val,self.points.ix[pointName].units_state)
        
    def write(self,args):
        """
        Write to present value of a point of a device
        
        :param args: (str) pointName value (both info in same string)
       
        """
        pointName, value = self.parseArgs(args)
        try:                
            self.bacnetApp.write('%s %s %s presentValue %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def default(self,args):
        """
        Write to relinquish default value of a point of a device
        
        :param args: (str) pointName value (both info in same string)
       
        """
        pointName, value = self.parseArgs(args)
        try:                
            self.bacnetApp.write('%s %s %s relinquishDefault %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def sim(self,args):
        """
        Simulate a value 
        Will write to out_of_service property (true)
        Will then write the presentValue so the controller will use that value
        The point name will be added to the list of simulated points
        (self.simPoints)        
        
        :param args: (str) pointName value (both info in same string)

        """
        pointName, value = self.parseArgs(args)
        try:
            self.bacnetApp.sim('%s %s %s presentValue %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
            if pointName not in self.simPoints:
                self.simPoints.append(pointName)
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

            
    def releaseAllSim(self):
        """
        Release all points stored in the self.simPoints variable 
        Will write to out_of_service property (false)
        The controller will take control back of the presentValue
        """
        for pointName in self.simPoints:
            try:
                self.bacnetApp.release('%s %s %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
                if pointName in self.simPoints:
                    self.simPoints.pop(pointName)
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)
                
    def release(self,args):
        """
        Release points 
        Will write to out_of_service property (false)
        The controller will take control back of the presentValue

        :param args: (str) pointName        
        """

        pointName = args
        try:
            self.bacnetApp.release('%s %s %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
            if pointName in self.simPoints:
                self.simPoints.remove(pointName)
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)
            
    def ovr(self,args):
        """
        Override the output (Make manual operator command on point at priority 8)

        :param args: (str) pointName value (both info in same string)
       
        """
        pointName, value = self.parseArgs(args)
        try:                
            self.bacnetApp.write('%s %s %s presentValue %s - 8' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

    def auto(self,args):
        """
        Release the override on the output (Write null on point at priority 8)

        :param args: (str) pointName value (both info in same string)
       
        """
        pointName, value = self.parseArgs(args)
        try:                
            self.bacnetApp.write('%s %s %s presentValue %s - 8' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
        except KeyError:
            raise Exception('Unknown point name : %s' % pointName)

                
    def parseArgs(self,arg):
        args = arg.split()
        pointName = ' '.join(args[:-1])
        value = args[-1]
        return (pointName, value)