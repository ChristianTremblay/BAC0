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

from tornado import gen

import math
import pandas as pd
import weakref

from ..tasks.RecurringTask import RecurringTask
from ..core.utils.notes import note_and_log


@note_and_log
class DynamicPlotHandler(Handler):
    def __init__(self, network):
        self._network = weakref.ref(network)
        self.sources = {}
        self._last_time_list = None
        self._update_complete = False
        self._recurring_update = RecurringTask(self.plan_update_data, delay=5)
        self._pcb = None #Periodic callback
        self._ntcb = None #Next Tick callback
        super().__init__()

    @property
    def network(self):
        return self._network()

    def organize_data(self):

        self._log.debug('Organize Data')

        self.s = {}
        for point in self.network.trends:
            self.s[point.history.name] = (point.history, point.history.units)
        self.lst_of_trends = [his[0] for name, his in self.s.items()]

    def build_data_sources(self):
        sources = {}
        self.organize_data()
        for each in self.lst_of_trends:
            df = pd.DataFrame(each)
            df = df.reset_index()
            df['name'] = each.name
            df['units'] = str(each.units)
            df['time_s'] = df['index'].apply(str)
            df.states = each.states
            try:
                df = df.fillna(method='ffill').fillna(
                    method='bfill').replace(['inactive', 'active'], [0, 1])
            except TypeError:
                df = df.fillna(method='ffill').fillna(method='bfill')

            sources[each.name] = ColumnDataSource(
                data=dict(
                    x=df['index'],
                    y=df[each.name],
                    time=df['time_s'],
                    name=df['name'],
                    units=df['units']
                )
            )
        return sources

    def build_plot(self):
        self._log.debug('Build Plot')

        self.stop_update_data()
        self.sources = self.build_data_sources()


        TOOLS = "pan,box_zoom,wheel_zoom,save,reset"
        self.p = Figure(x_axis_type="datetime", x_axis_label="Time",
                        y_axis_label="Numeric Value", title='BAC0 Trends',
                        tools=TOOLS, plot_width=800, plot_height=600,
                        toolbar_location='above')

        self.p.background_fill_color = "#f4f3ef"
        self.p.border_fill_color = "#f4f3ef"
        self.p.extra_y_ranges = {"bool": Range1d(start=0, end=1.1),
                                 "enum": Range1d(start=0, end=10)}
        self.p.add_layout(LinearAxis(y_range_name="bool",
                                     axis_label="Binary"), 'left')
        self.p.add_layout(LinearAxis(y_range_name="enum",
                                     axis_label="Enumerated"), 'right')

        hover = HoverTool(tooltips=[
            ('name', '@name'),
            ('value', '@y'),
            ('units', '@units'),
            ('time', '@time'),
        ])
        self.p.add_tools(hover)

        length = len(self.s.keys())
        if length <= 10:
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
                              source=self.sources[each.name],
                              name=each.name,
                              color=color_mapper[each.name],
                              legend=("%s | %s (OFF-ON)" %
                                      (each.name, each.description)),
                              y_range_name="bool",
                              size=10)
            elif each.states == 'multistates':
                self.p.diamond('x',
                               'y',
                               source=self.sources[each.name],
                               name=each.name,
                               color=color_mapper[each.name],
                               legend=("%s | %s (%s)" %
                                       (each.name, each.description, each.units)),
                               y_range_name="enum",
                               size=20)
            else:
                self.p.line('x',
                            'y',
                            source=self.sources[each.name],
                            name=each.name,
                            color=color_mapper[each.name],
                            legend=("%s | %s (%s)" %
                                    (each.name, each.description, each.units)),
                            line_width=2)

            self.p.legend.location = 'bottom_right'
            self.p.legend.click_policy = "hide"

            self.plots = [self.p, ]

    def update_data(self):
        self._log.debug('Update Data')
        doc = curdoc()
        #self.organize_data()
        if self._last_time_list:
            if self._last_time_list != self.s.keys():
                self._list_have_changed = True
                self.stop_update_data()
                #doc.add_next_tick_callback(self.modify_document)
                self.modify_document(doc)
            else:
                self._list_have_changed = False

        l = []
        for each in self.p.renderers:
            l.append(each.name)

        #for each in self.lst_of_trends:
        #    df = pd.DataFrame(each)
        #    df = df.reset_index()
        #    df['name'] = each.name
        #    df['units'] = str(each.units)
        #    df['time_s'] = df['index'].apply(str)

        #    try:
        #        df = df.fillna(method='ffill').fillna(
        #            method='bfill').replace(['inactive', 'active'], [0, 1])
        #    except TypeError:
        #        df = df.fillna(method='ffill').fillna(method='bfill')

            index = l.index(each.name)
        #    renderer = self.p.renderers[index]
        #    new_data = {}
        #    new_data['name'] = df['name']
        #    new_data['x'] = df['index']
        #    new_data['y'] = df[each.name]
        #    if each.states == 'binary':
        #        new_data['units'] = [each.units[int(x)] for x in df[each.name]]
        #    elif each.states == 'multistates':
        #        new_data['units'] = [
        #            each.units[int(math.fabs(x-1))] for x in df[each.name]]
        #    else:
        #        new_data['units'] = df['units']
        #    new_data['time'] = df['time_s']
        #    renderer.data_source.data = new_data
        try:
            new_data = self.build_data_sources()
            for each in self.lst_of_trends:
                self.sources[each.name].data = new_data[each.name].data
        
        except KeyError:
            self._log.warning('Problem updating {} on chart, will try again next time.'.format(each.name))

        else:
            self._last_time_list = self.s.keys()
            # self.start_update_data()
            self._update_complete = True


    def modify_document(self, doc):
        curdoc().clear()
        #doc = curdoc()
        try:
            curdoc().remove_periodic_callback(self._pcb)
        except:
            pass
        doc.clear()
        self.build_plot()
        layout = gridplot(self.plots, ncols=2)

        doc.add_root(layout)
        self._pcb = doc.add_periodic_callback(self.update_data, 10000)
        return doc

    def plan_update_data(self):
        doc = curdoc()
        if self._update_complete == True:
            self._update_complete = False
            self._ntcb = doc.add_next_tick_callback(self.update_data)

    def stop_update_data(self):
        doc = curdoc()
        if self._recurring_update.is_running:
            self._recurring_update.stop()
            while self._recurring_update.is_running:
                pass
            try:
                doc.remove_next_tick_callback(self._ntcb)
            except (ValueError, RuntimeError):
                pass  # Already gone

    def start_update_data(self):
        if not self._recurring_update.is_running:
            try:
                self._recurring_update.start()
                while not self._recurring_update.is_running:
                    pass
            except RuntimeError:
                pass


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
        # doc.add_periodic_callback(self.update_data,100)
        return doc

    def update_data(self):
        controller = self.network.notes[0]
        notes_df = pd.DataFrame(self.network.notes[1]).reset_index()
        notes_df.columns = ['index', 'notes']
        notes = ColumnDataSource(notes_df)
        self.data_table.source.data.update(notes.data)
        curdoc().title = 'Notes for %s' % controller
