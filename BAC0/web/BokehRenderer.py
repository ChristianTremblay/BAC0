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
from bokeh.models import ColumnDataSource, HoverTool, Range1d, LinearAxis, Legend
from bokeh.models.widgets import DataTable, TableColumn, Div
from bokeh.layouts import widgetbox, row, column, gridplot
from bokeh.palettes import d3, viridis
from bokeh.io import curdoc
from bokeh.application.handlers import Handler
from functools import partial

from tornado import gen

import math
import pandas as pd
import weakref
from queue import Queue

from ..tasks.RecurringTask import RecurringTask
from ..core.utils.notes import note_and_log


@note_and_log
class DynamicPlotHandler(Handler):

    analog_queue = Queue()
    binary_queue = Queue()
    multistates_queue = Queue()

    def __init__(self, network):
        super().__init__()
        self._network = weakref.ref(network)

        self._last_time_list = None
        self._update_complete = False
        self._pcb = None  # Periodic callback
        # self._ntcb = None  # Next Tick callback
        # self.cds = ColumnDataSource()
        self.glyphs = {}
        # self.glyph_map = {}

        self.cds = self.build_data_sources()
        self.figure = self.create_figure()

        # self.modify_document()
        # self.figure = self.create_figure()

        # self._recurring_update = RecurringTask(
        #    self.verify_if_document_needs_to_be_modified, delay=1
        # )
        # self._recurring_update.start()
        # self.start_update_data()

    @property
    def network(self):
        return self._network()

    @property
    def document(self):
        return curdoc()

    def build_dataframe(self):
        self._log.info("Building dataframe")
        r = {}
        _metadata = {}
        for point in self.network.trends:
            name = "{}/{}".format(
                point.properties.device.properties.name, point.properties.name
            )
            description = point.properties.description
            units = point.properties.units_state
            r[name] = point.history
            if "analog" in point.properties.type:
                self.analog_queue.put((name, description, units))
            elif "binary" in point.properties.type:
                self.binary_queue.put((name, description, units))
            else:
                self.multistates_queue.put((name, description, units))

        df = pd.DataFrame(r)
        df = df.reset_index()
        df["time_s"] = df["index"].apply(str)
        try:
            df = (
                df.fillna(method="ffill")
                .fillna(method="bfill")
                .replace(["inactive", "active"], [0, 1])
            )
        except TypeError:
            df = df.fillna(method="ffill").fillna(method="bfill")
        return df

    def make_glyph_invisible(self):
        for k, v in self.glyphs["analog"].items():
            v.visible = False
        for k, v in self.glyphs["binary"].items():
            v.visible = False
        for k, v in self.glyphs["multistates"].items():
            v.visible = False

    def update_glyphs(self):
        self._log.info("Updating Glyphs")
        for each in [
            (self.analog_queue, "analog"),
            (self.binary_queue, "binary"),
            (self.multistates_queue, "mnultistates"),
        ]:
            i = 0
            process_queue, key = each
            while not process_queue.empty():
                index = "{}{}".format(key[0].upper(), i)
                name, description, units = process_queue.get()
                self._log.info("Processing {} on index {}".format(name, index))
                self.glyphs[key][index].y = name
                self.glyphs[key][index].name = name
                self.glyphs[key][index].legend_label = "{} | {} ({})".format(
                    name, description, units
                )
                self.glyphs[key][index].visible = True
                self._log.info(
                    "{} | Visible : {}".format(
                        self.glyphs[key][index], self.glyphs[key][index].visible
                    )
                )
                i += 1
        self._log.info("Update of Glyphs over")

    def update_plot(self):
        self._log.info("Updating Plot...making visible")
        doc = curdoc()
        doc.add_next_tick_callback(self.make_glyph_invisible)
        doc.add_next_tick_callback(self.update_glyphs)
        # self.update_glyphs(self.analog_queue, "analog")
        # self.update_glyphs(self.binary_queue, "binary")
        # self.update_glyphs(self.multistates_queue, "multistates")

    def update(self):
        df = self.build_dataframe()
        d = {
            "level_0": df.index.values,
            "index": df["index"].values,
            "time_s": df["time_s"].values,
        }

        for point in self.network.trends:
            name = "{}/{}".format(
                point.properties.device.properties.name, point.properties.name
            )
            d[name] = df[name].values
        try:
            self.cds.data = d
        except RuntimeError as error:
            self._log.warning("Update failed, will try later | {}".format(error))

        if self.verify_if_document_needs_to_be_modified:
            self.make_glyph_invisible()
            self.update_glyphs()

    def build_data_sources(self):
        df = self.build_dataframe()
        # cds = ColumnDataSource(df)
        # cds.tags = [_metadata]
        return ColumnDataSource(df)

    def create_figure(self):
        analog_glyphs = {}
        binary_glyphs = {}
        multistates_glyphs = {}

        self._log.debug("Creating figure")

        TOOLS = "pan,box_zoom,wheel_zoom,save,reset"
        p = Figure(
            x_axis_type="datetime",
            x_axis_label="Time",
            y_axis_label="Numeric Value",
            title="BAC0 Trends",
            tools=TOOLS,
            plot_width=800,
            plot_height=600,
            toolbar_location="right",
        )

        p.background_fill_color = "#f4f3ef"
        p.border_fill_color = "#f4f3ef"
        p.extra_y_ranges = {
            "bool": Range1d(start=0, end=1.1),
            "enum": Range1d(start=0, end=10),
        }
        p.add_layout(LinearAxis(y_range_name="bool", axis_label="Binary"), "left")
        p.add_layout(LinearAxis(y_range_name="enum", axis_label="Enumerated"), "right")

        hover = HoverTool(
            tooltips=[
                ("name", "@name"),
                ("value", "@y"),
                ("units", "@units"),
                ("time", "@time"),
            ]
        )
        p.add_tools(hover)

        length = len(self.network.trends)
        keys = [each.properties.name for each in self.network.trends]
        if length <= 10:
            if length < 3:
                length = 3
            color_mapper = dict(zip(keys, d3["Category10"][length]))
        else:
            # This would be a very loaded trend...
            palette_size = min(length, 256)
            palette_count = length // palette_size + 1
            color_mapper = dict(
                zip(
                    keys,
                    [
                        color
                        for color in viridis(palette_size)
                        for _ in range(palette_count)
                    ],
                )
            )

        for each in range(20):
            binary_glyphs["B{}".format(each)] = p.circle(
                x="index",
                y="B{}".format(each),
                source=self.cds,
                name="empty",
                # color=color_mapper[each.properties.name],
                y_range_name="bool",
                size=10,
                legend_label=("{} | {} (OFF-ON)".format("name", "description")),
                visible=False,
            )

            multistates_glyphs["M{}".format(each)] = p.diamond(
                x="index",
                y="M{}".format(each),
                source=self.cds,
                name="empty",
                # color=color_mapper[each.properties.name],
                legend_label=("{} | {} ({})".format("name", "description", "units")),
                y_range_name="enum",
                size=20,
                visible=False,
            )
            analog_glyphs["A{}".format(each)] = p.line(
                x="index",
                y="A{}".format(each),
                source=self.cds,
                name="empty",
                # color=color_mapper[each.properties.name],
                legend_label=("{} | {} ({})".format("name", "description", "units")),
                line_width=2,
                visible=False,
            )

        p.legend.location = "top_left"
        # legend = Legend(items=self.legends_list, location=(0, -60))
        p.legend.click_policy = "hide"
        # self.p.add_layout(legend, "right")
        self.glyphs = {
            "analog": analog_glyphs,
            "binary": binary_glyphs,
            "multistates": multistates_glyphs,
        }
        return p

    def old_create_figure(self):
        self._log.debug("Creating figure")

        TOOLS = "pan,box_zoom,wheel_zoom,save,reset"
        p = Figure(
            x_axis_type="datetime",
            x_axis_label="Time",
            y_axis_label="Numeric Value",
            title="BAC0 Trends",
            tools=TOOLS,
            plot_width=800,
            plot_height=600,
            toolbar_location="right",
        )

        p.background_fill_color = "#f4f3ef"
        p.border_fill_color = "#f4f3ef"
        p.extra_y_ranges = {
            "bool": Range1d(start=0, end=1.1),
            "enum": Range1d(start=0, end=10),
        }
        p.add_layout(LinearAxis(y_range_name="bool", axis_label="Binary"), "left")
        p.add_layout(LinearAxis(y_range_name="enum", axis_label="Enumerated"), "right")

        hover = HoverTool(
            tooltips=[
                ("name", "@name"),
                ("value", "@y"),
                ("units", "@units"),
                ("time", "@time"),
            ]
        )
        p.add_tools(hover)

        length = len(self.network.trends)
        keys = [each.properties.name for each in self.network.trends]
        if length <= 10:
            if length < 3:
                length = 3
            color_mapper = dict(zip(keys, d3["Category10"][length]))
        else:
            # This would be a very loaded trend...
            palette_size = min(length, 256)
            palette_count = length // palette_size + 1
            color_mapper = dict(
                zip(
                    keys,
                    [
                        color
                        for color in viridis(palette_size)
                        for _ in range(palette_count)
                    ],
                )
            )

        for each in self.network.trends:
            if "binary" in each.properties.type:
                p.circle(
                    x="index",
                    y=each.property.name,
                    source=self.cds,
                    name=each.properties.name,
                    color=color_mapper[each.properties.name],
                    y_range_name="bool",
                    size=10,
                    legend_label=(
                        "{} | {} (OFF-ON)".format(
                            each.properties.name, each.properties.description
                        )
                    ),
                )

            elif "multi" in each.properties.type:
                p.diamond(
                    x="index",
                    y=each.properties.name,
                    source=self.cds,
                    name=each.properties.name,
                    color=color_mapper[each.properties.name],
                    legend_label=(
                        "{} | {} ({})".format(
                            each.properties.name,
                            each.properties.description,
                            each.properties.units_state,
                        )
                    ),
                    y_range_name="enum",
                    size=20,
                )
            else:
                p.line(
                    x="index",
                    y=each.properties.name,
                    source=self.cds,
                    name=each.properties.name,
                    color=color_mapper[each.properties.name],
                    legend_label=(
                        "{} | {} ({})".format(
                            each.properties.name,
                            each.properties.description,
                            each.properties.units_state,
                        )
                    ),
                    line_width=2,
                )

            p.legend.location = "top_left"
            # legend = Legend(items=self.legends_list, location=(0, -60))
            p.legend.click_policy = "hide"
            # self.p.add_layout(legend, "right")
            return p

    def modify_document(self, doc):
        self._log.info("Modify document")
        # doc.clear()
        self.cds = self.build_data_sources()
        self.figure = self.create_figure()
        # layout = row(self.figure, name='main_layout')
        layout = gridplot([self.figure], ncols=2)

        doc.add_root(layout)
        self._pcb = doc.add_periodic_callback(self.update, 10000)
        return doc

    # def modify_children_of_layout(self):
    #    doc = curdoc()
    #    rootLayout = doc.get_model_by_name("main_layout")
    #    listOfSubLayouts = rootLayout.children
    #    print(listOfSubLayouts)

    def verify_if_document_needs_to_be_modified(self):
        # self._log.info("Check if document needs to be changed")
        if self._last_time_list != self.network.trends:
            self._log.debug(
                "List of points to trend have changed, document will be modified."
            )
            # self.stop_update_data()
            self._last_time_list = self.network.trends
            return True
        else:
            return False

    def stop_update_data(self):
        doc = curdoc()
        try:
            doc.remove_periodic_callback(self._pcb)
        except:
            pass


#        if self._recurring_update.is_running:
#            self._recurring_update.stop()
#            while self._recurring_update.is_running:
#                pass
#        try:
#            doc.remove_next_tick_callback(self._ntcb)
#        except (ValueError, RuntimeError):
#            pass  # Already gone

#    def start_update_data(self):
#        if not self._recurring_update.is_running:
#            try:
#                self._recurring_update.start()
#                while not self._recurring_update.is_running:
#                    pass
#            except RuntimeError:
#                pass


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
            TableColumn(field="Name", title="Name"),
        ]
        data_table = DataTable(source=dev, columns=columns)
        layout = row([data_table])
        doc.add_root(layout)
        doc.title = "BACnet devices"
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
            TableColumn(field="Name", title="Name"),
        ]
        data_table = DataTable(source=dev, columns=columns)
        layout = row([data_table])
        doc.add_root(layout)
        doc.title = "BACnet devices"
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
        notes_df.columns = ["index", "notes"]
        notes = ColumnDataSource(notes_df)
        self.columns = [
            TableColumn(field="index", title="Timestamp"),
            TableColumn(field="notes", title="Notes"),
        ]
        self.data_table = DataTable(source=notes, columns=self.columns)
        layout = row([self.data_table])
        doc.add_root(layout)
        doc.title = "Notes for {}".format(controller)
        # doc.add_periodic_callback(self.update_data,100)
        return doc

    def update_data(self):
        controller = self.network.notes[0]
        notes_df = pd.DataFrame(self.network.notes[1]).reset_index()
        notes_df.columns = ["index", "notes"]
        notes = ColumnDataSource(notes_df)
        self.data_table.source.data.update(notes.data)
        curdoc().title = "Notes for {}".format(controller)
