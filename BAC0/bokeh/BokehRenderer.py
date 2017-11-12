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
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool, Range1d, LinearAxis, CategoricalColorMapper
from bokeh.models.widgets import DataTable, DateFormatter, NumberFormatter, TableColumn, Div
from bokeh.layouts import widgetbox, row, column, gridplot 
from bokeh.palettes import d3, Spectral6
from bokeh.models import Column
from bokeh.client import push_session
from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.application.handlers import Handler

import numpy as np


from collections import OrderedDict
import logging
import math
import weakref
import pandas as pd

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
        
#class BokehDocument(InstancesMixin):
#    def __init__(self, title = 'Live Trending'):
#        #self.document = Document(title = title)
#        self.layout = None
#        self.cb = (None, 0)
#        self.plots = []
#        self.widgets = [None,]
#        self._log = logging.getLogger("bokeh").setLevel(logging.INFO)
#        
#    def add_plot(self, new_plot_and_widget, linked_x_axis = True, infos = None):
#        #self.document.clear()
#        new_plot, widget = new_plot_and_widget
#        new_plot.x_range.bounds = None
#        new_plot.y_range.bounds = None
#        for key, plot in enumerate(self.plots):
#            if new_plot.title == plot.title:
#                self.plots.pop(key)
#                self.plots.append(new_plot)
#                break
#        else:
#            self.plots.append(new_plot)
#            if self.widgets:
#                pass
#            else:
#                # For now, let's deal with only one widget
#                self.widgets.append(widget)
#
#        
#        self.widgets[0] = widget
#
#        if linked_x_axis:
#            for plot in self.plots[1:]:
#                plot.x_range = self.plots[0].x_range
#                plot.x_range.bounds = None
#                plot.y_range.bounds = None

class DynamicPlotHandler(Handler):
    def __init__(self, network):
        self.network = network
        super().__init__()

    def build_plot(self):        
        self.df = pd.DataFrame()

        self.s = {}
        for point in self.network.points_to_trend:
            self.s[point.history.name] = (point.history, point.history.units)

        # Making a list to concatenate
        self.lst_of_trends = [his[0] for name, his in self.s.items()]         
        self.df = pd.concat(self.lst_of_trends, axis=1).reset_index()

        self.div_header_doc = Div(text ="""<div class="header">
                             <H1> BAC0 Trending Tools </H1></div>""")     
        self.div_header_notes = Div(text="""<div class="TableTitle"><H1> Notes from controller</H1></div>""")
        self.div_footer = Div(text="""<div class="footer"><p> <a href="http://www.servisys.com">Servisys inc.</a> | 
                         <a href="https://pythoninthebuilding.wordpress.com/">Python in the building</a></p></div>""")


        TOOLS = "pan,box_zoom,wheel_zoom,save,reset"
        self.p = Figure(x_axis_type="datetime", x_axis_label="Time", 
                        y_axis_label="Numeric Value", title = 'BAC0 Trends', 
                        tools = TOOLS, plot_width=700, plot_height=600,
                        toolbar_location = 'above')


        self.p.legend.location = 'top_left'
        self.p.extra_y_ranges = {"bool": Range1d(start=0, end=1.1),
                                 "enum": Range1d(start=0, end=10)}
        self.p.add_layout(LinearAxis(y_range_name="bool", axis_label="Binary"), 'left')
        self.p.add_layout(LinearAxis(y_range_name="enum", axis_label="Enumerated"), 'right')
        self.p.legend.location = "bottom_left"
                            
        hover = HoverTool(tooltips=[
            ('name', '@name'),
            ('value', '@y'),
            ('units', '@units'),
            ('time', '@time'),
        ])
        self.p.add_tools(hover)
        self.sources = {}
        
        length = len(self.s.keys())
        if length<=10:
            if length < 3:
                length = 3
            color_mapper = dict(zip(self.s.keys(), d3['Category10'][length]))
        else:
            # This would be a very loaded trend...
            color_mapper = dict(zip(self.s.keys(), Spectral6[:length]))
          

        for each in self.lst_of_trends:
            df = pd.DataFrame(each)
            df = df.reset_index()
            print(df)
            df['name'] = each.name
            df['units'] = each.units
            df['time_s'] = df['index'].apply(str)
            
        
        #            try:
        #                df['name'] = df['name'].replace('nameToReplace', ('%s / %s' % (each, self.device[each]['description'])))            
        #            except TypeError:
        #                continue
            self.sources[each.name] = ColumnDataSource(
                            data=dict(
                            x = df['index'],
                            y = df[each.name],
                            time = df['time_s'],
                            name = df['name'],
                            units = df['units']
                        )
                    )
            
            
            if each.states == 'binary':
                self.p.circle('x', 
                            'y',
                            source = self.sources[each.name],
                            name = each.name,
                            color=color_mapper[each.name],
                            legend=("%s | %s (OFF-ON)" % (each.name, each.description)),
                            y_range_name="bool",
                            size = 10)
            elif each.states == 'multistates':
                self.p.diamond('x', 
                            'y',
                            source = self.sources[each.name],
                            name = each.name,
                            color=color_mapper[each.name],
                            legend=("%s | %s (%s)" % (each.name, each.description, each.units)),
                            y_range_name="enum",
                            size = 20)            
            else:
                self.p.line('x',
                            'y',
                            source = self.sources[each.name],
                            name = each.name,
                            color=color_mapper[each.name],
                            legend=("%s | %s (%s)" % (each.name, each.description, each.units)),
                            line_width = 2)
#        if self.show_notes:        
#            columns = [
#                    TableColumn(field="x", title="Date", formatter=DateFormatter(format='yy-mm-dd')),
#                    TableColumn(field="units", title="Notes"),
#                ]        
#            data_table = DataTable(source=self.notes_source, columns=columns)    
#            return (self.p, data_table)
#        else:
#            return (self.p, None)
            self.plots = [self.p,]
    
        def update_data(self):
            if self.device.properties.network._started:           
                self.df = pd.concat(self.lst_of_trends, axis=1)
                df = self.df
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
    
    def modify_document(self, doc):
        self.build_plot()
        doc.clear()
        layout = column(widgetbox(self.div_header_doc), 
                gridplot(self.plots, ncols=2), 
                widgetbox(self.div_header_notes),
                #row(self.widgets),
                widgetbox(self.div_footer))
        doc.add_root(layout)
#        cb, delay = d.cb
#        if cb:
#            doc.add_periodic_callback(cb,delay)
        return doc

class DevicesTableHandler(Handler):
    """ 
    This handler will poll the network and show devices.

    """
    def __init__(self, network):
        self.network = network
        super().__init__()

    def modify_document(self, doc):
        self.network.whois()
        devices_df = self.network.devices
        dev = ColumnDataSource(devices_df)
        columns = [
            TableColumn(field=" Device ID", title="Dev ID"),
            TableColumn(field="Address", title="Address"),
            TableColumn(field="Manufacturer", title="Manuf"),
            TableColumn(field="Name", title="Name")]
        data_table = DataTable(source=dev, columns=columns)
        layout = row([data_table])
        doc.add_root(layout)
        doc.title = 'BACnet devices'
        return doc