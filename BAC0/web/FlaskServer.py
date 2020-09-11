#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module will start the Flask server 
"""
from threading import Thread
import weakref
import logging
from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
import json
from bokeh.embed import server_document

from .templates import create_sidebar, create_card, update_notifications
from flask.logging import default_handler


class FlaskServer(Thread):

    # Init thread running server
    def __init__(self, network, port=8111, ip="0.0.0.0", *, daemon=True):
        Thread.__init__(self, daemon=daemon)
        self.flask_app = Flask(__name__)
        Bootstrap(self.flask_app)
        self._network_ref = weakref.ref(network)
        self.port = port
        self.ip = ip
        self.notifications_log = []
        self.notifications_list = ""
        self.config_flask_app()
        self.exitFlag = False

    @property
    def network(self):
        return self._network_ref()

    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def startServer(self):
        self.flask_app.run(port=self.port, host="0.0.0.0")
        self.flask_app.logger.removeHandler(default_handler)

    def config_flask_app(self):
        @self.flask_app.route("/trends", methods=["GET"])
        def bkapp_trends_page():
            if self.network.registered_devices:
                script = server_document("http://{}:5006/trends".format(self.ip))
            else:
                script = "<div>No devices registered yet...</div>"
            return render_template(
                "trends.html",
                sidebar=create_sidebar(trends_class='class="active"'),
                bokeh_script=script,
                template="Flask",
            )

        #        @self.flask_app.route('/devices', methods=['GET'])
        #        def bkapp_devices_page():
        #            script = server_document('http://localhost:5006/devices')
        #            return render_template("embed.html", script=script, template="Flask")

        @self.flask_app.route("/notes", methods=["GET"])
        def bkapp_notes_page():
            script = server_document("http://{}:5006/notes".format(self.ip))
            return render_template("embed.html", script=script, template="Flask")

        @self.flask_app.route("/", methods=["GET"])
        def home_page():
            # Stat number of devices
            cnod = create_card(
                icon="ti-server",
                title="Number of devices",
                data=self.network.number_of_devices,
                id_data="devices",
                foot_icon="ti-reload",
                foot_data="Refresh to update",
            )
            cnot = create_card(
                icon="ti-bar-chart",
                title="Number of trends",
                data=self.network.number_of_registered_trends,
                id_data="trends",
                foot_icon="ti-timer",
                foot_data="Add trends !",
            )

            cnmn = create_card(
                icon="ti-plug",
                title="{} MSTP Networks".format(
                    len(self.network.network_stats["mstp_networks"])
                ),
                data="# {}".format(self.network.network_stats["print_mstpnetworks"]),
                id_data="mstpnetworks",
                foot_icon="ti-timer",
                foot_data="Last update : {}".format(
                    self.network.network_stats["timestamp"]
                ),
                id_foot_data="lastwhoisupdate",
            )

            notif = update_notifications(self.notifications_log, None)
            return render_template(
                "dashboard.html",
                sidebar=create_sidebar(dash_class='class="active"'),
                card_number_of_devices=cnod,
                card_number_of_mstp_networks=cnmn,
                card_number_of_trends=cnot,
                notifications=notif,
                template="Flask",
            )

        @self.flask_app.route("/dash_devices", methods=["GET"])
        def dashboard_devices_page():
            script = server_document("http://{}:5006/devices".format(self.ip))
            return render_template(
                "device_table.html",
                sidebar=create_sidebar(devices_class='class="active"'),
                bokeh_script=script,
                template="Flask",
            )

        @self.flask_app.route("/_dash_live_data", methods=["GET"])
        def dash_live_data():
            devices = self.network.number_of_devices
            trends = self.network.number_of_registered_trends
            return jsonify(
                number_of_devices=devices, number_of_registered_trends=trends
            )

        @self.flask_app.route("/_whois", methods=["GET"])
        def whois():
            self.notifications_list = update_notifications(
                self.notifications_log, "Sent a WhoIs Request"
            )
            self.network.discover()
            return jsonify(done="done")

        @self.flask_app.route("/_dash_live_stats", methods=["GET"])
        def dash_live_stats():
            stats = self.network.network_stats
            return jsonify(stats=stats)

        @self.flask_app.route("/_network_pie_chart", methods=["GET"])
        def net_pie_chart():
            stats = self.network.number_of_devices_per_network()
            return jsonify(stats=stats)

        @self.flask_app.route("/log", methods=["POST", "GET"])
        def log_page():
            return json.dumps(request.form)

    def task(self):
        try:
            self.startServer()
        except Exception as err:
            self._log.warning("Flask server already running", err)
            self.exitFlag = True

    def stop(self):
        self._log.debug("Trying to stop Bokeh Server")
        # self.bokeh_server.stop()
        self.p.terminate()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
