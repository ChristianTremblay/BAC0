#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
TaskManager.py - creation of threads used for repetitive tasks.  

A key building block for point simulation.
"""
# --- standard Python modules ---
from threading import Thread, Lock
import time

# --- 3rd party modules ---
# --- this application's modules ---
from ..core.utils.notes import note_and_log

# ------------------------------------------------------------------------------


class Manager:
    taskList = []
    threadLock = Lock()


def stopAllTasks():
    for each in Manager.taskList:
        each.exitFlag = True
    while True:
        _alive = [each.is_alive() for each in Manager.taskList]
        if not any(_alive):
            clean_tasklist()
            break
    return True


def clean_tasklist():
    for each in Manager.taskList:
        if not each.is_alive():
            Manager.taskList.remove(each)


@note_and_log
class Task(Thread):
    def __init__(self, delay=5, daemon=True, name="recurring"):
        Thread.__init__(self, name=name, daemon=daemon)
        self.is_running = False
        self.exitFlag = False
        self.lock = Manager.threadLock
        self.delay = delay
        if self.name not in Manager.taskList:
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
            for _ in range(self.delay * 2):
                if self.exitFlag:
                    break
                time.sleep(0.5)
            clean_tasklist()

    def task(self):
        raise RuntimeError("task must be overridden")

    def stop(self):
        self.is_running = False
        self.exitFlag = True
        clean_tasklist()

    def beforeStop(self):
        """
        Action done when closing thread
        """
        if self in Manager.taskList:
            Manager.taskList.remove(self)


@note_and_log
class OneShotTask(Thread):
    def __init__(self, daemon=True, name="Oneshot"):
        Thread.__init__(self, name=name, daemon=daemon)
        self.lock = Manager.threadLock
        if self.name not in Manager.taskList:
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
