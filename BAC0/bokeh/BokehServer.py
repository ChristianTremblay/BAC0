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
import time

from bokeh.application import Application
from bokeh.server.server import Server
from bokeh.command.bootstrap import main as bokehserve

from tornado.ioloop import IOLoop
import os
import sys
import subprocess
from subprocess import PIPE
import shlex

class BokehServer(Thread):

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
