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
            val = self.bacnetApp.read('%s %s %s presentValue' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)))
        else:
            val = self.bacnetApp.read(args)
        return val
        
    def write(self,args):
        """
        Write to present value of a point of a device
        """
        if len(args.split()) == 2:
            pointName, value = args.split()
            self.bacnetApp.write('%s %s %s presentValue %s' % (self.addr,self.points.ix[pointName].pointType,str(self.points.ix[pointName].pointAddress)),value)
        else:
            self.bacnetApp.write(args)   