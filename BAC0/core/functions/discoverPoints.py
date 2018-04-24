#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
discoverPoints.py - allow discovery of BACnet points in a controller.
'''

#--- standard Python modules ---

#--- 3rd party modules ---
try:
    import pandas as pd
    _PANDA = True
except ImportError:
    _PANDA = False

#--- this application's modules ---
from ..devices.Points import EnumPoint, BooleanPoint, NumericPoint


#------------------------------------------------------------------------------

def discoverPoints(bacnetapp, address, devID):
    """
    Discover the BACnet points in a BACnet device.

    :param bacnetApp: The app itself so we can call read
    :param address: address of the device as a string (ex. '2:5')
    :param devID: device ID of the bacnet device as a string (ex. '1001')

    :returns: a tuple with deviceName, pss, objList, df

        * *deviceName* : name of the device
        * *pss* : protocole service supported
        * *objList* : list of bacnet object (ex. analogInput, 1)
        * *df* : is a dataFrame containing pointType, pointAddress, pointName, description
        presentValue and units

        If pandas can't be found, df will be a simple array
    """
    pss = bacnetapp.read('{} device {} protocolServicesSupported'.format(address, devID))
    deviceName = bacnetapp.read('{} device {} objectName'.format(address, devID))

    #print('Device {}- building points list'.format(deviceName))
    objList = bacnetapp.read('{} device {] objectList'.format(address, devID))

    newLine = []
    result = []
    points = []

    for pointType, pointAddr in objList:

        if 'binary' in pointType:           # BI/BO/BV
            newLine = [pointType, pointAddr]
            infos = bacnetapp.readMultiple(
                        '{} {} {} objectName description presentValue inactiveText activeText'.format(
                        address, pointType, pointAddr))

            newLine.extend(infos[:-2])
            newLine.extend([infos[-2:]])
            newPoint = BooleanPoint(pointType=newLine[0], pointAddress=newLine[1], 
                                    pointName=newLine[2], description=newLine[3], 
                                    presentValue=newLine[4], units_state=newLine[5])

        elif 'multiState' in pointType:     # MI/MV/MO
            newLine = [pointType, pointAddr]
            newLine.extend(bacnetapp.readMultiple(
                '{} {} {} objectName description presentValue stateText'.format(address, pointType, pointAddr)))
            
            newPoint = EnumPoint(pointType=newLine[0], pointAddress=newLine[1], 
                                 pointName=newLine[2], description=newLine[3], 
                                 presentValue=newLine[4], units_state=newLine[5])

        elif 'analog' in pointType:         # AI/AO/AV
            newLine = [pointType, pointAddr]
            newLine.extend(bacnetapp.readMultiple(
                '{} {} {} objectName description presentValue units'.format(address, pointType, pointAddr)))
            
            newPoint = NumericPoint(pointType=newLine[0], pointAddress=newLine[1], 
                                    pointName=newLine[2], description=newLine[3], 
                                    presentValue=newLine[4], units_state=newLine[5])

        else:
            continue        # skip

        result.append(newLine)
        points.append(newPoint)


    if _PANDA:
        df = pd.DataFrame(result, columns=['pointType', 'pointAddress', 'pointName',
                                           'description', 'presentValue', 'units_state']).set_index(['pointName'])
    else:
        df = result
        
    #print('Ready!')
    return (deviceName, pss, objList, df, points)
