#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
TaskManager.py - creation of threads used for repetitive tasks.  

A key building block for point simulation.
'''
#--- standard Python modules ---
from threading import Thread, Lock
import time

#--- 3rd party modules ---
#--- this application's modules ---

#------------------------------------------------------------------------------

class Manager():
    taskList = []
    threadLock = Lock()


def stopAllTasks():
    for each in Manager.taskList:
        each.exitFlag = True
    #print('Stopping all threads')


class Task(Thread):

    def __init__(self, delay=5, daemon = True, name='recurring'):
        Thread.__init__(self, name=name, daemon = daemon)
        self.is_running = False
        self.exitFlag = False
        self.lock = Manager.threadLock
        self.delay = delay
        if not self.name in Manager.taskList:
            Manager.taskList.append(self)


    def run(self):
        self.process()


    def process(self):
        self.is_running = True
        while not self.exitFlag:
            self.lock.acquire()
            self.task()
            self.lock.release()
            # This replace a single time.sleep
            # the goal is to speed up the stop
            # of the thread by providing an easy way out
            for i in range(self.delay * 2):
                if self.exitFlag:
                    break
                time.sleep(0.5)


    def task(self):
        raise RuntimeError("task must be overridden")


    def stop(self):
        self.is_running = False
        self.exitFlag = True


    def beforeStop(self):
        """
        Action done when closing thread
        """
        if self in Manager.taskList:
            Manager.taskList.remove(self)


class OneShotTask(Thread):

    def __init__(self, daemon = True,name='Oneshot'):
        Thread.__init__(self, name=name, daemon = daemon)
        self.lock = Manager.threadLock
        if not self.name in Manager.taskList:
            Manager.taskList.append(self)

    def run(self):
        self.process()

    def process(self):
        self.task()
            
    def task(self):
        raise RuntimeError("task must be overridden")

    def stop(self):
        pass

    def beforeStop(self):
        """
        Action done when closing thread
        """
        if self in Manager.taskList:
            Manager.taskList.remove(self)
