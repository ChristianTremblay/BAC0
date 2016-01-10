#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module will call the loop until closed method on the session.
"""
from threading import Thread

import weakref

class BokehLoopUntilClosed(Thread):
    #figures = {}
    _instances = set()

    # Init thread running server
    def __init__(self, session, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.exitFlag = False
        self.session = session
        
        for obj in BokehLoopUntilClosed.getinstances():
            if obj.session.id == self.session.id:
                obj.stop()
                del obj
        #clean instances
        list(self.getinstances())

        self._instances.add(weakref.ref(self)) 
         
    @classmethod
    def getinstances(cls):
        dead = set()
        for ref in cls._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        cls._instances -= dead
        
    def run(self):
        self.process()

    def process(self):
        while not self.exitFlag:
            self.task()

    def task(self):
        self.session.loop_until_closed()       

    def stop(self):
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
