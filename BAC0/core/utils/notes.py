# -*- coding: utf-8 -*-
"""
Notes and logger decorator to be used on class
This will add a "notes" object to the class and will allow
logging feature at the same time.
Goal is to be able to access quickly to important informations for
the web interface.
"""
# --- standard Python modules ---
from collections import namedtuple
from datetime import datetime
import logging
from logging import FileHandler
import sys

import os
from os.path import expanduser, join

# --- 3rd party modules ---
try:
    import pandas as pd

    _PANDAS = True
except ImportError:
    _PANDAS = False


class LogList:
    LOGGERS = []


def convert_level(level):
    if not level:
        return None
    _valid_levels = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]
    if level in _valid_levels:
        return level
    if level.lower() == "info":
        return logging.INFO
    elif level.lower() == "debug":
        return logging.DEBUG
    elif level.lower() == "warning":
        return logging.WARNING
    elif level.lower() == "error":
        return logging.ERROR
    elif level.lower() == "critical":
        return logging.CRITICAL
    raise ValueError(
        "Wrong log level use one of the following : {}".format(_valid_levels)
    )


def update_log_level(
    level=None, *, log_file=None, stderr=None, stdout=None, log_this=True
):
    """
    Typical usage ::
        # Silence (use CRITICAL so not much messages will be sent)
        BAC0.log_level('silence')
        # Verbose
        BAC0.log_level('info')
        # Default, Info on console....but Warning in file
        BAC0.log_level(file='warning', stdout='info', stderr='critical')
        # Debug in file and console... this is a bad idea as the console will be filled
        BAC0.log_level(file='debug', stdout='debug', stderr='critical')
           
        # Preferably, debug in the file, keep console limited to info
        BAC0.log_level('debug')
        # OR
        BAC0.log_level(file='debug', stdout='info', stderr='critical')   
        

    Giving only one parameter will set file and console to the same level.
    I tend to keep stderr CRITICAL
     
    """
    update_log_file_lvl = False
    update_stderr_lvl = False
    update_stdout_lvl = False

    if level:
        logging.getLogger("BAC0_Root.BAC0.scripts.Base.Base").disabled = False
        if level.lower() == "silence":
            log_file_lvl = logging.CRITICAL
            stderr_lvl = logging.CRITICAL
            stdout_lvl = logging.CRITICAL
            update_log_file_lvl = True
            update_stderr_lvl = True
            update_stdout_lvl = True
            logging.getLogger("BAC0_Root.BAC0.scripts.Base.Base").disabled = True
        elif level.lower() == "default":
            log_file_lvl = logging.WARNING
            stderr_lvl = logging.CRITICAL
            stdout_lvl = logging.INFO
            update_log_file_lvl = True
            update_stderr_lvl = True
            update_stdout_lvl = True
        elif level.lower() == "debug":
            log_file_lvl = logging.DEBUG
            stdout_lvl = logging.INFO
            update_log_file_lvl = True
            update_stdout_lvl = True
        else:
            level = convert_level(level)
            log_file_lvl = level
            stdout_lvl = level
            update_log_file_lvl = True
            update_stdout_lvl = True

    else:
        if log_file:
            log_file_lvl = convert_level(log_file)
            update_log_file_lvl = True
        if stderr:
            stderr_lvl = convert_level(stderr)
            update_stderr_lvl = True
        if stdout:
            stdout_lvl = convert_level(stdout)
            update_stdout_lvl = True

    # Choose Base as logger for this task
    if log_this:
        BAC0_logger = logging.getLogger("BAC0_Root.BAC0.scripts.Base.Base")

    for each in LogList.LOGGERS:
        for handler in each.handlers:
            if update_log_file_lvl and handler.get_name() == "file_handler":
                handler.setLevel(log_file_lvl)
                if log_this:
                    BAC0_logger.warning(
                        "Changed log level of file to {}".format(
                            logging.getLevelName(log_file_lvl)
                        )
                    )
            elif update_stdout_lvl and handler.get_name() == "stdout":
                handler.setLevel(stdout_lvl)
                if log_this:
                    BAC0_logger.warning(
                        "Changed log level of console stdout to {}".format(
                            logging.getLevelName(stdout_lvl)
                        )
                    )
            elif update_stderr_lvl and handler.get_name() == "stderr":
                handler.setLevel(stderr_lvl)
                if log_this:
                    BAC0_logger.warning(
                        "Changed log level of console stderr to {}".format(
                            logging.getLevelName(stderr_lvl)
                        )
                    )


def note_and_log(cls):
    """
    This will be used as a decorator on class to activate
    logging and store messages in the variable cls._notes
    This will allow quick access to events in the web app.
    A note can be added to cls._notes without logging if passing
    the argument log=false to function note()
    Something can be logged without addind a note using function log()
    """
    if hasattr(cls, "DEBUG_LEVEL"):
        if cls.DEBUG_LEVEL == "debug":
            file_level = logging.DEBUG
            console_level = logging.DEBUG
        elif cls.DEBUG_LEVEL == "info":
            file_level = logging.INFO
            console_level = logging.INFO
    else:
        file_level = logging.WARNING
        console_level = logging.INFO
    # Notes object
    cls._notes = namedtuple("_notes", ["timestamp", "notes"])
    cls._notes.timestamp = []
    cls._notes.notes = []

    # Defining log object
    cls.logname = "{} | {}".format(cls.__module__, cls.__name__)
    cls._log = logging.getLogger("BAC0_Root.{}.{}".format(cls.__module__, cls.__name__))

    # Set level to debug so filter is done by handler
    cls._log.setLevel(logging.DEBUG)

    # Console Handler
    ch = logging.StreamHandler(sys.stderr)
    ch.set_name("stderr")
    ch.setLevel(logging.CRITICAL)

    ch2 = logging.StreamHandler(sys.stdout)
    ch2.set_name("stdout")
    ch2.setLevel(console_level)

    formatter = logging.Formatter("{asctime} - {levelname:<8}| {message}", style="{")

    # File Handler
    _PERMISSION_TO_WRITE = True
    logUserPath = expanduser("~")
    logSaveFilePath = join(logUserPath, ".BAC0")

    logFile = join(logSaveFilePath, "BAC0.log")
    if not os.path.exists(logSaveFilePath):
        try:
            os.makedirs(logSaveFilePath)
        except:
            _PERMISSION_TO_WRITE = False
    if _PERMISSION_TO_WRITE:
        fh = FileHandler(logFile)
        fh.set_name("file_handler")
        fh.setLevel(file_level)
        fh.setFormatter(formatter)

    ch.setFormatter(formatter)
    ch2.setFormatter(formatter)
    # Add handlers the first time only...
    if not len(cls._log.handlers):
        if _PERMISSION_TO_WRITE:
            cls._log.addHandler(fh)
        cls._log.addHandler(ch)
        cls._log.addHandler(ch2)

    LogList.LOGGERS.append(cls._log)

    def log_title(self, title, args=None, width=35):
        cls._log.debug("")
        cls._log.debug("#" * width)
        cls._log.debug("# {}".format(title))
        cls._log.debug("#" * width)
        if args:
            cls._log.debug("{!r}".format(args))
            cls._log.debug("#" * 35)

    def log_subtitle(self, subtitle, args=None, width=35):
        cls._log.debug("")
        cls._log.debug("=" * width)
        cls._log.debug("{}".format(subtitle))
        cls._log.debug("=" * width)
        if args:
            cls._log.debug("{!r}".format(args))
            cls._log.debug("=" * width)

    def log(self, note, *, level=logging.DEBUG):
        """
        Add a log entry...no note
        """
        if not note:
            raise ValueError("Provide something to log")
        note = "{} | {}".format(cls.logname, note)
        cls._log.log(level, note)

    def note(self, note, *, level=logging.INFO, log=True):
        """
        Add note to the object. By default, the note will also
        be logged
        :param note: (str) The note itself
        :param level: (logging.level)
        :param log: (boolean) Enable or disable logging of note
        """
        if not note:
            raise ValueError("Provide something to log")
        note = "{} | {}".format(cls.logname, note)
        cls._notes.timestamp.append(datetime.now())
        cls._notes.notes.append(note)
        if log:
            cls.log(level, note)

    @property
    def notes(self):
        """
        Retrieve notes list as a Pandas Series
        """
        if not _PANDAS:
            return dict(zip(self._notes.timestamp, self._notes.notes))
        return pd.Series(self._notes.notes, index=self._notes.timestamp)

    def clear_notes(self):
        """
        Clear notes object
        """
        cls._notes.timestamp = []
        cls._notes.notes = []

    # Add the functions to the decorated class
    cls.clear_notes = clear_notes
    cls.note = note
    cls.notes = notes
    cls.log = log
    cls.log_title = log_title
    cls.log_subtitle = log_subtitle
    return cls
