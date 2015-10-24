#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module define discoverPoints function
"""

from ..devices.Points import EnumPoint, BooleanPoint, NumericPoint

try:
    import pandas as pd
    _PANDA = True
except:
    _PANDA = False


def discoverPoints(bacnetapp, address, devID):
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
    pss = bacnetapp.read(
        '%s device %s protocolServicesSupported' % (address, devID))
    deviceName = bacnetapp.read('%s device %s objectName' % (address, devID))
    print('Found %s... building points list' % deviceName)
    objList = bacnetapp.read('%s device %s objectList' % (address, devID))
    newLine = []
    result = []
    points = []

    for pointType, pointAddr in objList:
        if pointType not in 'file calendar device schedule notificationClass eventLog':
            if 'binary' not in pointType and 'multiState' not in pointType:
                newLine = [pointType, pointAddr]
                newLine.extend(bacnetapp.readMultiple(
                    '%s %s %s objectName description presentValue units' % (address, pointType, pointAddr)))
                newPoint = NumericPoint(pointType=newLine[0], pointAddress=newLine[1], pointName=newLine[
                                        2], description=newLine[3], presentValue=newLine[4], units_state=newLine[5])
            elif 'binary' in pointType:
                newLine = [pointType, pointAddr]
                infos = (bacnetapp.readMultiple(
                    '%s %s %s objectName description presentValue inactiveText activeText' % (address, pointType, pointAddr)))
                newLine.extend(infos[:-2])
                newLine.extend([infos[-2:]])
                newPoint = BooleanPoint(pointType=newLine[0], pointAddress=newLine[1], pointName=newLine[
                                        2], description=newLine[3], presentValue=newLine[4], units_state=newLine[5])
            elif 'multiState' in pointType:
                newLine = [pointType, pointAddr]
                newLine.extend(bacnetapp.readMultiple(
                    '%s %s %s objectName description presentValue stateText' % (address, pointType, pointAddr)))
                newPoint = EnumPoint(pointType=newLine[0], pointAddress=newLine[1], pointName=newLine[
                                     2], description=newLine[3], presentValue=newLine[4], units_state=newLine[5])
            result.append(newLine)
            points.append(newPoint)
    if _PANDA:
        df = pd.DataFrame(result, columns=['pointType', 'pointAddress', 'pointName',
                                           'description', 'presentValue', 'units_state']).set_index(['pointName'])
    else:
        df = result
    print('Ready!')
    return (deviceName, pss, objList, df, points)
