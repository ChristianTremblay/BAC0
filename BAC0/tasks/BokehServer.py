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

from bokeh.application import Application
from bokeh.server.server import Server
from tornado.ioloop import IOLoop
import os
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

    def launchWithoutConsole(self, command, args):
        #os.environ['__compat_layer'] = 'RUNASINVOKER'
        """Launches 'command' windowless and waits until finished"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen([command] + args, startupinfo=startupinfo).wait()

    def startProcess(self, commandToExecute):
        """
        c:\\JCI\\FXWorkbench-6.0\\bin\\wb.exe
        arg = "-profile:jciFxDriverAppliance:JciFullApplianceProfile -locale:fr"
         C:\JCI\FXWorkbench-6.0\bin\wb.exe
        """
        cmdargs = shlex.split(commandToExecute)
        print('Starting process : %s' % cmdargs)
        p = subprocess.Popen(cmdargs, stdout=PIPE, stderr=PIPE)
        output, errors = p.communicate()
        if p.returncode:
            return('Failed running %s' % commandToExecute)
            #raise Exception(errors)
        return output.decode('utf-8')
    
    def task(self):
        self.startProcess('C:\\Users\\ctremblay.SERVISYS\\AppData\\Local\\Continuum\\Anaconda3\\bs.bat')

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
