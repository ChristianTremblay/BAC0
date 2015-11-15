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
from threading import Thread, Lock
import time


class Manager():
    taskList = []
    threadLock = Lock()


def stopAllTasks():
    for each in Manager.taskList:
        each.exitFlag = True
    print('Stopping all threads')


class Task(Thread):

    def __init__(self, delay=5, daemon = True):
        Thread.__init__(self, daemon = daemon)
        self.exitFlag = False
        self.lock = Manager.threadLock
        self.delay = delay
        if not self.name in Manager.taskList:
            Manager.taskList.append(self)

    def run(self):
        self.process()
        if self.lock.release():
            print('Task too fast...slow down, last call not finisehd yet...')
        else:
            try:
                self.lock.release()
            except RuntimeError:
                pass
            self.beforeStop()
            if self in Manager.taskList:
                Manager.taskList.remove(self)

    def process(self):
        # if self.started = True
        while not self.exitFlag:
            self.lock.acquire()
            self.task()
            self.lock.release()
            time.sleep(self.delay)

    def task(self):
        raise RuntimeError("task must be overridden")

    def stop(self):
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
