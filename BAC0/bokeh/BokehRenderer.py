#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module deals with Bokeh Session, Document and Plots
A connection to the server is mandatory to use update_data
"""
import random
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool, Range1d, LinearAxis, CategoricalColorMapper
from bokeh.models.widgets import DataTable, DateFormatter, NumberFormatter, TableColumn, Div
from bokeh.layouts import widgetbox, row, column, gridplot 
from bokeh.palettes import d3, Spectral6
from bokeh.models import Column
from bokeh.client import push_session
from bokeh.document import Document
from bokeh.io import curdoc

import numpy as np


from collections import OrderedDict
import logging
import math
import weakref

from .BokehLoopUntilClosed import BokehLoopUntilClosed

class InstancesMixin(object):
    _instances = set()
    
    def checkInstances(self, cls):
        for obj in cls.getinstances():
            if obj.title == self.title:
                del obj
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
        self.document = Document(title = title)
        self.plots = []
        self.widgets = [None,]
        self._log = logging.getLogger("bokeh").setLevel(logging.INFO)
        
    def add_plot(self, new_plot_and_widget, linked_x_axis = True, infos = None):
        self.document.clear()
        new_plot, widget = new_plot_and_widget
        new_plot.x_range.bounds = None
        new_plot.y_range.bounds = None
        for key, plot in enumerate(self.plots):
            if new_plot.title == plot.title:
                self.plots.pop(key)
                self.plots.append(new_plot)
                break
        else:
            self.plots.append(new_plot)
            if self.widgets:
                pass
            else:
                # For now, let's deal with only one widget
                self.widgets.append(widget)

        
        self.widgets[0] = widget

        if linked_x_axis:
            for plot in self.plots[1:]:
                plot.x_range = self.plots[0].x_range
                plot.x_range.bounds = None
                plot.y_range.bounds = None
        
        div_header_doc = Div(text ="""<div class="header">
                             <H1> BAC0 Trending Tools </H1>
                             <h2>For %s (Address : %s | Device ID : %s)</h2></div>""" % (infos.name, infos.address, infos.device_id))        
        div_header_notes = Div(text="""<div class="TableTitle"><H1> Notes from controller</H1></div>""")
        div_footer = Div(text="""<div class="footer"><p> <a href="http://www.servisys.com">Servisys inc.</a> | 
                         <a href="https://pythoninthebuilding.wordpress.com/">Python in the building</a></p></div>""")

        layout = column(widgetbox(div_header_doc), 
                        gridplot(self.plots, ncols=2), 
                        widgetbox(div_header_notes),
                        row(self.widgets),
                        widgetbox(div_footer))
        self.document.add_root(layout)
        #curdoc().add_root(layout)
        
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
        print('Click here to open Live Trending Web Page')
        print('http://localhost:5006/?bokeh-session-id=%s' % self.session_id)
    
    def loop(self):
        if BokehSession._loop == None:
                BokehSession._loop = BokehLoopUntilClosed(BokehSession._session)
        try:
            BokehSession._loop.start() 
        except RuntimeError:
            # probably started
            pass

class BokehPlot(object):
    def __init__(self, device, points_list, *, title = 'My title', show_notes = True, update_data = True):
        self.device = device
        if len(points_list) < 3:
            raise ValueError("Provide at least 3 objects to the chart")
        self.points_list = points_list
        self.title = title
        self.units = {}
        self.show_notes = show_notes

        self.lst = self.points_list

        self.multi_states = self.device.multi_states
        self.binary_states = self.device.binary_states
        self.analog_units = self.device.analog_units

        plot = self.build_plot()

        self.device.properties.network.bokeh_document.add_plot(plot, infos=self.device.properties)
        #curdoc().add_root(plot)
        if update_data:
            self.device.properties.network.bokeh_document.add_periodic_callback(self.update_data, 100)   
        print('Chart created, please reload your web page to see changes')
        
     # Get data
    def read_lst(self):
        df = self.device[self.lst]
        try:
            df = df.fillna(method='ffill').fillna(method='bfill').replace(['inactive', 'active'], [0, 1])
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

        TOOLS = "pan,box_zoom,wheel_zoom,resize,save,reset"
        self.p = Figure(x_axis_type="datetime", x_axis_label="Time", 
                        y_axis_label="Numeric Value", title = self.title, 
                        tools = TOOLS, plot_width=700, plot_height=600,
                        toolbar_location = 'above')

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
                            #color = "#%06x" % random.randint(0x000000, 0x777777), 
                            legend='Notes',
                            size = 40) 

        self.p.legend.location = 'top_left'
        self.p.extra_y_ranges = {"bool": Range1d(start=0, end=1.1),
                                 "enum": Range1d(start=0, end=10)}
        self.p.add_layout(LinearAxis(y_range_name="bool", axis_label="Binary"), 'left')
        self.p.add_layout(LinearAxis(y_range_name="enum", axis_label="Enumerated"), 'right')
        self.p.legend.location = "bottom_left"
                            
        hover = HoverTool(tooltips=[
            ('name', '@desc'),
            ('value', '@y'),
            ('units', '@units'),
            ('time', '@time'),
        ])
        self.p.add_tools(hover)

        self.sources = {}
        if len(self.lst)<=10:
            color_mapper = dict(zip(self.lst, d3['Category10'][len(self.lst)]))
        else:
            # This would be a very loaded trend...
            color_mapper = dict(zip(self.lst, Spectral6[:len(self.lst)]))
            
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
                            color=color_mapper[each],
                            legend=("%s/%s (OFF-ON)" % (each, self.device[each]['description'])),
                            y_range_name="bool",
                            size = 10)
            elif each in self.multi_states:
                self.p.diamond('x', 
                            'y',
                            source = self.sources[each],
                            name = each,
                            color=color_mapper[each],
                            legend=("%s/%s (%s)" % (each, self.device[each]['description'], self.device[each].properties.units_state)),
                            y_range_name="enum",
                            size = 20)            
            else:
                self.p.line('x',
                            'y',
                            source = self.sources[each],
                            name = each,
                            color=color_mapper[each],
                            legend=("%s/%s (%s)" % (each, self.device[each]['description'], self.device[each].properties.units_state)),
                            line_width = 2)
        if self.show_notes:        
            columns = [
                    TableColumn(field="x", title="Date", formatter=DateFormatter(format='yy-mm-dd')),
                    TableColumn(field="units", title="Notes"),
                ]        
            data_table = DataTable(source=self.notes_source, columns=columns)    
            return (self.p, data_table)
        else:
            return (self.p, None)
    
    def update_data(self):
        if self.device.properties.network._started:           
            df = self.read_lst()
            for renderer in self.p.renderers:
                name = renderer.name
                glyph_renderer = renderer
                new_data = {}
                if name in self.points_list:     
                    df['name'] = ('%s / %s' % (name, self.device[name]['description']))
                    new_data['x'] = df['index']
                    new_data['y'] = df[name]
                    new_data['desc'] = df['name']
                    new_data['time'] = df['time_s']
                    if name in self.multi_states:
                        new_data['units'] = [self.multi_states[name][int(math.fabs(x-1))] for x in df[name]]
                    elif name in self.binary_states:
                        new_data['y'] = df[name]
                        new_data['units'] = [self.binary_states[name][int(x/1)] for x in df[name]]
                    else:
                        df['units'] = self.analog_units[name]
                        new_data['units'] = df['units']
                    glyph_renderer.data_source.data = new_data
                elif name == 'Notes':
                    notes_df = self.read_notes()
                    new_data['x'] = notes_df['index']
                    new_data['y'] = notes_df['value']
                    new_data['desc'] = notes_df['desc']
                    new_data['units'] = notes_df[0]
                    new_data['time'] = notes_df['time_s']
                    glyph_renderer.data_source.data = new_data
