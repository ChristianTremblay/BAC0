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
from bokeh.plotting import figure, output_server, cursession, show, ColumnDataSource, curdoc
from bokeh.models import HoverTool
from bokeh.io import gridplot, vplot
from bokeh.embed import autoload_server
from bokeh.session import Session
from bokeh.document import Document
#from bokeh.client import push_session

from collections import OrderedDict
import logging
import math
import weakref

class BokehRenderer(Thread):
    #figures = {}
    _instances = set()

    def __init__(self, device, points_list, *, title = 'My title', daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.exitFlag = False
        self.device = device
        self.points_list = points_list
        self.title = title
        self.units = {}
        logging.getLogger("requests").setLevel(logging.INFO)
        logging.getLogger("bokeh").setLevel(logging.INFO)
        
        for obj in BokehRenderer.getinstances():
            if obj.title == title:
                print('Chart already exist, stopping thread and deleting it')
                obj.stop()
                del obj
        #clean instances
        list(self.getinstances())

        TOOLS = "resize,hover,save,pan,box_zoom,wheel_zoom,reset"
        self.p = figure(plot_width=500, plot_height=450, x_axis_type="datetime", title = self.title, tools = TOOLS)
        #BokehRenderer.figures[title] = self.p
        #BokehRenderer.render_threads[title] = self
        self._instances.add(weakref.ref(self)) 
 
        output_server('Commissionning %s' % (self.device.properties.name))
                    
        cursession().publish()
        
    @classmethod
    def getinstances(cls):
        dead = set()
        for ref in cls._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        cls._instances -= dead
        
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
            df['units'] = 'waiting for refresh'
            return df

        def read_notes():
            notes_df = self.device.notes.reset_index()
            notes_df['value'] = 100
            notes_df['desc'] = 'Notes'
            return notes_df
        
        df = read_lst()
        notes_df = read_notes()

       

        notes_source = ColumnDataSource(
                    data=dict(
                        x = notes_df['index'],
                        y = notes_df['value'],
                        desc = notes_df['desc'],
                        units = notes_df[0]
                    )
                )
        self.p.asterisk('x', 
                        'y',
                        source = notes_source,
                        name = 'Notes',
                        color = "#%06x" % random.randint(0x000000, 0x777777), 
                        legend='Notes',
                        size = 40) 

        for each in lst:
            try:
                df['name'] = df['name'].replace('nameToReplace', ('%s / %s' % (each, self.device[each]['description'])))            
            except TypeError:
                continue
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
        self.p.legend.orientation = 'top_left'
        hover = self.p.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ('name', '@desc'),
            ('value', '@y'),
            ('units', '@units'),
        ])
        self.make_grid()
        
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
                    elif name in binary_states:
                        glyph_renderer.data_source.data['y'] = df[name]
                        glyph_renderer.data_source.data['units'] = [binary_states[name][int(x/50)] for x in df[name]]
                    else:
                        df['units'] = analog_units[name]
                        glyph_renderer.data_source.data['units'] = df['units']
                    cursession().store_objects(glyph_renderer.data_source)
                elif name == 'Notes':
                    notes_df = read_notes()
                    glyph_renderer = renderer
                    glyph_renderer.data_source.data['x'] = notes_df['index']
                    glyph_renderer.data_source.data['y'] = notes_df['value']
                    glyph_renderer.data_source.data['desc'] = notes_df['desc']
                    glyph_renderer.data_source.data['units'] = notes_df[0]
                    cursession().store_objects(glyph_renderer.data_source)
            
            time.sleep(1)
    
    @classmethod        
    def make_grid(cls):

        figs = []        
        for obj in BokehRenderer.getinstances():
            figs.append(obj.p)
       
        if len(figs) > 1:
            number_of_rows = int(round(len(figs) / 2))
            rows = []
            number_of_columns = 2
            i = 0
            for each in range(number_of_rows):
                rows.append(list(fig for fig in figs[i:i+number_of_columns]))
                i += number_of_columns
            layout = gridplot(rows)

        else:
            layout = vplot(figs[0])

        cursession().publish()        
        show(layout)


    def stop(self):
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
