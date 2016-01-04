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
from bokeh.charts.glyphs import StepGlyph
from bokeh.models import ColumnDataSource, HoverTool, CustomJS
from bokeh.models.widgets import VBox, HBox, Slider, TextInput, VBoxForm
from bokeh.client import push_session, pull_session
from bokeh.driving import repeat
from bokeh.document import Document
from bokeh.io import gridplot, vplot

from collections import OrderedDict, namedtuple
import logging
import math
import weakref
import uuid
from itertools import zip_longest

from .BokehLoopUntilClosed import BokehLoopUntilClosed

class InstancesMixin(object):
    _instances = set()
    
    def checkInstances(self, cls):
        for obj in cls.getinstances():
            if obj.title == self.title:
                del obj        
        #clean instances
        list(self.getinstances())

        self._instances.add(weakref.ref(self)) 
        
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
        
class BokehDocument(InstancesMixin):
    def __init__(self, title = 'Live Trending'):
        self.document = Document(title = 'BAC0 - Live trending')
        self.plots = []
        
    def add_plot(self, new_plot, linked_x_axis = True):
        self.document.clear()
        for key, plot in enumerate(self.plots):
            if new_plot.title == plot.title:
                self.plots.pop(key)
                self.plots.append(new_plot)
                break
        else:
            self.plots.append(new_plot)
        if linked_x_axis:
            for plot in self.plots[1:]:
                plot.x_range = self.plots[0].x_range
                
#        yrange_callback = CustomJS(args=dict(source=source), code="""
#            var data = source.get('data');
#            var start = cb_obj.get('frame').get('y_range').get('start');
#            var end = cb_obj.get('frame').get('y_range').get('end');
#            data['y'] = [start + (end - start) / 2];
#            data['height'] = [end - start];
#            source.trigger('change');
#        """)
#        self.p.y_range.callback = yrange_callback  
#        for plot in self.plots
        #
#        def grouper(iterable, n, fillvalue=None):
#            "Collect data into fixed-length chunks or blocks"
#            # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
#            args = [iter(iterable)] * n
#            return zip_longest(*args, fillvalue=fillvalue)
#        
#        rows = [] 
#        [rows.append(HBox(x)) for x in grouper(self.plots, 2)]
        if len(self.plots) > 1:
            number_of_rows = int(round(len(self.plots) / 2))
            rows = []
            number_of_columns = 2
            i = 0
            for each in range(number_of_rows):
                rows.append(list(plot for plot in self.plots[i:i+number_of_columns]))
                i += number_of_columns
            layout = gridplot(rows)
        else:
           layout = VBox(self.plots)            
#        layout = VBox(self.plots)
        self.document.add_root(layout)
        
    def add_periodic_callback(self, cb, update = 100):
        self.document.add_periodic_callback(cb,update)

class BokehSession(object):
    _session = None
    _loop = None
    def __init__(self, document):
        if BokehSession._session == None:
            BokehSession._session = push_session(document)
        else:
            pass
        self.session_id = BokehSession._session.id
        print('http://localhost:5006/?bokeh-session-id=%s' % self.session_id)
    
    def loop(self):
        if BokehSession._loop == None:
            BokehSession._loop = BokehLoopUntilClosed(BokehSession._session)
            BokehSession._loop.start() 
        else:
            BokehSession._loop.stop()
            BokehSession._loop = BokehLoopUntilClosed(BokehSession._session)
            BokehSession._loop.start()

class BokehPlot(object):
    def __init__(self, device, points_list, *, title = 'My title', show_notes = True):
        self.device = device
        self.points_list = points_list
        self.title = title
        self.units = {}
        self.show_notes = show_notes

        #self.checkInstances(BokehPlot)
        
        logging.getLogger("requests").setLevel(logging.INFO)
        logging.getLogger("bokeh").setLevel(logging.INFO)

        self.lst = self.points_list

        self.multi_states = self.device.multi_states
        self.binary_states = self.device.binary_states
        self.analog_units = self.device.analog_units

        print('Building')
        plot = self.build_plot()

        self.device.properties.network.bokeh_document.add_plot(plot)
        self.device.properties.network.bokeh_document.add_periodic_callback(self.update_data, 100)   
        
     # Get data
    def read_lst(self):
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
        notes_df = self.device.notes.reset_index()
        notes_df['value'] = -5
        notes_df['desc'] = 'Notes'
        notes_df['time_s'] = notes_df['index'].apply(str)
        return notes_df

    def build_plot(self):        
        df = self.read_lst()
        notes_df = self.read_notes()

        TOOLS = "hover,resize,save,pan,box_zoom,wheel_zoom,reset"
        #plot_width=800, plot_height=600,
        self.p = Figure(x_axis_type="datetime", title = self.title, tools = TOOLS)

        if self.show_notes:
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
                #step = StepGlyph('x', 
                #            'y',
                #            source = self.sources[each],
                #            name = each,
                #            color = "#%06x" % random.randint(0x000000, 0x777777),
                #            legend=each,
                #            width = 4)               
                #self.p.add_glyph(step)
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
