#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module define discoverPoints function
"""

try:
    import pandas as pd
    _PANDA = True
except:
    _PANDA= False

def discoverPoints(bacnetapp,address, devID):
    """
    This function allows the discovery of all bacnet points in a device

    :param bacnetApp: The app itself so we can call read
    :param address: address of the device as a string (ex. '2:5')
    :param devID: device ID of the bacnet device as a string (ex. '1001')    
    
    :returns: a tuple with deviceName, pss, objList, df
    
    *deviceName* : name of the device
    *pss* : protocole service supported
    *objList* : list of bacnet object (ex. analogInput, 1)
    *df* : is a dataFrame containing pointType, pointAddress, pointName, description
    presentValue and units

    If pandas can't be found, df will be a simple array    
    
    """
    pss = bacnetapp.read('%s device %s protocolServicesSupported' % (address,devID))
    deviceName = bacnetapp.read('%s device %s objectName' % (address,devID))
    print('Found %s... building points list' % deviceName)
    objList = bacnetapp.read('%s device %s objectList' % (address,devID))
    newLine = []   
    result = []
    
    for each in objList:
        if each[0] not in 'file calendar device schedule notificationClass eventLog':
            if 'binary' not in each[0] and 'multiState' not in each[0]:
                newLine = [each[0],each[1]]
                newLine.extend(bacnetapp.readMultiple('%s %s %s objectName description presentValue units' % (address, each[0], each[1])))
            else:
                newLine = [each[0],each[1]]
                newLine.extend(bacnetapp.readMultiple('%s %s %s objectName description presentValue' % (address, each[0], each[1])))
            result.append(newLine)
    if _PANDA:       
        df = pd.DataFrame(result, columns=['pointType','pointAddress','pointName','description','presentValue','units']).set_index(['pointName'])
    else:
        df = result
    print('Ready!')
    return (deviceName,pss,objList,df)




