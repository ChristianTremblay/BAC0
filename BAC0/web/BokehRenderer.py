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
    Label,
    LabelSet,
    LinearAxis,
    Legend,
    LegendItem,
    Dropdown,
    MultiChoice,
    CustomJS,
)
from bokeh.models.widgets import DataTable, TableColumn, Div
from bokeh.layouts import widgetbox, row, column, gridplot, widgetbox
from bokeh.palettes import d3, viridis
from bokeh.io import curdoc
from bokeh.application.handlers import Handler
from bokeh.models.tools import CustomJSHover

from functools import partial

from tornado import gen

import math
import pandas as pd
import weakref
from queue import Queue
from collections import deque

from ..tasks.RecurringTask import RecurringTask
from ..core.utils.notes import note_and_log
from ..core.devices.Virtuals import VirtualPoint
from ..core.devices.Trends import TrendLog


@note_and_log
class DynamicPlotHandler(Handler):

    analog_queue = Queue()
    binary_queue = Queue()
    multistates_queue = Queue()
    multistates_label_queue = Queue()
    virtuals_queue = Queue()

    def __init__(self, network):
        super().__init__()
        self._network = weakref.ref(network)

        self._last_time_list = None
        self._last_time_devices = None
        self._peristent_widget_choices = {}
        self._update_complete = False
        self._pcb = None  # Periodic callback
        self.widget = column(
            children=[MultiChoice(value=[], options=["n/a"])],
            sizing_mode="scale_width",
            name="widgetbox",
        )

        self._analog_name = ["A{}".format(each) for each in range(20)]
        self._binary_name = ["B{}".format(each) for each in range(20)]
        self._multistates_name = ["M{}".format(each) for each in range(20)]
        self._multistates_labels = ["M{}_state".format(each) for each in range(20)]
        self._virtuals_name = ["V{}".format(each) for each in range(20)]
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

    def clean_trend_list(self):
        a = []
        b = []
        m = []
        v = []
        for trend in self.network.trends:
            if "analog" in trend.properties.type:
                a.append(trend)
            elif "binary" in trend.properties.type:
                b.append(trend)
            elif "multi" in trend.properties.type:
                m.append(trend)
            else:
                v.append(trend)
        for each in a[19:]:
            self.warning(
                "Too many analog trends, removing {}".format(each.properties.name)
            )
            self.network.remove_trend(each)
        for each in b[19:]:
            self.warning(
                "Too many binary trends, removing {}".format(each.properties.name)
            )
            self.network.remove_trend(each)
        for each in m[19:]:
            self.warning(
                "Too many mutlistates trends, removing {}".format(each.properties.name)
            )
            self.network.remove_trend(each)
        for each in v[19:]:
            self.warning(
                "Too many virtual trends, removing {}".format(each.properties.name)
            )
            self.network.remove_trend(each)

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

        def _add_mv_states(val):
            try:
                return val.split(":")[1]
            except AttributeError:
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
            if "multi" in point.properties.type:
                # Create a series but keep only the first time the value change
                # Because I don't want to fill the trend with labels...
                _name = name + "_state"
                _duplicate = name + "_duplicate"
                r[_name] = point.history.apply(lambda x: _add_mv_states(x))
                r[_duplicate] = r[name].eq(r[name].shift())
                r[_name].loc[r[_duplicate]] = ""
                del r[_duplicate]

        try:
            df = pd.DataFrame(r)
        except ValueError:
            self._log.error("Problem with dataframe creation. {}".format(r.keys()))
            self.trouble_r = r
            raise
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
        for _, v in self.glyphs["analog"].items():
            v.visible = False
        for _, v in self.glyphs["binary"].items():
            v.visible = False
        for _, v in self.glyphs["multistates"].items():
            v.visible = False
        for _, v in self.glyphs["multistates_labels"].items():
            v.visible = False
        for _, v in self.glyphs["virtual"].items():
            v.visible = False

    def update_glyphs(self):
        self._log.debug("Updating Glyphs")
        enumerated_axis_needed = True
        for point in self.network.trends:
            name = "{}/{}".format(
                point.properties.device.properties.name, point.properties.name
            )
            if "analog" in point.properties.type or "TrendLog" in point.properties.type:
                self.analog_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )
            elif "binary" in point.properties.type:
                self.binary_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )
            elif "multi" in point.properties.type:
                enumerated_axis_needed = True
                self.multistates_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )
                self.multistates_label_queue.put(
                    (
                        name + "_state",
                        point.properties.description,
                        point.properties.units_state,
                    )
                )
            elif "virtual" in point.properties.type:
                self.virtuals_queue.put(
                    (name, point.properties.description, point.properties.units_state)
                )

        # for each in self.figure.right:
        #    try:
        #        if each.axis_label == "Enumerated":
        #            each.visible = enumerated_axis_needed
        #    except AttributeError:
        #        pass
        for each in [
            (self.analog_queue, "analog"),
            (self.binary_queue, "binary"),
            (self.multistates_queue, "multistates"),
            (self.multistates_label_queue, "multistates_labels"),
            (self.virtuals_queue, "virtual"),
        ]:
            i = 0
            process_queue, key = each

            while not process_queue.empty():

                index = "{}{}".format(key[0].upper(), i)
                if "labels" in key:
                    index = index + "_state"
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
            multistates_states = "M{}_state".format(each)
            virtuals_name = "V{}".format(each)
            _temp = {
                analog_name: None,
                binary_name: None,
                multistates_name: None,
                multistates_states: None,
                virtuals_name: None,
            }
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

        # add selected points to bacnet.trend
        def get_device(name):
            for controller in self.network.registered_devices:
                if controller.properties.name == name:
                    return controller
            raise KeyError("Controller not found")

        def _already_trended(name):
            # print('Point name : {}'.format(name))
            for point in self.network.trends:
                if point.properties.name == name:
                    return True
            return False

        self._all_points_selected = []

        for device_choice in self.widget.children:
            try:
                _device = get_device(device_choice.title)
            except KeyError:
                continue
            self._peristent_widget_choices[device_choice.title] = device_choice.value
            for point_name in device_choice.value:
                self._all_points_selected.append(
                    "{}/{}".format(device_choice.title, point_name)
                )
                if not _already_trended(point_name):
                    _name = "{}/{}".format(device_choice.title, point_name)
                    self._log.info("Adding {} to trends".format(_name))
                    _device[point_name].chart()

        #       self._all_points_selected = [device_choice.value for device_choice in self.widget.children][0]
        for point in self.network.trends:
            _trend_name = "{}/{}".format(
                point.properties.device.properties.name, point.properties.name
            )
            if _trend_name not in self._all_points_selected and not isinstance(
                point, VirtualPoint
            ):
                self._log.info("Removing {} from trends".format(_trend_name))
                self.network.remove_trend(point)
                for k, v in self._cds_struct.items():
                    if v == _trend_name:
                        self._cds_struct[k] = None

                for device_choice in self.widget.children:
                    self._peristent_widget_choices[
                        device_choice.title
                    ] = device_choice.value

        if self.verify_if_document_needs_to_be_modified():
            try:
                self.update_glyphs()
                self.update_legend()
                self.update_widgets()
            except RuntimeError:
                self._log.warning("Problem updating. Will retry")

    def create_figure(self):

        analog_glyphs = {}
        binary_glyphs = {}
        multistates_glyphs = {}
        multistates_labels = {}
        virtuals_glyphs = {}

        self._log.debug("Creating figure")

        TOOLS = "pan,box_zoom,wheel_zoom,save,reset"
        p = Figure(
            x_axis_type="datetime",
            x_axis_label="Time",
            y_axis_label="Value",
            title="Live trends",
            tools=TOOLS,
            plot_width=1200,
            plot_height=800,
            toolbar_location="right",
        )

        p.title.text_font_size = "24pt"
        p.xaxis.axis_label_text_font_size = "18pt"
        p.yaxis.axis_label_text_font_size = "18pt"
        p.xaxis.axis_label_text_font_style = "normal"
        p.yaxis.axis_label_text_font_style = "normal"
        p.xaxis.major_label_text_font_size = "12pt"
        p.yaxis.major_label_text_font_size = "12pt"

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
            LinearAxis(
                y_range_name="enum",
                axis_label="Enumerated",
                visible=False,
                # ticker=list(range(11)),
            ),
            "right",
        )

        hover_common = HoverTool(
            tooltips=[
                ("name", "$name"),
                ("value", "$data_y"),
                # ('state', "@$name_state"),
                # ("units", "$tags"),
                ("time", "@time_s"),
            ],
            renderers=[],
            toggleable=False,
            formatters={"@time_s": "datetime"},
            mode="mouse",
        )
        hover_multi = {}

        p.add_tools(hover_common)

        for name in self._binary_name:
            binary_glyphs[name] = p.step(
                x="index",
                y=name,
                source=self.cds,
                name=name,
                color=self.color_mappers["binary"][name],
                y_range_name="bool",
                mode="after",
                line_width=8,
                visible=False,
                tags=["unit", "description"],
            )
            # binary_glyphs[name].add_tool(hover_common)
            hover_common.renderers.append(binary_glyphs[name])

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
                mode="after",
            )

        #        for name in self._multistates_labels:
        #            multistates_labels[name] = LabelSet(x="index", y=name.split('_')[0], text=name, level='glyph',
        #              x_offset=0, y_offset=1, source=self.cds, render_mode='canvas', visible=False)
        #            p.add_layout(multistates_labels[name])
        #        for name in self._multistates_labels:
        #            _msname = name.split("_")[0]
        #            multistates_labels[name] = p.circle(
        #                x="index",
        #                y=_msname,
        #                source=self.cds,
        #                color=self.color_mappers["multistates"][_msname],
        #                size=10,
        #                alpha=0.1,
        #                y_range_name="enum",
        #                visible=False,
        #            )
        #            hover_multi[name] = HoverTool(
        #                tooltips=[
        #                    ("name", "$name"),
        #                    ("value", "@" + name),
        #                    ("time", "@time_s"),
        #                ],
        #                mode="mouse",
        #                renderers=[multistates_labels[name]],
        #                toggleable=False,
        #            )
        #            p.add_tools(hover_multi[name])

        for name in self._multistates_labels:
            _msname = name.split("_")[0]
            multistates_labels[name] = p.text(
                x="index",
                y=_msname,
                text=name,
                source=self.cds,
                text_color=self.color_mappers["multistates"][_msname],
                angle=0.7835,
                # size=10,
                # alpha=0.1,
                y_range_name="enum",
                visible=False,
            )
            hover_multi[name] = HoverTool(
                tooltips=[
                    ("name", "$name"),
                    ("value", "@" + name),
                    ("time", "@time_s"),
                ],
                mode="mouse",
                renderers=[multistates_labels[name]],
                toggleable=False,
            )
            p.add_tools(hover_multi[name])

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
            # analog_glyphs[name].add_tool(hover_common)
            hover_common.renderers.append(analog_glyphs[name])

        for name in self._virtuals_name:
            virtuals_glyphs[name] = p.line(
                x="index",
                y=name,
                source=self.cds,
                name=name,
                color=self.color_mappers["virtual"][name],
                line_width=2,
                visible=False,
                tags=["unit", "description"],
            )
            # virtuals_glyphs[name].add_tool(hover_common)
            hover_common.renderers.append(virtuals_glyphs[name])

        self.glyphs = {
            "analog": analog_glyphs,
            "binary": binary_glyphs,
            "multistates": multistates_glyphs,
            "multistates_labels": multistates_labels,
            "virtual": virtuals_glyphs,
        }
        legend = Legend(items=[])
        legend.click_policy = "hide"
        p.add_layout(legend, "below")
        return p

    @staticmethod
    def _type(k):
        try:
            t = {"A": "analog", "B": "binary", "M": "multistates", "V": "virtual"}
            _k = t[k[0]]
        except KeyError:
            _k = k
        return _k

    def update_legend(self):
        lst_of_items = []
        for k, v in self._cds_struct.items():
            if not v or "_state" in k:
                continue
            try:
                _t = DynamicPlotHandler._type(k)
                glyph = self.glyphs[_t][k]
                label = "{} | {} ({})".format(glyph.name, glyph.tags[1], glyph.tags[0])
                if _t != "M":
                    lst_of_items.append(LegendItem(label=label, renderers=[glyph]))
                else:
                    glyph_text = self.glyphs["multistates_labels"][k]
                    lst_of_items.append(
                        LegendItem(label=label, renderers=[glyph, glyph_text])
                    )
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

        palette = rotate_palette(palette)
        keys = [each for each in self._virtuals_name]
        virtual_color_mapper = dict(zip(keys, palette))

        return {
            "analog": analog_color_mapper,
            "binary": binary_color_mapper,
            "multistates": multistates_color_mapper,
            "virtual": virtual_color_mapper,
        }

    def modify_document(self, doc):
        self._log.debug("Modify document")
        self.stop_update_data()
        doc.clear()
        self._cds_struct = {}
        self.cds = self.initialize_cds()
        self.figure = self.create_figure()
        layout = row(
            [
                column([self.figure], name="main_plot"),
                column([self.widget], name="widgets"),
            ]
        )
        doc.add_root(layout)
        self._pcb = doc.add_periodic_callback(self.update, 3000)
        return doc

    def verify_if_document_needs_to_be_modified(self):
        # self.clean_trend_list()
        if (
            self._last_time_list != self.network.trends
            or self._last_time_devices != self.network.registered_devices
        ):
            self._log.debug(
                "List of points to trend have changed, document will be modified."
            )
            self._last_time_list = self.network.trends
            self._last_time_devices = self.network.registered_devices
            return True
        else:
            return False

    def stop_update_data(self):
        doc = curdoc()
        try:
            doc.remove_periodic_callback(self._pcb)
        except:
            pass

    def update_widgets(self):
        sel = self.generate_selection()
        self.widget.children = sel

    def generate_selection(self):
        devices = self.network.registered_devices
        selectors = []
        _cache = []

        for device in devices:
            try:
                _cache = self._peristent_widget_choices[device.properties.name]
            except KeyError:
                pass
            options = list(device.points_name)
            options.extend(list(device.trendlogs_names))
            mc = MultiChoice(
                value=_cache, options=options, title=device.properties.name
            )
            mc.js_on_change(
                "value",
                CustomJS(
                    code="""
                console.log('multi_choice: value=' + this.value, this.toString())
                """
                ),
            )

            selectors.append(mc)
        return selectors


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
