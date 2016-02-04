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

import time



class SQLMixin(object):
    """
    A mixin to be used with a Device to backup to SQL.
    """
    def to_sql(self, filename = 'backup'):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        fname = '%s_%s.db' % (filename, timestr)
        cnx = sqlite3.connect(fname)
    
        backup = pd.DataFrame()
        
        for point in self.points:
            if point.history.dtypes == object:
                backup[point.properties.name] = point.history.replace(['inactive', 'active'], [0, 1]).resample('1s')
            else:
                backup[point.properties.name] = point.history.resample('1s')
            
        sql.to_sql(backup, name='history', con=cnx, index_label = 'index', index = True, if_exists = 'replace')
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