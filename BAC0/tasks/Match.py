#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Match.py - verify a point's status matches its commanded value.

Example:
    Is a fan commanded to 'On' actually 'running'?
"""

# --- standard Python modules ---
# --- 3rd party modules ---

# --- this application's modules ---
from .TaskManager import Task
from ..core.utils.notes import note_and_log

# ------------------------------------------------------------------------------


@note_and_log
class Match(Task):
    """
    Match two properties of a BACnet Object (i.e. a point status with its command).
    """

    def __init__(self, command=None, status=None, delay=5):
        self._log.debug(
            "Creating Match task for {} and {}. Delay : {}".format(
                command, status, delay
            )
        )
        self.command = command
        self.status = status
        Task.__init__(self, delay=delay, daemon=True)

    def task(self):
        try:
            if self.status.history[-1] != self.command.history[-1]:
                self.status._setitem(self.command.history[-1])
        except Exception:
            self._log.error(
                "Something wrong matching {} and {}... try again next time...".format(
                    self.command, self.status
                )
            )

    def stop(self):
        self.status._setitem("auto")
        self.exitFlag = True


@note_and_log
class Match_Value(Task):
    """
    Verify a point's Present_Value equals the given value after a delay of X seconds.
    Thus giving the BACnet controller (and connected equipment) time to respond to the
    command.
    
        Match_Value(On, <AI:1>, 5)
        
    i.e. Does Fan value = On after 5 seconds. 
    """

    def __init__(self, value=None, point=None, delay=5):
        self._log.debug("Creating MatchValue task for {} and {}".format(value, point))
        self.value = value
        self.point = point
        Task.__init__(self, delay=delay, daemon=True)

    def task(self):
        try:
            if hasattr(self.value, "__call__"):
                value = self.value()
            else:
                value = self.value
            if value != self.point.value:
                self.point._set(value)
        except Exception:
            self._log.error(
                "Something is wrong matching {} and {}... try again next time".format(
                    self.value, self.point
                )
            )

    def stop(self):
        self.point._set("auto")
        self.exitFlag = True
