#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Simple Bacnet Device
"""
from ..functions.discoverPoints import discoverPoints

class Device():
    """
    Bacnet device
    """
    def __init__(self,addr,devId,bacnetApp):
        self.addr = addr
        self.deviceID = devId
        self.bacnetApp = bacnetApp
        self.points = []
        self.name = ''
        self.discover()
        self.simPoints = []

        
    def discover(self):
        result = discoverPoints(self.bacnetApp,(self.addr),self.deviceID)
        self.points = result[3]
        self.name = result[0]
        
    def read(self,args):
        """
        Read a point from a device
        """
        if len(args.split()) == 1:
            pointName = args
            try:
                val = self.bacnetApp.read('%s %s %s presentValue' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)
        else:
            val = self.bacnetApp.read(args)
        return val
        
    def write(self,args):
        """
        Write to present value of a point of a device
        """
        if len(args.split()) == 2:
            pointName, value = args.split()
            try:                
                self.bacnetApp.write('%s %s %s presentValue %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)
        else:
            self.bacnetApp.write(args)   

    def sim(self,args):
        """
        Simulate a value with out_of_service feature
        """
        if len(args.split()) == 2:
            pointName, value = args.split()
            try:
                self.bacnetApp.sim('%s %s %s presentValue %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress),value))
                if pointName not in self.simPoints:
                    self.simPoints.append(pointName)
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)
        else:
            self.bacnetApp.write(args)
            
    def releaseAllSim(self):
        """
        Release points (out_of_service = false)
        """
        for pointName in self.simPoints:
            try:
                self.bacnetApp.release('%s %s %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
                if pointName in self.simPoints:
                    self.simPoints.pop(pointName)
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)
                
    def release(self,args):
        if len(args.split()) == 1:
            pointName = args
            try:
                self.bacnetApp.release('%s %s %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
                if pointName in self.simPoints:
                    self.simPoints.pop(pointName)
            except KeyError:
                raise Exception('Unknown point name : %s' % pointName)
        else:
            self.bacnetApp.release(args)  