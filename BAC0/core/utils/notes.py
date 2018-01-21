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
    cls._notes = namedtuple('_notes',['timestamp', 'notes'])
    cls._notes.timestamp = []
    cls._notes.notes = []
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
    
    def add_note(self, note='', level=logging.INFO):
        cls._notes.timestamp.append(datetime.now())
        cls._notes.notes.append(note)
        cls._log.log(level, note)
    
    def get_notes(self):
        return pd.Series(self._notes.notes, index=self._notes.timestamp)

    cls.add_note = add_note
    cls.get_notes = get_notes
    return cls
