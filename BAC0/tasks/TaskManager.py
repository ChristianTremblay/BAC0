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
from collections import deque
from random import random


# --- 3rd party modules ---
# --- this application's modules ---
from ..core.utils.notes import note_and_log
from ..core.io.IOExceptions import DeviceNotConnected

# ------------------------------------------------------------------------------


@note_and_log
class Manager:
    tasks = []
    manager = None
    enable = False

    def __init__(self):
        if not Manager.enable:
            self.start_service()

        self._log.debug("Task Manager Initiated")

    @classmethod
    def process(cls):
        task = None
        while cls.enable:
            try:
                if cls.tasks == []:
                    raise IndexError
                _temp = cls.tasks.copy()
                _temp.sort()
                if _temp[-1].next_execution <= time.time():
                    task = _temp.pop()
                    task.execute()
                    cls.tasks.remove(task.id)
                    task.previous_execution = time.time()
                    if task.delay > 0:
                        task.next_execution = task.previous_execution + task.delay
                        cls.schedule_task(task)

                    cls._log.debug(
                        "Task {} | {} executed. {}".format(task.id, task.name, task)
                    )
            except IndexError:
                cls._log.debug("Task Manager waiting for tasks...")
                time.sleep(1)
            except DeviceNotConnected as error:
                cls._log.warning(
                    "Device disconnected. Removing task ({}).".format(error, task)
                )
                cls.tasks.remove(task.id)
            except Exception as error:
                cls._log.error(
                    "Super Mega Giga big error {}. Removing task.".format(error)
                )
                cls.tasks.remove(task.id)
            else:
                if not cls.manager.is_alive() and cls.enable:
                    cls._log.error(
                        "TaskManager Thread stopped... This is not normal..."
                    )
                    cls.stop_service()
                    cls.start_service()
            time.sleep(0.01)
        cls.stop_service()

    @classmethod
    def schedule_task(cls, task):
        cls.tasks.append(task)

    @classmethod
    def stopAllTasks(cls):
        cls._log.info("Stopping all tasks")
        cls.enable = False
        while cls.manager.is_alive():
            time.sleep(0.01)

        cls._log.info("Ok all tasks stopped")
        cls.clean_tasklist()
        return True

    @classmethod
    def start_service(cls):
        cls._log.info("Starting TaskManager")
        cls.enable = True
        cls.manager = Thread(target=cls.process, daemon=True)
        cls.manager.start()

    @classmethod
    def stop_service(cls):
        cls._log.info("Stopping TaskManager")
        cls.enable = False
        # time.sleep(1)
        # cls.manager.join()

    @classmethod
    def clean_tasklist(cls):
        cls._log.debug("Cleaning tasks list")
        cls.tasks = []

    def __repr__(self):
        return "TaskManager"

    @classmethod
    def number_of_tasks(cls):
        return len(cls.tasks)


@note_and_log
class Task(object):
    _tasks = []

    def __init__(self, fn=None, name=None, delay=0):
        if not Manager.enable:
            _manager = Manager()
        # delay = 0 -> one shot
        if isinstance(fn, tuple):
            self.fn, self.args = fn
        else:
            self.fn = fn
            self.args = None
        self.name = name
        if delay > 0:
            self.delay = delay if delay >= 5 else 5
        else:
            self.delay = 0
        self.previous_execution = None
        self.average_execution_delay = 0
        self.average_latency = 0
        self.next_execution = time.time() + delay + (random() * 10)
        self.execution_time = 0
        self.count = 0
        self.id = id(self)
        self._kwargs = None
        Task._tasks.append(self)

    def task(self):
        raise NotImplementedError("Must be implemented")

    def execute(self):
        _start_time = time.time()
        self.count += 1
        self.average_latency = (
            self.average_latency + (_start_time - self.next_execution)
        ) / 2
        if self.fn and self.args is not None:
            self.fn(self.args)
        elif self.fn:
            self.fn()
        else:
            if self._kwargs is not None:
                self.task(self._kwargs)
            else:
                self.task()
        if self.previous_execution:
            _total = self.average_execution_delay + (
                _start_time - self.previous_execution
            )
            self.average_execution_delay = _total / 2
        else:
            self.average_execution_delay = self.delay

        # self._log.info('Stat for task {}'.format(self))
        if self.average_latency > 5:
            self._log.warning("High latency for {}".format(self.name))
            self._log.warning("Stats : {}".format(self))

        self._log.debug("Executing : {}".format(self.name))
        self.execution_time = time.time() - _start_time

    def start(self):
        Manager.schedule_task(task=self)

    def stop(self):
        self.delay = 0

    @property
    def last_time(self):
        return time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(self.previous_execution)
        )

    @property
    def next_time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.next_execution))

    @property
    def latency(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.average_latency))

    def is_alive(self):
        return

    def __repr__(self):
        return "{:<40} | Avg exec delay : {:.2f} sec | Avg latency : {:.2f} sec | last executed : {} | Next Time : {}".format(
            self.name,
            self.average_execution_delay,
            self.average_latency,
            self.last_time,
            self.next_time,
        )

    def __lt__(self, other):
        # list sort use __lt__... little cheat to reverse list already
        return self.next_execution > other.next_execution

    def __eq__(self, other):
        # list remove use __eq__... so compare with id
        if isinstance(other, Task):
            return self.id == other.id
        else:
            return self.id == other


def stopAllTasks():
    return Manager.stopAllTasks()


@note_and_log
class OneShotTask(Task):
    def __init__(self, fn=None, args=None, name="Oneshot"):
        super().__init__(name=name, delay=0)
