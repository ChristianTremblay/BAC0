#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
RecurringTask.py - execute a recurring task
"""

import asyncio
import functools
import inspect
from typing import Any, Callable, Coroutine, Tuple, Union

from ..core.utils.notes import note_and_log
from .TaskManager import Task


@note_and_log
class RecurringTask(Task):
    """
    Start a recurring task (a function passed)
    """

    def __init__(
        self,
        fnc: Union[Tuple[Callable, Any], Callable, Coroutine],
        delay: Union[int, float] = 60,
        name: str = "recurring",
        minimum_delay: Union[int, float] = 5,
    ) -> None:
        """
        :param fnc: a function or a tuple (function, args)
        :param delay: (int) Delay between reads executions

        :returns: Nothing
        """
        self.fnc_args = None
        self.delay = delay
        if isinstance(fnc, tuple):
            self.func, self.fnc_args = fnc
        elif hasattr(fnc, "__call__"):
            self.func = fnc
        else:
            raise ValueError(
                "You must pass a function or a tuple (function,args) to this..."
            )
        Task.__init__(self, name=name, delay=delay, minimum_delay=minimum_delay)

    async def task(self) -> None:
        # Prefer awaiting async callables; offload sync callables with to_thread.
        def _is_async_callable(fn: Callable) -> bool:
            if inspect.iscoroutinefunction(fn):
                return True
            call = getattr(fn, "__call__", None)
            if call and inspect.iscoroutinefunction(call):
                return True
            if isinstance(fn, functools.partial):
                return _is_async_callable(fn.func)
            return False

        if self.fnc_args is not None:
            if _is_async_callable(self.func):
                await self.func(self.fnc_args)
            else:
                try:
                    await asyncio.to_thread(self.func, self.fnc_args)
                except (RuntimeError, AttributeError):
                    # Fallback for environments without to_thread or loop quirks
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, self.func, self.fnc_args)
        else:
            if _is_async_callable(self.func):
                await self.func()
            else:
                try:
                    await asyncio.to_thread(self.func)
                except (RuntimeError, AttributeError):
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, self.func)
