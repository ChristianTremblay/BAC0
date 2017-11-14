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

from bokeh.embed import server_document
   
class Bokeh_Worker(Thread):

    # Init thread running server
    def __init__(self, dev, trends,notes, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.dev = dev
        self.trends= trends
        self.notes= notes
        self.exitFlag = False
                
    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def startServer(self):
        self.server = Server({'/devices' : self.dev, 
                              '/trends' : self.trends,
                              '/notes' : self.notes}, allow_websocket_origin=["localhost:8111", "localhost:5006"])
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