#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
RecurringTask.py - execute a recurring task
"""

from typing import Any, Callable, Tuple, Union

from ..core.utils.notes import note_and_log
from .TaskManager import Task


@note_and_log
class RecurringTask(Task):
    """
    Start a recurring task (a function passed)
    """

    def __init__(
        self,
        fnc: Union[Tuple[Callable, Any], Callable],
        delay: int = 60,
        name: str = "recurring",
    ) -> None:
        """
        :param fnc: a function or a tuple (function, args)
        :param delay: (int) Delay between reads executions

        :returns: Nothing
        """
        self.fnc_args = None
        if isinstance(fnc, tuple):
            self.func, self.fnc_args = fnc
        elif hasattr(fnc, "__call__"):
            self.func = fnc
        else:
            raise ValueError(
                "You must pass a function or a tuple (function,args) to this..."
            )
        Task.__init__(self, name=name, delay=delay)

    def task(self) -> None:
        if self.fnc_args:
            self.func(self.fnc_args)
        else:
            self.func()
