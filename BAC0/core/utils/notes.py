# -*- coding: utf-8 -*-
"""
Notes and logger decorator to be used on class
This will add a "notes" object to the class and will allow
logging feature at the same time.
Goal is to be able to access quickly to important informations for
the web interface.
"""
#--- standard Python modules ---
from collections import namedtuple
from datetime import datetime
import logging
from logging import FileHandler
import sys

import os
from os.path import expanduser, join

#--- 3rd party modules ---
try:
    import pandas as pd
    _PANDAS = True
except ImportError:
    _PANDAS = False

def convert_level(level):
    if not level:
        return None
    if level.lower() == 'info':
        level = logging.INFO
    elif level.lower() == 'debug':
        level = logging.DEBUG
    elif level.lower() == 'warning':
        level = logging.WARNING
    elif level.lower() == 'error':
        level = logging.ERROR
    elif level.lower() == 'critical':
        level = logging.CRITICAL
    return level

def update_log_level(level=None,*,file=None, stderr = None, stdout = None):
    """
    Typical usage : 
        Normal
        BAC0.log_level(file='warning', stdout='warning', stderr='error')
        Info on console....but not in file
        BAC0.log_level(file='warning', stdout='info', stderr='error')
        Debug
        BAC0.log_level(file='debug', stdout='info', stderr='error')
    """
    if level:
        file = level
        stderr = level
        stdout = level
    file = convert_level(file)
    stderr = convert_level(stderr)
    stdout = convert_level(stdout)       
    BAC0_logger = logging.getLogger('BAC0')
#    if console:
#        BAC0_logger.setLevel(console)
#        BAC0_logger.warning('Changed log level of console to {}'.format(logging.getLevelName(level)))

    for handler in BAC0_logger.handlers:
        if file and handler.get_name() == 'file_handler':
            handler.setLevel(file)
            BAC0_logger.info('Changed log level of file to {}'.format(logging.getLevelName(file)))
        elif stdout and handler.get_name() == 'stdout':
            handler.setLevel(stdout)
            BAC0_logger.info('Changed log level of console stdout to {}'.format(logging.getLevelName(stdout)))
        elif stderr and handler.get_name() == 'stderr':
            handler.setLevel(stderr)
            BAC0_logger.info('Changed log level of console stderr to {}'.format(logging.getLevelName(stderr)))


def note_and_log(cls):
    """
    This will be used as a decorator on class to activate
    logging and store messages in the variable cls._notes
    This will allow quick access to events in the web app.
    A note can be added to cls._notes without logging if passing
    the argument log=false to function note()
    Something can be logged without addind a note using function log()
    """
    if hasattr(cls, 'DEBUG_LEVEL'):
        if cls.DEBUG_LEVEL == 'debug':
            file_level = logging.DEBUG
            console_level = logging.DEBUG
        elif cls.DEBUG_LEVEL == 'info':
            file_level = logging.INFO
            console_level = logging.INFO
    else:
        file_level = logging.WARNING
        console_level = logging.INFO
    # Notes object
    cls._notes = namedtuple('_notes', ['timestamp', 'notes'])
    cls._notes.timestamp = []
    cls._notes.notes = []

    # Defining log object
    cls.logname = '{} | {}'.format(cls.__module__, cls.__name__)
    root_logger = logging.getLogger()
    cls._log = logging.getLogger('BAC0')
    if not len(root_logger.handlers):
        root_logger.addHandler(cls._log)

    # Console Handler
    ch = logging.StreamHandler()
    ch.set_name('stderr')
    ch2 = logging.StreamHandler(sys.stdout)
    ch2.set_name('stdout')
    ch.setLevel(console_level)
    ch2.setLevel(logging.CRITICAL)

    formatter = logging.Formatter(
        '{asctime} - {levelname:<8}| {message}', style='{')

    # File Handler
    _PERMISSION_TO_WRITE = True
    logUserPath = expanduser('~')
    logSaveFilePath = join(logUserPath, '.BAC0')

    logFile = join(logSaveFilePath, 'BAC0.log')
    if not os.path.exists(logSaveFilePath):
        try:
            os.makedirs(logSaveFilePath)
        except:
            _PERMISSION_TO_WRITE = False
    if _PERMISSION_TO_WRITE:
        fh = FileHandler(logFile)
        fh.set_name('file_handler')
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

#    cls._log.setLevel(logging.CRITICAL)

    def log_title(self, title, args=None, width=35):
        cls._log.debug("")
        cls._log.debug("#"*width)
        cls._log.debug("# {}".format(title))
        cls._log.debug("#"*width)
        if args:
            cls._log.debug("{!r}".format(args))
            cls._log.debug("#"*35)

    def log_subtitle(self, subtitle, args=None, width=35):
        cls._log.debug("")
        cls._log.debug("="*width)
        cls._log.debug("{}".format(subtitle))
        cls._log.debug("="*width)
        if args:
            cls._log.debug("{!r}".format(args))
            cls._log.debug("="*width)

    def log(self, note, *, level=logging.DEBUG):
        """
        Add a log entry...no note
        """
        if not note:
            raise ValueError('Provide something to log')
        note = '{} | {}'.format(cls.logname, note)
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
            raise ValueError('Provide something to log')
        note = '{} | {}'.format(cls.logname, note)
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
