#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This will start the Bokeh Server
"""
from threading import Thread
import weakref
from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from ..core.utils.notes import note_and_log


@note_and_log
class Bokeh_Worker(Thread):

    # Init thread running server
    def __init__(self, dev_app, trends_app, notes_app, serverIP, *, daemon=True):
        Thread.__init__(self, daemon=daemon)
        self._dev_app_ref = weakref.ref(dev_app)
        self._trends_app_ref = weakref.ref(trends_app)
        self._notes_app_ref = weakref.ref(notes_app)
        self.IP = serverIP
        self.exitFlag = False

    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def startServer(self):
        self.server = Server(
            {
                "/devices": self._dev_app_ref(),
                "/trends": self._trends_app_ref(),
                "/notes": self._notes_app_ref(),
            },
            io_loop=IOLoop(),
            allow_websocket_origin=[
                "{}:8111".format(self.IP),
                "{}:5006".format(self.IP),
                "{}:8111".format("localhost"),
                "{}:5006".format("localhost"),
            ],
        )
        self.server.start()
        self.server.io_loop.start()

    def task(self):
        try:
            self.startServer()
        except Exception as err:
            self._log.warning("Bokeh server already running", err)
            self.exitFlag = True

    def stop(self):
        self.bokeh_server.stop()
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
