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
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    Range1d,
    LinearAxis,
    Legend,
    LegendItem,
)
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
from collections import deque

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

        self._analog_name = ["A{}".format(each) for each in range(20)]
        self._binary_name = ["B{}".format(each) for each in range(20)]
        self._multistates_name = ["M{}".format(each) for each in range(20)]
        self.color_mappers = self.create_color_mappers()

        self._cds_struct = {}
        self.cds = self.initialize_cds()
        self.glyphs = {}

        self.figure = self.create_figure()

    @property
    def network(self):
        return self._network()

    @property
    def document(self):
        return curdoc()

    def build_dataframe(self):
        def _translate_binary_values(val):
            if val == "active:":
                return 0
            elif val == "inactive":
                return 1
            elif isinstance(val, str) and ":" in val:
                return int(val.split(":")[0])
            else:
                return val

        self._log.debug("Building dataframe")
        r = {}
        for point in self.network.trends:
            name = "{}/{}".format(
                point.properties.device.properties.name, point.properties.name
            )
            if point.history.dtype == "O":
                r[name] = point.history.apply(lambda x: _translate_binary_values(x))
            else:
                r[name] = point.history

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
        self._log.debug("Updating Glyphs")
        for point in self.network.trends:
            name = "{}/{}".format(
                point.properties.device.properties.name, point.properties.name
            )
            if "analog" in point.properties.type:
                self.analog_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )
            elif "binary" in point.properties.type:
                self.binary_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )
            else:
                self.multistates_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )
        for each in [
            (self.analog_queue, "analog"),
            (self.binary_queue, "binary"),
            (self.multistates_queue, "multistates"),
        ]:
            i = 0
            process_queue, key = each
            while not process_queue.empty():
                index = "{}{}".format(key[0].upper(), i)
                name, description, units = process_queue.get()
                self._log.debug("Processing {} on index {}".format(name, index))
                self._cds_struct[index] = name
                self.glyphs[key][index].name = name
                self.glyphs[key][index].tags = [units, description]
                self.glyphs[key][index].visible = True
                self._log.debug(
                    "{} | Visible : {}".format(
                        self.glyphs[key][index], self.glyphs[key][index].visible
                    )
                )
                i += 1
        self._log.debug("Update of Glyphs over")

    def initialize_cds(self):
        for each in range(20):
            analog_name = "A{}".format(each)
            binary_name = "B{}".format(each)
            multistates_name = "M{}".format(each)
            _temp = {analog_name: None, binary_name: None, multistates_name: None}
            self._cds_struct.update(_temp)

        self._cds_struct.update({"index": "index", "time_s": "time_s"})

        df = self.build_dataframe()
        self.new_data = {}
        # add keys
        for k, v in self._cds_struct.items():
            self.new_data[k] = None

        for k, v in self.new_data.items():
            try:
                self.new_data[k] = df[self._cds_struct[k]].values
            except KeyError:
                self.new_data[k] = df["time_s"].values

        return ColumnDataSource(self.new_data)

    def update(self):
        df = self.build_dataframe()

        self.new_data = {}
        # add keys
        for k, v in self._cds_struct.items():
            self.new_data[k] = None

        for k, v in self.new_data.items():
            try:
                self.new_data[k] = df[self._cds_struct[k]].values

            except (KeyError, ValueError):
                self.new_data[k] = df["time_s"].values

        try:
            self.cds.data = self.new_data
        except RuntimeError as error:
            self._log.warning("Update failed, will try later | {}".format(error))

        if self.verify_if_document_needs_to_be_modified():
            try:
                self.update_glyphs()
                self.update_legend()
            except RuntimeError:
                self._log.warning("Problem updating. Will retry")

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
            plot_width=1200,
            plot_height=800,
            toolbar_location="right",
        )

        p.background_fill_color = "#f4f3ef"
        p.border_fill_color = "#f4f3ef"
        p.extra_y_ranges = {
            "bool": Range1d(start=0, end=1.1),
            "enum": Range1d(start=0, end=10),
        }
        p.add_layout(
            LinearAxis(y_range_name="bool", axis_label="Binary", visible=False), "left"
        )
        p.add_layout(
            LinearAxis(y_range_name="enum", axis_label="Enumerated", visible=True),
            "right",
        )

        hover = HoverTool(
            tooltips=[
                ("name", "$name"),
                ("value", "$y"),
                # ("units", "$tags[0]"),
                ("time", "@time_s"),
            ]
        )
        p.add_tools(hover)

        for name in self._binary_name:
            binary_glyphs[name] = p.step(
                x="index",
                y=name,
                source=self.cds,
                name=name,
                color=self.color_mappers["binary"][name],
                y_range_name="bool",
                mode="after",
                line_width=4,
                visible=False,
                tags=["unit", "description"],
            )
        for name in self._multistates_name:
            multistates_glyphs[name] = p.step(
                x="index",
                y=name,
                source=self.cds,
                name=name,
                color=self.color_mappers["multistates"][name],
                y_range_name="enum",
                line_dash="dashed",
                line_width=7,
                visible=False,
                tags=["unit", "description"],
            )

        for name in self._analog_name:
            analog_glyphs[name] = p.line(
                x="index",
                y=name,
                source=self.cds,
                name=name,
                color=self.color_mappers["analog"][name],
                line_width=2,
                visible=False,
                tags=["unit", "description"],
            )

        self.glyphs = {
            "analog": analog_glyphs,
            "binary": binary_glyphs,
            "multistates": multistates_glyphs,
        }
        p.add_layout(Legend(items=[]), "below")
        return p

    @staticmethod
    def _type(k):
        try:
            t = {"A": "analog", "B": "binary", "M": "multistates"}
            _k = t[k[0]]
        except KeyError:
            _k = k
        # print(_k)
        return _k

    def update_legend(self):
        lst_of_items = []
        for k, v in self._cds_struct.items():
            if not v:
                continue
            # print(k, v)
            try:
                glyph = self.glyphs[DynamicPlotHandler._type(k)][k]
                # glyph = _glyph
                label = "{} | {} ({})".format(glyph.name, glyph.tags[1], glyph.tags[0])
                lst_of_items.append(LegendItem(label=label, renderers=[glyph]))
            except KeyError:
                pass

        self.figure.legend.items = lst_of_items

    def create_color_mappers(self):
        def rotate_palette(palette):
            for each in range(4):
                x = palette.pop()
                palette.insert(0, x)
            return palette

        palette = []
        _p = [d3["Category20"][20][i::4] for i in range(4)]
        for each in _p:
            palette.extend(each)
        keys = [each for each in self._analog_name]
        analog_color_mapper = dict(zip(keys, palette))

        palette = rotate_palette(palette)
        keys = [each for each in self._binary_name]
        binary_color_mapper = dict(zip(keys, palette))

        palette = rotate_palette(palette)
        keys = [each for each in self._multistates_name]
        multistates_color_mapper = dict(zip(keys, palette))

        return {
            "analog": analog_color_mapper,
            "binary": binary_color_mapper,
            "multistates": multistates_color_mapper,
        }

    def modify_document(self, doc):
        self._log.debug("Modify document")
        self.stop_update_data()
        doc.clear()
        self._cds_struct = {}
        self.cds = self.initialize_cds()
        self.figure = self.create_figure()
        layout = gridplot([self.figure], ncols=2)
        doc.add_root(layout)
        self._pcb = doc.add_periodic_callback(self.update, 3000)
        return doc

    def verify_if_document_needs_to_be_modified(self):
        if self._last_time_list != self.network.trends:
            self._log.debug(
                "List of points to trend have changed, document will be modified."
            )
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
