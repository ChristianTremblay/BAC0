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
from bokeh.models import ColumnDataSource, HoverTool, Range1d, LinearAxis
from bokeh.models.widgets import DataTable, TableColumn, Div
from bokeh.layouts import widgetbox, row, column, gridplot 
from bokeh.palettes import d3, Spectral6
from bokeh.io import curdoc
from bokeh.application.handlers import Handler

import logging
import math
import pandas as pd
import weakref

class DynamicPlotHandler(Handler):
    def __init__(self, network):
        self._network = weakref.ref(network)
        self.sources = {}
        self._last_time_list = None
        super().__init__()
    
    @property
    def network(self):
        return self._network()
        
    def organize_data(self):
        self.s = {}
        for point in self.network.points_to_trend:
            self.s[point.history.name] = (point.history, point.history.units)
        self.lst_of_trends = [his[0] for name, his in self.s.items()]  
       
    def build_plot(self):     
        self.organize_data()
        for each in self.lst_of_trends:
            df = pd.DataFrame(each)
            df = df.reset_index()
            #print(df)
            df['name'] = each.name
            df['units'] = str(each.units)
            df['time_s'] = df['index'].apply(str)
            df.states = each.states
            try:
                df = df.fillna(method='ffill').fillna(method='bfill').replace(['inactive', 'active'], [0, 1])
            except TypeError:
                df = df.fillna(method='ffill').fillna(method='bfill')
            
            self.sources[each.name] = ColumnDataSource(
                            data=dict(
                            x = df['index'],
                            y = df[each.name],
                            time = df['time_s'],
                            name = df['name'],
                            units = df['units']
                        )
                            )
#        self.div_header_doc = Div(text ="""<div class="header">
#                             <H1> BAC0 Trending Tools </H1></div>""")     
#        #self.div_header_notes = Div(text="""<div class="TableTitle"><H1> Notes from controller</H1></div>""")
#        self.div_footer = Div(text="""<div class="footer"><p> <a href="http://www.servisys.com">Servisys inc.</a> | 
#                         <a href="https://pythoninthebuilding.wordpress.com/">Python in the building</a></p></div>""")

        TOOLS = "pan,box_zoom,wheel_zoom,save,reset"
        self.p = Figure(x_axis_type="datetime", x_axis_label="Time", 
                        y_axis_label="Numeric Value", title = 'BAC0 Trends', 
                        tools = TOOLS, plot_width=1300, plot_height=600,
                        toolbar_location = 'above')

        self.p.background_fill_color = "#f4f3ef"
        self.p.border_fill_color = "#f4f3ef"
        self.p.extra_y_ranges = {"bool": Range1d(start=0, end=1.1),
                                 "enum": Range1d(start=0, end=10)}
        self.p.add_layout(LinearAxis(y_range_name="bool", axis_label="Binary"), 'left')
        self.p.add_layout(LinearAxis(y_range_name="enum", axis_label="Enumerated"), 'right')
                            
        hover = HoverTool(tooltips=[
            ('name', '@name'),
            ('value', '@y'),
            ('units', '@units'),
            ('time', '@time'),
        ])
        self.p.add_tools(hover)
        
        length = len(self.s.keys())
        if length<=10:
            if length < 3:
                length = 3
            color_mapper = dict(zip(self.s.keys(), d3['Category10'][length]))
        else:
            # This would be a very loaded trend...
            color_mapper = dict(zip(self.s.keys(), Spectral6[:length]))
          

        for each in self.lst_of_trends:
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
                
            self.p.legend.location = 'bottom_left'
            self.p.legend.click_policy = "hide"

            self.plots = [self.p,]
    
    def update_data(self):
        self.organize_data()
        if self._last_time_list:
            if self._last_time_list != self.s.keys():
                self._list_have_changed = True
                curdoc().remove_periodic_callback(self.update_data)
                self.modify_document(curdoc())
            else:
                self._list_have_changed = False
        
        l = []
        for each in self.p.renderers:
            l.append(each.name)
        
        for each in self.lst_of_trends:
            df = pd.DataFrame(each)
            df = df.reset_index()
            df['name'] = each.name
            df['units'] = str(each.units)
            df['time_s'] = df['index'].apply(str)
            
            try:
                df = df.fillna(method='ffill').fillna(method='bfill').replace(['inactive', 'active'], [0, 1])
            except TypeError:
                df = df.fillna(method='ffill').fillna(method='bfill')
            
            index = l.index(each.name)
            renderer = self.p.renderers[index]
            new_data = {}
            new_data['name'] = df['name']
            new_data['x'] = df['index']
            new_data['y'] = df[each.name]
            if each.states == 'binary':
                new_data['units'] = [each.units[int(x)] for x in df[each.name]]
            elif each.states == 'multistates':
                new_data['units'] = [each.units[int(math.fabs(x-1))] for x in df[each.name]]
            else:
                new_data['units'] = df['units']
            new_data['time'] = df['time_s']
            renderer.data_source.data = new_data
        self._last_time_list = self.s.keys()
            
    def modify_document(self, doc):
        curdoc().clear()
        try:
            curdoc().remove_periodic_callback(self.update_data)
        except:
            pass
        doc.clear()
        self.build_plot()
        #column(widgetbox(self.div_header_doc), 
        layout = gridplot(self.plots, ncols=2)
                #widgetbox(self.div_header_notes),
                #widgetbox(self.div_footer)
                
        doc.add_root(layout)
        doc.add_periodic_callback(self.update_data,100)          
        return doc

class DevicesTableHandler(Handler):
    """ 
    This handler will poll the network and show devices.

    """
    def __init__(self, network):
        self._network = weakref.ref(network)
        super().__init__()
        
    @property
    def network(self):
        return self._network()

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

class NetworkPieChartHandler(Handler):
    """ 
    This handler will poll the network and show devices.

    """
    def __init__(self, network):
        self._network = weakref.ref(network)
        super().__init__()

    @property
    def network(self):
        return self._network()
    
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

class NotesTableHandler(Handler):
    """ 
    This handler will poll the network and show devices.

    """
    def __init__(self, network):
        self._network_ref = weakref.ref(network)
        super().__init__()

    @property
    def network(self):
        return self._network_ref()

    def modify_document(self, doc):
        controller = self.network.notes[0]
        notes_df = pd.DataFrame(self.network.notes[1]).reset_index()
        notes_df.columns = ['index', 'notes']
        notes = ColumnDataSource(notes_df)
        self.columns = [
            TableColumn(field="index", title="Timestamp"),
            TableColumn(field="notes", title="Notes")]
        self.data_table = DataTable(source=notes, columns=self.columns)
        layout = row([self.data_table])
        doc.add_root(layout)
        doc.title = 'Notes for %s' % controller
        #doc.add_periodic_callback(self.update_data,100)  
        return doc
    
    def update_data(self):
        controller = self.network.notes[0]
        notes_df = pd.DataFrame(self.network.notes[1]).reset_index()
        notes_df.columns = ['index', 'notes']
        notes = ColumnDataSource(notes_df)
        self.data_table.source.data.update(notes.data)
        curdoc().title = 'Notes for %s' % controller