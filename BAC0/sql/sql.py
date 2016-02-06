#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

import sqlite3
import pandas as pd
from pandas.io import sql
from pandas.lib import Timestamp
import pickle

import time



class SQLMixin(object):
    """
    A mixin to be used with a Device to backup to SQL.
    """
    def dev_properties_df(self):
        dic = self.properties.asdict
        dic.pop('charts', None)
        dic.pop('network', None)
        dic.pop('pss', None)
        dic.pop('serving_chart', None)
        dev = {}
        dev[self.properties.name] = dic
        df = pd.DataFrame(dev)
        return df
        
    
    def points_properties_df(self):
        """
        This returns a dict of point / point_properties so it can be saved to SQL
        """
        pprops = {}
        for each in self.points:
            #print(each.properties.asdict)
            p = each.properties.asdict
            p.pop('device', None)
            p.pop('network', None)
            p.pop('simulated', None)
            p.pop('overridden', None)
            pprops[each.properties.name] = p
        pprops
        df = pd.DataFrame(pprops)
        return df

    def backup_histories_df(self):
        backup = pd.DataFrame()
        for point in self.points:
            if point.history.dtypes == object:
                backup[point.properties.name] = point.history.replace(['inactive', 'active'], [0, 1]).resample('1s')
            else:
                backup[point.properties.name] = point.history.resample('1s')
        return backup

    def to_sql(self, filename = 'backup'):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        fname = '%s_%s.db' % (filename, timestr)
        cnx = sqlite3.connect(fname)
    
        # DataFrames that will be saved to SQL
        sql.to_sql(self.backup_histories_df(), name='history', con=cnx, index_label = 'index', index = True, if_exists = 'append')
        #sql.to_sql(self.points_properties_df(), name='points_properties', con=cnx, if_exists = 'replace')
        #sql.to_sql(self.dev_properties_df(), name='device_properties', con=cnx, if_exists = 'replace')
        # pickling properties 
        pickle.dump(self.points_properties_df(), open( "%s_prop.bin"  % self.properties.name, "wb" ))
        pickle.dump(self.dev_properties_df(), open( "%s_points_prop.bin"  % self.properties.name, "wb" ))
                
        print('%s saved to disk' % fname)
        
    def points_from_sql(self, db):
        points = sql.read_sql("SELECT * FROM history;", db) 
        return list(points.columns.values)[1:]
        
    def his_from_sql(self, db, point):
        his = sql.read_sql('select * from "%s"' % 'history', db)  
        his.index = his['index'].apply(Timestamp)
        return his.set_index('index')[point]
        
    def value_from_sql(self, db, point):
        """
        Take last known value as the value
        """
        return self.his_from_sql(db, point).last_valid_index()
        
    def point_prop(self, name, point):
        #prop = sql.read_sql('select %s from "%s"' % (point, 'points_properties'), db)
        return pickle.load(open( "%s_prop.bin" % name, "rb" ))[point]
        
    def dev_prop(self, name):
        #prop = sql.read_sql('select * from "%s"' % 'device_properties', db)
        return pickle.load(open( "%s_points_prop.bin" % name, "rb" ))
        