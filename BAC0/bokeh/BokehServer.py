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
        #self.app = Application()
        #self.server = Server(Application(), io_loop= IOLoop(), extra_patterns=None, port=5006)
                
    def run(self):
        self.process()

    def process(self):
        # if self.started = True
        while not self.exitFlag:
            self.task()

    def startServer(self):
        if 'win' in sys.platform:
            commandToExecute = "bokeh.bat serve"
        else:
            commandToExecute = "bokeh serve"
        cmdargs = shlex.split(commandToExecute)
        #showDebug("EXECUTE BOKEH SERVE COMMAND '%s'" % cmdargs)
        p = subprocess.Popen(cmdargs, stdout=PIPE, stderr=PIPE)
        output, errors = p.communicate()
        if p.returncode:
            print('Failed running %s' % commandToExecute)
            raise Exception(errors)
        return output.decode('utf-8')
    
    def task(self):
        #self.startProcess('C:\\Users\\ctremblay.SERVISYS\\AppData\\Local\\Continuum\\Anaconda3\\bs.bat')
        try:
            self.startServer()
        except Exception:
            print('Bokeh server already running')
            self.exitFlag = True
        #bokehserve(['','serve'])

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
