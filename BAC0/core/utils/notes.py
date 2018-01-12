# -*- coding: utf-8 -*-
"""
Notes object used in device and network

@author: CTremblay
"""
#--- standard Python modules ---
from collections import namedtuple
from datetime import datetime

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

        