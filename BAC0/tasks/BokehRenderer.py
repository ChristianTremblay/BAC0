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
import time
import random
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import VBox, HBox, Slider, TextInput, VBoxForm
from bokeh.client import push_session, pull_session
from bokeh.driving import repeat
from bokeh.document import Document

from collections import OrderedDict
import logging
import math
import weakref

from .BokehLoopUntilClosed import BokehLoopUntilClosed

class BokehSession(object):
    

class BokehRenderer(object):
    
    _instances = set()

    def __init__(self, device, points_list, *, title = 'My title'):
        self.device = device
        self.points_list = points_list
        self.title = title
        self.units = {}
        
        for obj in BokehRenderer.getinstances():
            if obj.title == self.title:
                obj.stop()
                del obj        
        #clean instances
        list(self.getinstances())

        self._instances.add(weakref.ref(self)) 
        

        logging.getLogger("requests").setLevel(logging.INFO)
        logging.getLogger("bokeh").setLevel(logging.INFO)

        self.lst = self.points_list

        self.multi_states = self.device.multi_states
        self.binary_states = self.device.binary_states
        self.analog_units = self.device.analog_units
        self.document = Document(title = 'BAC0 - Live trending')
        self.document.clear()
        print('Building')
        plot = self.build_plot()
        layout = VBox(plot)
        
        self.session = push_session(self.document)
        self.document.add_root(layout)
        self.document.add_periodic_callback(self.update_data, 100)   
        self.session_id = self.session.id
        print('http://localhost:5006/?bokeh-session-id=%s' % self.session_id)
        loop = BokehLoopUntilClosed(self.session)
        loop.start()

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
        # Get data
    def read_lst(self):
        print('Reading list')
        df = self.device[self.lst]
        try:
            df = df.fillna(method='ffill').fillna(method='bfill').replace(['inactive', 'active'], [0, 50])
        except TypeError:
            df = df.fillna(method='ffill').fillna(method='bfill')
                                      
        df = df.reset_index()
        df['name'] = 'nameToReplace'
        df['units'] = 'waiting for refresh'
        df['time_s'] = df['index'].apply(str)
        return df

    def read_notes(self):
        print('Reading notes')
        notes_df = self.device.notes.reset_index()
        notes_df['value'] = 100
        notes_df['desc'] = 'Notes'
        notes_df['time_s'] = notes_df['index'].apply(str)
        return notes_df

    def build_plot(self):        
        df = self.read_lst()
        notes_df = self.read_notes()

        TOOLS = "hover,resize,save,pan,box_zoom,wheel_zoom,reset"
        
        # Generate a figure container for notes
        self.p = Figure(plot_width=800, plot_height=600, x_axis_type="datetime", title = self.title, tools = TOOLS)

        self.notes_source = ColumnDataSource(
                    data=dict(
                        x = notes_df['index'],
                        y = notes_df['value'],
                        time = notes_df['time_s'],
                        desc = notes_df['desc'],
                        units = notes_df[0]
                    )
                )
                

        self.p.asterisk('x', 
                        'y',
                        source = self.notes_source,
                        name = 'Notes',
                        color = "#%06x" % random.randint(0x000000, 0x777777), 
                        legend='Notes',
                        size = 40) 

        # plot = plot ?
#        self.p = self.p
        self.p.legend.location = 'top_left'
        hover = self.p.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ('name', '@desc'),
            ('value', '@y'),
            ('units', '@units'),
            ('time', '@time'),
        ])
        
        # Build a plot for each point in list
        self.sources = {}               
        for each in self.lst:
            
            try:
                df['name'] = df['name'].replace('nameToReplace', ('%s / %s' % (each, self.device[each]['description'])))            
            except TypeError:
                continue
            self.sources[each] = ColumnDataSource(
                            data=dict(
                            x = df['index'],
                            y = df[each],
                            time = df['time_s'],
                            name = df['name'],
                            units = df['units']
                        )
                    )

            if each in self.binary_states:
                
                self.p.circle('x', 
                            'y',
                            source = self.sources[each],
                            name = each,
                            color = "#%06x" % random.randint(0x000000, 0x777777),
                            legend=each,
                            size = 10)
            elif each in self.multi_states:
                self.p.diamond('x', 
                            'y',
                            source = self.sources[each],
                            name = each,
                            color = "#%06x" % random.randint(0x000000, 0x777777), 
                            legend=each,
                            size = 20)            
            else:
                self.p.line('x',
                            'y',
                            source = self.sources[each],
                            name = each,
                            color = "#%06x" % random.randint(0x000000, 0x777777),
                            legend=each,
                            line_width = 2)
            
        return self.p

    def update_data(self):
        print('Running update')
        df = self.read_lst()
        for renderer in self.p.renderers:
            name = renderer.name
            if name in self.points_list:
                glyph_renderer = renderer
                df['name'] = ('%s / %s' % (name, self.device[name]['description']))
                glyph_renderer.data_source.data['x'] = df['index']
                glyph_renderer.data_source.data['y'] = df[name]
                glyph_renderer.data_source.data['desc'] = df['name']
                glyph_renderer.data_source.data['time'] = df['time_s']
                if name in self.multi_states:
                    glyph_renderer.data_source.data['units'] = [self.multi_states[name][int(math.fabs(x-1))] for x in df[name]]
                elif name in self.binary_states:
                    glyph_renderer.data_source.data['y'] = df[name]
                    glyph_renderer.data_source.data['units'] = [self.binary_states[name][int(x/50)] for x in df[name]]
                else:
                    df['units'] = self.analog_units[name]
                    glyph_renderer.data_source.data['units'] = df['units']
            elif name == 'Notes':
                notes_df = self.read_notes()
                glyph_renderer = renderer
                glyph_renderer.data_source.data['x'] = notes_df['index']
                glyph_renderer.data_source.data['y'] = notes_df['value']
                glyph_renderer.data_source.data['desc'] = notes_df['desc']
                glyph_renderer.data_source.data['units'] = notes_df[0]
                glyph_renderer.data_source.data['time'] = notes_df['time_s']

#        df = self.read_lst() 
#        notes_df = self.read_notes()
#        
#        for key, value in self.sources.items():            
#            try:
#                df['name'] = df['name'].replace('nameToReplace', ('%s / %s' % (key, self.device[key]['description'])))            
#            except TypeError:
#                continue
#            self.sources[key].data = ColumnDataSource(
#                            data=dict(
#                            x = df['index'],
#                            y = df[key],
#                            time = df['time_s'],
#                            desc = df['name'],
#                            units = df['units']
#                        )
#                    )       
#        self.notes_source.data = ColumnDataSource(
#                        data=dict(
#                        x = notes_df['index'],
#                        y = notes_df[key],
#                        time = notes_df['time_s'],
#                        desc = notes_df['name'],
#                        units = notes_df['units']
#                    )
#                )



#    def choose_y_axis(self, point_name):
#        """
#        Could be use to select the y axis... not working yet...
#        """
#        if point_name in list(self.device.temperatures):
#            return 'temperature'
#        elif point_name in list(self.device.percent):
#            return 'percent'
#        else:
#            return None

#    def stop(self):
#        self.exitFlag = True

#    def beforeStop(self):
#        """
#        Action done when closing thread
#        """
#        pass
