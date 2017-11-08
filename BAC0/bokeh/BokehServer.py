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

from bokeh.server.server import Server

import sys
import subprocess
from subprocess import PIPE
import shlex

from flask import Flask, render_template
from bokeh.embed import server_document


class BokehServer(Thread):
    """
    DEPRECATED
    """

    # Init thread running server
    def __init__(self, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.exitFlag = False
                
    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def startServer(self):
        if 'win32' in sys.platform:
            commandToExecute = "bokeh serve"
        else:
            commandToExecute = "bokeh serve"
        cmdargs = shlex.split(commandToExecute)
        p = subprocess.Popen(cmdargs, stdout=PIPE, stderr=PIPE)
        output, errors = p.communicate()
        if p.returncode:
            print('Failed running %s' % commandToExecute)
            raise Exception(errors)
        return output.decode('utf-8')
    
    def task(self):
        try:
            self.startServer()
        except Exception:
            print('Bokeh server already running')
            self.exitFlag = True

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass

class FlaskServer(Thread):

    # Init thread running server
    def __init__(self, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.flask_app = Flask(__name__)
        self.config_flask_app()
        self.exitFlag = False
                
    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def startServer(self):
        self.flask_app.run(port=8111)

    def config_flask_app(self):
        @self.flask_app.route('/trends', methods=['GET'])
        def bkapp_trends_page():
            script = server_document('http://localhost:5006/trends')
            return render_template("embed.html", script=script, template="Flask")
 
        @self.flask_app.route('/devices', methods=['GET'])
        def bkapp_devices_page():
            script = server_document('http://localhost:5006/devices')
            return render_template("embed.html", script=script, template="Flask")
        
        @self.flask_app.route('/', methods=['GET'])
        def home_page():
            #script = server_document('http://localhost:5006')
            return render_template("index.html", template="Flask")   
        
    def task(self):
        try:
            self.startServer()
        except Exception as err:
            print('Flask server already running', err)
            self.exitFlag = True

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
    
class Bokeh_Worker(Thread):

    # Init thread running server
    def __init__(self, dev, trends, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.dev = dev
        self.trends= trends
        self.exitFlag = False
                
    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def startServer(self):
        self.server = Server({'/devices' : self.dev, '/trends' : self.trends}, allow_websocket_origin=["localhost:8111", "localhost:5006"])
        self.server.start()
        self.server.io_loop.start()
    
    def task(self):
        try:
            self.startServer()
        except Exception as err:
            print('Bokeh server already running', err)
            self.exitFlag = True

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass