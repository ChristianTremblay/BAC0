#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module allows the creation of threads that will be used as repetitive
tasks for simulation purposes
"""
from threading import Thread

import time
import random
from bokeh.plotting import Figure, ColumnDataSource
from bokeh.models import HoverTool, LinearAxis, Range1d
from bokeh.io import gridplot, vplot, curdoc
#from bokeh.embed import autoload_server
#from bokeh.session import Session
#from bokeh.document import Document

from bokeh.application import Application
from bokeh.document import Document
from bokeh.server.server import Server


class BokehServer(Thread):

    # Init thread running server
    def __init__(self, *, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.exitFlag = False
        self.app = Application()
        
    def run(self):
        self.process()

    def process(self):
        # if self.started = True
        while not self.exitFlag:
            self.task()

    def task(self):

        self.bokeh_server = Server(self.app)

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
