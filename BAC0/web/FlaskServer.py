#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module starts an external process : bokeh serve
As Bokeh use Tornado, I didn't find a way to include the server in the code.
The IOLoop creates some conflicts. 

So actually, the process is called outside of the script... then communication
with the server is made using localhost:5006
"""
from threading import Thread
import weakref

from flask import Flask, render_template, jsonify
from bokeh.embed import server_document

from .templates import create_sidebar, create_card
from ..core.functions.PrintDebug import print_list

class FlaskServer(Thread):

    # Init thread running server
    def __init__(self, network, port=8111, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.flask_app = Flask(__name__)
        self._network_ref = weakref.ref(network)
        self.port = port
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
        self.flask_app.run(port=self.port)

    def config_flask_app(self):
        @self.flask_app.route('/trends', methods=['GET'])
        def bkapp_trends_page():
            if self.network.number_of_registered_trends > 0:
                script = server_document('http://localhost:5006/trends')
            else:
                script = "<div>No trend registered yet...</div>"
            return render_template("trends.html",
                                   sidebar=create_sidebar(trends_class = 'class="active"'),
                                   bokeh_script=script, 
                                   template="Flask")
 
#        @self.flask_app.route('/devices', methods=['GET'])
#        def bkapp_devices_page():
#            script = server_document('http://localhost:5006/devices')
#            return render_template("embed.html", script=script, template="Flask")

        @self.flask_app.route('/notes', methods=['GET'])
        def bkapp_notes_page():
            script = server_document('http://localhost:5006/notes')
            return render_template("embed.html", script=script, template="Flask")

        @self.flask_app.route('/', methods=['GET'])
        def home_page():
            # Stat number of devices
            cnod = create_card(icon = 'ti-server',
                               title = 'Number of devices',
                               data = self.network.number_of_devices,
                               id_data = 'devices',
                               foot_icon = 'ti-reload',
                               foot_data = 'Refresh to update')
            cnot = create_card(icon = 'ti-bar-chart',
                               title = 'Number of trends',
                               data = self.network.number_of_registered_trends,
                               id_data = 'trends',
                               foot_icon = 'ti-timer',
                               foot_data = 'Add trends !')
            cnmn = create_card(icon = 'ti-plug',
                               title = 'MSTP Networks',
                               data = '%s' % (self.network.network_stats['print_mstpnetworks']),
                               id_data = 'mstpnetworks',
                               foot_icon = 'ti-timer',
                               foot_data = 'Last update : %s' % self.network.network_stats['timestamp'],
                               id_foot_data = 'lastwhoisupdate')
            return render_template("dashboard.html", 
                                   sidebar=create_sidebar(dash_class = 'class="active"'),
                                   card_number_of_devices = cnod,
                                   card_number_of_mstp_networks = cnmn,
                                   card_number_of_trends = cnot,
                                   template="Flask")


        @self.flask_app.route('/dash_devices', methods=['GET'])
        def dashboard_devices_page():
            script = server_document('http://localhost:5006/devices')
            return render_template("device_table.html",
                                   sidebar=create_sidebar(devices_class = 'class="active"'),
                                   bokeh_script = script,
                                   template="Flask")
        
        @self.flask_app.route('/_dash_live_data', methods= ['GET'])
        def dash_live_data():
            devices=self.network.number_of_devices
            trends=self.network.number_of_registered_trends
            return jsonify(number_of_devices=devices, number_of_registered_trends=trends)

        @self.flask_app.route('/_whois', methods= ['GET'])
        def whois():
            self.network.whois_answer = self.network.update_whois()
            return jsonify(done='done')

        @self.flask_app.route('/_dash_live_stats', methods= ['GET'])
        def dash_live_stats():
            stats=self.network.network_stats
            return jsonify(stats=stats)

        @self.flask_app.route('/_network_pie_chart', methods= ['GET'])
        def net_pie_chart():
            stats=self.network.number_of_devices_per_network()
            return jsonify(stats=stats)
        
    def task(self):
        try:
            self.startServer()
        except Exception as err:
            print('Flask server already running', err)
            self.exitFlag = True

    def stop(self):
        print('Trying to stop Bokeh Server')
        #self.bokeh_server.stop()
        self.p.terminate()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
    