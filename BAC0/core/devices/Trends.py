#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Points.py - Definition of points so operations on Read results are more convenient.
'''

#--- standard Python modules ---
from datetime import datetime
from collections import namedtuple
import time

#--- 3rd party modules ---
try:
    import pandas as pd
    from pandas.io import sql
    try:
        from pandas import Timestamp
    except ImportError:
        from pandas.lib import Timestamp
    _PANDAS = True
except ImportError:
    _PANDAS = False
    
from bacpypes.object import TrendLogObject

#--- this application's modules ---
from ...tasks.Poll import SimplePoll as Poll
from ...tasks.Match import Match, Match_Value
from ..io.IOExceptions import NoResponseFromController, UnknownPropertyError
from ..utils.notes import note_and_log


#------------------------------------------------------------------------------

class TrendLogProperties(object):
    """
    A container for trend properties
    """

    def __init__(self):
        self.device = None
        self.oid = None
        self.object_name = None
        self.description = ''
        self.log_device_object_property = None
        self.buffer_size = 0
        self.record_count = 0
        self.total_record_count = 0
        self.description = None
        self.statusFlags = None
        self.status_flags = {'in_alarm':False,
                             'fault':False,
                             'overridden':False,
                             'out_of_service':False}

        self._df = None

@note_and_log
class TrendLog(TrendLogProperties):
    """
    BAC0 simplification of TrendLog Object
    """
    def __init__(self, OID, device=None, read_log_on_creation = True, multiple_request = None):
        self.properties = TrendLogProperties()
        self.properties.device = device
        self.properties.oid = OID
        try:
            self.properties.object_name,\
            self.properties.description,\
            self.properties.record_count,\
            self.properties.buffer_size,\
            self.properties.total_record_count,\
            self.properties.log_device_object_property,\
            self.properties.statusFlags = self.properties.device.properties.network.readMultiple('{addr} trendLog {oid} objectName description recordCount bufferSize totalRecordCount logDeviceObjectProperty statusFlags'.format(
                addr=self.properties.device.properties.address,
                oid=str(self.properties.oid)))

            if read_log_on_creation:
                self.read_log_buffer()
        except Exception:
            raise Exception('Problem reading trendLog informations')
        
    def read_log_buffer(self):
        try:
            _log_buffer = self.properties.device.properties.network.readRange('{} trendLog {} logBuffer'.format(
                self.properties.device.properties.address,
                str(self.properties.oid)))
            self.create_dataframe(_log_buffer)
        except Exception:
            raise Exception('Problem reading TrendLog')

    def create_dataframe(self,log_buffer):
        index = []
        logdatum = []
        status = []
        for each in log_buffer:
            year, month, day, dow = each.timestamp.date
            year = year + 1900
            hours, minutes, seconds, ms = each.timestamp.time
            index.append(pd.to_datetime('{}-{}-{} {}:{}:{}.{}'.format(year,month,day,hours,minutes,seconds,ms),format='%Y-%m-%d %H:%M:%S.%f'))
            logdatum.append(each.logDatum.dict_contents())
            status.append(each.statusFlags)
            
        if _PANDAS:    
            df = pd.DataFrame({'index':index,'logdatum':logdatum,'status':status})
            df = df.set_index('index')
            df['choice'] = df['logdatum'].apply(lambda x: list(x.keys())[0])
            df[self.properties.object_name] = df['logdatum'].apply(lambda x: list(x.values())[0])
    
            self.properties._df = df
        else:
            self.properties._history_components= (index,logdatum,status)
            self._log.warning('Pandas not installed. Treating histories as simple list.')
            

    @property
    def history(self):
        if _PANDAS:
            objectType, objectAddress = self.properties.log_device_object_property.objectIdentifier
            logged_point = self.properties.device.find_point(objectType,objectAddress) 
            serie = self.properties._df[self.properties.object_name].copy()
            serie.units = logged_point.properties.units_state
            serie.name = (
            '{}/{}').format(self.properties.device.properties.name, self.properties.object_name)
            if logged_point.properties.name in self.properties.device.binary_states:
                serie.states = 'binary'
            elif logged_point.properties.name in self.properties.device.multi_states:
                serie.states = 'multistates'
            else:
                serie.states = 'analog'
            serie.description = self.properties.description
            serie.datatype = objectType
            return serie
        else:
            return dict(zip(self.properties._history_components[0], self.properties._history_components[1]))
    
    def chart(self, remove=False):
        """
        Add point to the bacnet trending list
        """
        if not _PANDAS:
            self._log.error('Pandas must be installed to use live chart feature. See documentation how how to run BAC0 in complete mode')
        else:          
            if remove:
                self.properties.device.properties.network.remove_trend(self)
            else:
                self.properties.device.properties.network.add_trend(self)
