#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module allows the creation of threads that will be used as repetitive
tasks for simulation purposes
"""
from threading import Thread

import time
import random
from bokeh._legacy_charts import TimeSeries 
from bokeh.plotting import figure, output_server, cursession, show, ColumnDataSource
from bokeh.charts import Line
from bokeh._legacy_charts import Step
from bokeh.models import HoverTool
from bokeh.document import Document

from collections import OrderedDict
import logging
import math



class BokehRenderer(Thread):

    def __init__(self, device, points_list, *, title = 'My title', daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.exitFlag = False
        self.device = device
        self.points_list = points_list
        self.title = title
        self.units = {}
        
        logging.getLogger("requests").setLevel(logging.WARNING)
        output_server('Commissionning %s / %s' % (self.device.properties.name, self.title))
        TOOLS = "resize,hover,save,pan,box_zoom,wheel_zoom,reset"
        self.p = figure(plot_width=800, plot_height=600, x_axis_type="datetime", title = self.title, tools = TOOLS)
        cursession().publish()
        
    def run(self):
        self.process()

    def process(self):
        # if self.started = True
        while not self.exitFlag:
            self.task()

    def task(self):

        lst = self.points_list
        multi_states = self.device.multi_states
        binary_states = self.device.binary_states
        analog_units = self.device.analog_units        
        
        def read_lst():
            df = self.device[lst]
            try:
                df = df.fillna(method='ffill').fillna(method='bfill').replace(['inactive', 'active'], [0, 50])
            except TypeError:
                df = df.fillna(method='ffill').fillna(method='bfill')
                                          
            df = df.reset_index()
            df['name'] = 'nameToReplace'
            df['units'] = 'unit or state'
            return df
            
        df = read_lst()

        for each in lst:
            df['name'] = df['name'].replace('nameToReplace', ('%s / %s' % (each, self.device[each]['description'])))            
#            df['units'] = '.'
            source = ColumnDataSource(
                        data=dict(
                            x = df['index'],
                            y = df[each],
                            desc = df['name'],
                            units = df['units']
                        )
                    )

            if each in binary_states:
                self.p.circle('x', 
                            'y',
                            source = source,
                            name = each,
                            color = "#%06x" % random.randint(0x000000, 0x777777), 
                            legend=each,
                            size = 10)
            elif each in multi_states:
                self.p.diamond('x', 
                            'y',
                            source = source,
                            name = each,
                            color = "#%06x" % random.randint(0x000000, 0x777777), 
                            legend=each,
                            size = 20)            
            else:
                self.p.line('x',
                            'y',
                            source = source,
                            name = each,
                            color = "#%06x" % random.randint(0x000000, 0x777777),
                            legend=each, 
                            line_width = 2)
        
        hover = self.p.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ('name', '@desc'),
            ('value', '@y'),
            ('units', '@units'),
        ])
        show(self.p)
        
        while not self.exitFlag:
            # Update y data of the source object
            for renderer in self.p.renderers:
                name = renderer.name
                if name in lst:
                    df = read_lst()                
                    
                    glyph_renderer = renderer
                    df['name'] = df['name'].replace('nameToReplace', ('%s / %s' % (name, self.device[name]['description'])))
                    glyph_renderer.data_source.data['x'] = df['index']
                    glyph_renderer.data_source.data['y'] = df[name]
                    glyph_renderer.data_source.data['desc'] = df['name']
                    if name in multi_states:
                        glyph_renderer.data_source.data['units'] = [multi_states[name][int(math.fabs(x-1))] for x in df[name]]
                        #df['units'] = 'multi'
                    elif name in binary_states:
                        glyph_renderer.data_source.data['y'] = df[name]
                        glyph_renderer.data_source.data['units'] = [binary_states[name][int(x/50)] for x in df[name]]
                        #df['units'] = 'binaire'
                    else:
                        df['units'] = analog_units[name]
                        glyph_renderer.data_source.data['units'] = df['units']
                    #df['units'] = df['units'].replace('unit', ('%s' % self.device[each]['units']))
                    #glyph_renderer.data_source.data['units'] = df['units']
                    # store the updated source on the server
                    cursession().store_objects(glyph_renderer.data_source)
            
            time.sleep(1)

    def stop(self):
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
