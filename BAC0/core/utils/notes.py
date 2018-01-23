# -*- coding: utf-8 -*-
"""
Notes object used in device and network

@author: CTremblay
"""
#--- standard Python modules ---
from collections import namedtuple
from datetime import datetime
import logging

#--- 3rd party modules ---
import pandas as pd

class Notes():
    def __init__(self, init_note = None):
        if not init_note:
            raise ValueError('Provide initial note')
        self._notes = namedtuple('_notes',['timestamp', 'notes'])
        self._notes.timestamp = []
        self._notes.notes = []
        self._notes.notes.append(init_note)
        self._notes.timestamp.append(datetime.now())
        
    def add(self, note):
        self._notes.timestamp.append(datetime.now())
        self._notes.notes.append(note)

    def get_serie(self):
        notes_table = pd.Series(self._notes.notes, index=self._notes.timestamp)
        return notes_table  

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
    self.clear_notes()

    # Defining log object
    logname = 'BAC0'
    cls._log = logging.getLogger(logname)
    ch = logging.StreamHandler()
    ch.setLevel = logging.ERROR
    fh = logging.FileHandler('BAC0.log')
    fh.setLevel = logging.DEBUG
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    cls._log.addHandler(ch)
    cls._log.addHandler(fh)
    
    def note(self, note='', level=logging.INFO, log=True):
        """
        Add note to the object. By default, the note will also
        be logged

        :param note: (str) The note itself
        :param level: (logging.level)
        :param log: (boolean) Enable or disable logging of note
        """
        cls._notes.timestamp.append(datetime.now())
        cls._notes.notes.append(note)
        if log:
            self.log(level, note)

    def log(self, note='', level=logging.DEBUG):
        """
        Add a log entry...no note
        """
        cls._log.log(level, note)
    
    @property
    def notes(self):
        """
        Retrieve notes list as a Pandas Series
        """
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
    return cls
