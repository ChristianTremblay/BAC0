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
import random

class Global():
    taskList = [];
    threadLock = Lock()
# TODO : A task manager that could start a bunch of thread...or stop them...    
#class TaskManager():
#    
#    threads = []
#    
#    def __init__(self):
#        for each in taskList:
#            self.threads.append(Task())
#        
#    def run_tasks(self)
#        thread1 = repeat(1, "Thread-1",('2:5 analogInput 1 presentValue'),('2:5 analogInput 2 presentValue'),threadLock)
#        thread2 = repeat(2, "Thread-2",('2:5 analogInput 3 presentValue'),('2:5 analogInput 4 presentValue'),threadLock)
#    
#        # Start new Threads
#        thread1.start()
#        thread2.start()

class Task(Thread):
    def __init__(self, delay = 5):
        Thread.__init__(self)
        self.exitFlag = False
        self.lock = Global.threadLock
        self.delay = delay
    
    def run(self):
        # Get lock to synchronize threads
        print("Starting " + self.name)
        #print_time(self.name)
        self.process()
        try:
            self.lock.release()
        except RuntimeError:
            pass
        Global.numberOfThreads -= 1
        self.beforeStop()
        print("Exiting " + self.name)
    
    def process(self):
        #if self.started = True
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
        

        


