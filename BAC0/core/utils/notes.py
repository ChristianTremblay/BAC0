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
from logging.handlers import RotatingFileHandler

import os
from os.path import expanduser

#--- 3rd party modules ---
try:
    import pandas as pd
    _PANDAS = True
except ImportError:
    _PANDAS = False

def note_and_log(cls):
    """
    This will be used as a decorator on class to activate
    logging and store messages in the variable cls._notes
    This will allow quick access to events in the web app.

    A note can be added to cls._notes without logging if passing
    the argument log=false to function note()
    Something can be logged without addind a note using function log()
    """
    # Notes object
    cls._notes = namedtuple('_notes',['timestamp', 'notes'])
    cls._notes.timestamp = []
    cls._notes.notes = []

    # Defining log object
    logname = '%s | %s' % (cls.__module__, cls.__name__)
    cls._log = logging.getLogger(logname)
    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # Rotating File Handler
    logUserPath = expanduser('~')
    logSaveFilePath = r'%s\.BAC0' %(logUserPath)

    logFile = r'%s\%s' (logSaveFilePath,'BAC0.log')
    if not os.path.exists(logSaveFilePath):
        os.makedirs(logSaveFilePath)
    fh = RotatingFileHandler(logFile, mode='a', maxBytes=1000000, backupCount=1, encoding=None, delay=False)
    fh.setLevel = logging.DEBUG
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # Add handlers the first time only... 
    if not len(cls._log.handlers):
        cls._log.addHandler(fh)
        cls._log.addHandler(ch)
    
    def log(self, note,*, level=logging.DEBUG):
        """
        Add a log entry...no note
        """
        if not note:
            raise ValueError('Provide something to log')
        cls._log.log(level, note)
    
    def note(self, note,*, level=logging.INFO, log=True):
        """
        Add note to the object. By default, the note will also
        be logged

        :param note: (str) The note itself
        :param level: (logging.level)
        :param log: (boolean) Enable or disable logging of note
        """
        if not note:
            raise ValueError('Provide something to log')
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
            return dict(zip(self._notes.timestamp,self._notes.notes))
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
    return cls
