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

from flask import Flask, render_template, jsonify
from bokeh.embed import server_document

from .templates import create_sidebar, create_card

class FlaskServer(Thread):

    # Init thread running server
    def __init__(self, network, port=8111, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.flask_app = Flask(__name__)
        self.network = network
        self.port = port
        self.config_flask_app()
        self.exitFlag = False
                
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
            script = server_document('http://localhost:5006/trends')
            return render_template("embed.html", script=script, template="Flask")
 
        @self.flask_app.route('/devices', methods=['GET'])
        def bkapp_devices_page():
            script = server_document('http://localhost:5006/devices')
            return render_template("embed.html", script=script, template="Flask")

        @self.flask_app.route('/notes', methods=['GET'])
        def bkapp_notes_page():
            script = server_document('http://localhost:5006/notes')
            return render_template("embed.html", script=script, template="Flask")

        @self.flask_app.route('/dash', methods=['GET'])
        def dashboard_page():
            # Stat number of devices
            cnod = create_card(icon = 'ti-server',
                               title = 'Number of devices',
                               data = self.network.number_of_devices,
                               name = '#devices',
                               foot_icon = 'ti-reload',
                               foot_data = 'Refresh to update')
            cnot = create_card(icon = 'ti-pulse',
                               title = 'Number of trends',
                               data = self.network.number_of_registered_trends,
                               name = '#trends',
                               foot_icon = 'ti-timer',
                               foot_data = 'Add trends !')
            return render_template("dashboard.html", 
                                   sidebar=create_sidebar(),
                                   card_number_of_devices = cnod,
                                   card_number_of_trends = cnot,
                                   template="Flask")

        @self.flask_app.route('/dash_devices', methods=['GET'])
        def dashboard_devices_page():
            return render_template("table.html",
                                   sidebar=create_sidebar(),
                                   template="Flask")
        
        @self.flask_app.route('/', methods=['GET'])
        def home_page():
            #script = server_document('http://localhost:5006')
            return render_template("template.html", template="Flask") 
        
        @self.flask_app.route('/_dash_live_data', methods= ['GET'])
        def dash_live_data():
            devices=self.network.number_of_devices
            trends=self.network.number_of_registered_trends
            return jsonify(number_of_devices=devices, number_of_registered_trends=trends)
        
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
    