#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
Points.py - Definition of points so operations on Read results are more convenient.
'''

#--- standard Python modules ---
from datetime import datetime
from collections import namedtuple
import time

#--- 3rd party modules ---
try:
    import pandas as pd
    from pandas.io import sql
    try:
        from pandas import Timestamp
    except ImportError:
        from pandas.lib import Timestamp
    _PANDAS = True
except ImportError:
    _PANDAS = False

#--- this application's modules ---
from ...tasks.Poll import SimplePoll as Poll
from ...tasks.Match import Match, Match_Value
from ..io.IOExceptions import NoResponseFromController, UnknownPropertyError
from ..utils.notes import note_and_log


#------------------------------------------------------------------------------


class PointProperties(object):
    """
    A container for point properties.
    """

    def __init__(self):
        self.device = None
        self.name = None
        self.type = None
        self.address = None
        self.description = None
        self.units_state = None
        self.simulated = (False, None)
        self.overridden = (False, None)
        self.priority_array = None
        self.history_size = None

    def __repr__(self):
        return '%s' % self.asdict

    @property
    def asdict(self):
        return self.__dict__

#------------------------------------------------------------------------------

@note_and_log
class Point():
    """
    Represents a device BACnet point.  Used to NumericPoint, BooleanPoint and EnumPoints.

    Each point implements a history feature. Each time the point is read, its value (with timestamp)
    is added to a history table. Histories capture the changes to point values over time.
    """

    def __init__(self, device=None,
                 pointType=None,    pointAddress=None,  pointName=None,
                 description=None,  presentValue=None,  units_state=None,
                 history_size=None):

        self._history = namedtuple('_history', ['timestamp', 'value'])
        self.properties = PointProperties()

        self._polling_task = namedtuple('_polling_task', ['task', 'running'])
        self._polling_task.task = None
        self._polling_task.running = False

        self._match_task = namedtuple('_match_task', ['task', 'running'])
        self._match_task.task = None
        self._match_task.running = False

        self._history.timestamp = []
        self._history.value = []
        self._history.value.append(presentValue)
        self._history.timestamp.append(datetime.now())
        self.history_size = history_size

        self.properties.device = device
        self.properties.name = pointName
        self.properties.type = pointType
        self.properties.address = pointAddress

        self.properties.description = description
        self.properties.units_state = units_state
        self.properties.simulated = (False, 0)
        self.properties.overridden = (False, 0)

    @property
    def value(self):
        """
        Retrieve value of the point
        """
        try:
            res = self.properties.device.properties.network.read('{} {} {} presentValue'.format(
                self.properties.device.properties.address, self.properties.type, str(self.properties.address)))
            self._trend(res)
        except Exception:
            raise Exception(
                'Problem reading : {}'.format(self.properties.name))

        return res
    
    def read_priority_array(self):
        """
        Retrieve priority array of the point
        """
        if self.properties.priority_array != False:
            try:
                res = self.properties.device.properties.network.read('{} {} {} priorityArray'.format(
                    self.properties.device.properties.address, self.properties.type, str(self.properties.address)))
                self.properties.priority_array = res
            except (ValueError, UnknownPropertyError):
                self.properties.priority_array = False
            except Exception:
                raise Exception(
                    'Problem reading : {}'.format(self.properties.name))
   
    
    @property
    def is_overridden(self):
        self.read_priority_array()  
        if self.properties.priority_array == False:
            return False      
        if self.priority(8) or self.priority(1):
            self.properties.overridden = (True, self.value)
            return True
        else:
            return False
   
    def priority(self, priority=None):
        if self.properties.priority_array == False:
            return None

        self.read_priority_array()
        if not priority:
            return self.properties.priority_array.debug_contents()
        if priority < 1 or priority > 16:
            raise IndexError('Please provide priority to read (1-16)')

        else:
            pa = self.properties.priority_array.value[priority]
            try:
                key, value = zip(*pa.dict_contents().items())
                if key[0] == 'null':
                    return None
                else:
                    return (key[0], value[0])
            except ValueError:
                return None

    def _trend(self, res):
        self._history.timestamp.append(datetime.now())
        self._history.value.append(res)
        if self.properties.history_size == None:
            return
        else:
            if self.properties.history_size < 1:
                self.properties.history_size = 1
            if len(self._history.timestamp) >= self.properties.history_size:
                try:
                    self._history.timestamp = self._history.timestamp[-self.properties.history_size:]
                    self._history.value = self._history.value[-self.properties.history_size:]
                    assert len(self._history.timestamp) == len(self._history.value)
                except Exception as e:
                    self._log.exception("Can't append to history")

    @property
    def units(self):
        """
        Should return units
        """
        raise Exception('Must be overridden')

    @property
    def lastValue(self):
        """
        returns: last value read
        """
        if _PANDAS:
            return self.history.dropna().iloc[-1]
        else:
            return self._history.value[-1]

    @property
    def history(self):
        """
        returns : (pd.Series) containing timestamp and value of all readings
        """
        if not _PANDAS:
            return dict(zip(self._history.timestamp, self._history.value))
        his_table = pd.Series(self._history.value[:len(self._history.timestamp)],
                              index=self._history.timestamp)
        his_table.name = (
            '{}/{}').format(self.properties.device.properties.name, self.properties.name)
        his_table.units = self.properties.units_state
        if self.properties.name in self.properties.device.binary_states:
            his_table.states = 'binary'
        elif self.properties.name in self.properties.device.multi_states:
            his_table.states = 'multistates'
        else:
            his_table.states = 'analog'
        his_table.description = self.properties.description

        his_table.datatype = self.properties.type
        return his_table

    def clear_history(self):
        self._history.timestamp = []
        self._history.value = []

    def chart(self, remove=False):
        """
        Add point to the bacnet trending list
        """
        if remove:
            self.properties.device.properties.network.remove_trend(self)
        else:
            self.properties.device.properties.network.add_trend(self)

    def __getitem__(self, key):
        """
        Way to get points... presentValue, status, flags, etc...

        :param key: state
        :returns: list of enum states
        """
        if str(key).lower() in ['unit', 'units', 'state', 'states']:
            key = 'units_state'
        try:
            return getattr(self.properties, key)
        except AttributeError:
            raise ValueError('Wrong property')

    def write(self, value, *, prop='presentValue', priority=''):
        """
        Write to present value of a point

        :param value: (float) numeric value
        :param prop: (str) property to write. Default = presentValue
        :param priority: (int) priority to which write.

        """
        if priority != '':
            if isinstance(float(priority), float)\
                    and float(priority) >= 1\
                    and float(priority) <= 16:
                priority = '- {}'.format(priority)
            else:
                raise ValueError('Priority must be a number between 1 and 16')

        try:
            self.properties.device.properties.network.write(
                '{} {} {} {} {} {}'.format(
                    self.properties.device.properties.address,
                    self.properties.type,
                    self.properties.address,
                    prop,
                    value,
                    priority))
        except Exception:
            raise NoResponseFromController()

        # Read after the write so history gets updated.
        self.value

    def default(self, value):
        self.write(value, prop='relinquishDefault')

    def sim(self, value, *, force=False):
        """
        Simulate a value.  Sets the Out_Of_Service property- to disconnect the point from the
        controller's control.  Then writes to the Present_Value.
        The point name is added to the list of simulated points (self.simPoints)

        :param value: (float) value to simulate
        """
        if self.properties.simulated[0] \
                and self.properties.simulated[1] == value \
                and force == False:
            pass
        else:
            self.properties.device.properties.network.sim('{} {} {} presentValue {}'.format(
                self.properties.device.properties.address, self.properties.type, str(self.properties.address), str(value)))
            self.properties.simulated = (True, value)

    def out_of_service(self):
        """
        Sets the Out_Of_Service property [to True].
        """
        self.properties.device.properties.network.out_of_service('{} {} {}'.format(
            self.properties.device.properties.address, self.properties.type, str(self.properties.address)))
        self.properties.simulated = (True, None)

    def release(self):
        """
        Clears the Out_Of_Service property [to False] - so the controller regains control of the point.
        """
        self.properties.device.properties.network.release('{} {} {}'.format(
            self.properties.device.properties.address, self.properties.type, str(self.properties.address)))
        self.properties.simulated = (False, None)

    def ovr(self, value):
        self.write(value, priority=8)
        self.properties.overridden = (True, value)

    def auto(self):
        self.write('null', priority=8)
        self.properties.overridden = (False, 0)

    def release_ovr(self):
        self.write('null', priority=1)
        self.write('null', priority=8)
        self.properties.overridden = (False, None)

    def _setitem(self, value):
        """
        Called by _set, will trigger right function depending on
        point type to write to the value and make tests.
        This is default behaviour of the point  :
        AnalogValue are written to
        AnalogOutput are overridden
        """
        if 'Value' in self.properties.type:
            if str(value).lower() == 'auto':
                raise ValueError(
                    'Value was not simulated or overridden, cannot release to auto')
            # analog value must be written to
            self.write(value)

        elif 'Output' in self.properties.type:
            # analog output must be overridden
            if str(value).lower() == 'auto':
                self.auto()
            else:
                self.ovr(value)
        else:
            # input are left... must be simulated
            if str(value).lower() == 'auto':
                self.release()
            else:
                self.sim(value)

    def _set(self, value):
        """
        Allows the syntax:
            device['point'] = value
        """
        raise Exception('Must be overridden')

    def poll(self, command='start', *, delay=10):
        """
        Poll a point every x seconds (delay=x sec)
        Stopped by using point.poll('stop') or .poll(0) or .poll(False)
        or by setting a delay = 0
        """
        if str(command).lower() == 'stop' \
                or command == False \
                or command == 0 \
                or delay == 0:

            if isinstance(self._polling_task.task, Poll):
                self._polling_task.task.stop()
                self._polling_task.task = None
                self._polling_task.running = False

        elif self._polling_task.task is None:
            self._polling_task.task = Poll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True

        elif self._polling_task.running:
            self._polling_task.task.stop()
            self._polling_task.running = False
            self._polling_task.task = Poll(self, delay=delay)
            self._polling_task.task.start()
            self._polling_task.running = True

        else:
            raise RuntimeError('Stop polling before redefining it')

    def match(self, point, *, delay=5):
        """
        This allow functions like :
            device['status'].match('command')

        A fan status for example will follow the command...
        """
        if self._match_task.task is None:
            self._match_task.task = Match(
                command=point, status=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay > 0:
            self._match_task.task.stop()
            self._match_task.running = False
            time.sleep(1)

            self._match_task.task = Match(
                command=point, status=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay == 0:
            self._match_task.task.stop()
            self._match_task.running = False

        else:
            raise RuntimeError('Stop task before redefining it')

    def match_value(self, value, *, delay=5):
        """
        This allow functions like :
            device['point'].match('value')

        A sensor will follow a calculation...
        """
        if self._match_task.task is None:
            self._match_task.task = Match_Value(
                value=value, point=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay > 0:
            self._match_task.task.stop()
            self._match_task.running = False
            time.sleep(1)

            self._match_task.task = Match_Value(
                value=value, point=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay == 0:
            self._match_task.task.stop()
            self._match_task.running = False

        else:
            raise RuntimeError('Stop task before redefining it')

    def __len__(self):
        """
        Length of a point = # of history records
        """
        return len(self.history)


#------------------------------------------------------------------------------

class NumericPoint(Point):
    """
    Representation of a Numeric value
    """

    def __init__(self, device=None,
                 pointType=None,    pointAddress=None,  pointName=None,
                 description=None,  presentValue=None,  units_state=None,
                 history_size=None):

        Point.__init__(self, device=device,
                       pointType=pointType,     pointAddress=pointAddress,  pointName=pointName,
                       description=description, presentValue=presentValue,  units_state=units_state,
                       history_size=history_size)

    @property
    def units(self):
        return self.properties.units_state

    def _set(self, value):
        if str(value).lower() == 'auto':
            self._setitem(value)
        else:
            try:
                if isinstance(value, Point):
                    value = value.lastValue
                val = float(value)
                if isinstance(val, float):
                    self._setitem(value)
            except:
                raise ValueError('Value must be numeric')

    def __repr__(self):
        return '{}/{} : {:.2f} {}'.format(self.properties.device.properties.name, self.properties.name, self.value, self.properties.units_state)

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __lt__(self, other):
        return self.value < other

    def __le__(self, other):
        return self.value <= other

    def __eq__(self, other):
        return self.value == other

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other

#------------------------------------------------------------------------------


class BooleanPoint(Point):
    """
    Representation of a Boolean value
    """

    def __init__(self, device=None,
                 pointType=None,    pointAddress=None,  pointName=None,
                 description=None,  presentValue=None,  units_state=None,
                 history_size=None):

        Point.__init__(self, device=device,
                       pointType=pointType,     pointAddress=pointAddress,  pointName=pointName,
                       description=description, presentValue=presentValue,  units_state=units_state,
                       history_size=history_size)

    @property
    def value(self):
        """
        Read the value from BACnet network
        """
        try:
            res = self.properties.device.properties.network.read('{} {} {} presentValue'.format(
                self.properties.device.properties.address, self.properties.type, str(self.properties.address)))
            self._trend(res)

        except Exception:
            raise Exception(
                'Problem reading : {}'.format(self.properties.name))

        if res == 'inactive':
            self._key = 0
            self._boolKey = False
        else:
            self._key = 1
            self._boolKey = True
        return res

    @property
    def boolValue(self):
        """
        returns : (boolean) Value
        """
        if self.lastValue == 1 or self.lastValue == 'active':
            self._key = 1
            self._boolKey = True
        else:
            self._key = 0
            self._boolKey = False
        return self._boolKey

    @property
    def units(self):
        """
        Boolean points don't have units
        """
        return None

    def _set(self, value):
        if value == True:
            self._setitem('active')
        elif value == False:
            self._setitem('inactive')
        elif str(value) in ['inactive', 'active'] or str(value).lower() == 'auto':
            self._setitem(value)
        else:
            raise ValueError(
                'Value must be boolean True, False or "active"/"inactive"')

    def __repr__(self):
        return '{}/{} : {}'.format(self.properties.device.properties.name, self.properties.name, self.boolValue)

    def __or__(self, other):
        return self.boolValue | other

    def __and__(self, other):
        return self.boolValue & other

    def __xor__(self, other):
        return self.boolValue ^ other

    def __eq__(self, other):
        return self.boolValue == other

#------------------------------------------------------------------------------


class EnumPoint(Point):
    """
    Representation of an Enumerated (multiState) value
    """

    def __init__(self, device=None,
                 pointType=None,    pointAddress=None,  pointName=None,
                 description=None,  presentValue=None,  units_state=None,
                 history_size=None):

        Point.__init__(self, device=device,
                       pointType=pointType,     pointAddress=pointAddress,  pointName=pointName,
                       description=description, presentValue=presentValue,  units_state=units_state,
                       history_size=history_size)

    @property
    def enumValue(self):
        """
        returns: (str) Enum state value
        """
        try:
            return self.properties.units_state[int(self.lastValue) - 1]
        except IndexError:
            value = 'unknown'
        except ValueError:
            value = 'NaN'
        return value

    @property
    def units(self):
        """
        Enums have 'state text' instead of units.
        """
        return None

    def _set(self, value):
        if isinstance(value, int):
            self._setitem(value)
        elif str(value) in self.properties.units_state:
            self._setitem(self.properties.units_state.index(value) + 1)
        elif str(value).lower() == 'auto':
            self._setitem('auto')
        else:
            raise ValueError(
                'Value must be integer or correct enum state : {}'.format(self.properties.units_state))

    def __repr__(self):
        # return '%s : %s' % (self.name, )
        return '{}/{} : {}'.format(self.properties.device.properties.name, self.properties.name, self.enumValue)

    def __eq__(self, other):
        return self.value == self.properties.units_state.index(other) + 1


#------------------------------------------------------------------------------

class OfflinePoint(Point):
    """
    When offline (DB state), points needs to behave in a particular way
    (we can't read on bacnet...)
    """

    def __init__(self, device, name):
        self.properties = PointProperties()
        self.properties.device = device
        dev_name = self.properties.device.properties.db_name
        props = self.properties.device.read_point_prop(dev_name, name)

        self.properties.name = props['name']
        self.properties.type = props['type']
        self.properties.address = props['address']

        self.properties.description = props['description']
        self.properties.units_state = props['units_state']
        self.properties.simulated = 'Offline'
        self.properties.overridden = 'Offline'

        if 'analog' in self.properties.type:
            self.new_state(NumericPointOffline)
        elif 'multi' in self.properties.type:
            self.new_state(EnumPointOffline)
        elif 'binary' in self.properties.type:
            self.new_state(BooleanPointOffline)
        else:
            raise TypeError('Unknown point type')

    def new_state(self, newstate):
        self.__class__ = newstate


class NumericPointOffline(NumericPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql('select * from "{}"'.format(
            'history'),self.properties.device.properties.db_name)
        his.index = his['index'].apply(Timestamp)
        return his.set_index('index')[self.properties.name]

    @property
    def value(self):
        """
        Take last known value as the value
        """
        try:
            value = self.lastValue
        except IndexError:
            value = 65535
        return value

    def write(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    def sim(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    def release(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    @property
    def units(self):
        return self.properties.units_state

    def _set(self, value):
        raise OfflineException('Must be online to write')

    def __repr__(self):
        return '{}/{} : {:.2f} {}'.format(self.properties.device.properties.name, self.properties.name, self.value, self.properties.units_state)


class BooleanPointOffline(BooleanPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql('select * from "{}"'.format(
            'history'),self.properties.device.properties.db_name)
        his.index = his['index'].apply(Timestamp)
        return his.set_index('index')[self.properties.name]

    @property
    def value(self):
        try:
            value = self.lastValue
        except IndexError:
            value = 'NaN'
        return value

    def _set(self, value):
        raise OfflineException('Point must be online to write')

    def write(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    def sim(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    def release(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')


class EnumPointOffline(EnumPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql('select * from "{}"'.format(
            'history'),self.properties.device.properties.db_name)
        his.index = his['index'].apply(Timestamp)
        return his.set_index('index')[self.properties.name]

    @property
    def value(self):
        """
        Take last known value as the value
        """
        try:
            value = self.lastValue
        except IndexError:
            value = 'NaN'
        except ValueError:
            value = 'NaN'
        return value

    @property
    def enumValue(self):
        """
        returns: (str) Enum state value
        """
        try:
            value = self.properties.units_state[int(self.lastValue) - 1]
        except IndexError:
            value = 'unknown'
        except ValueError:
            value = 'NaN'
        return value

    def _set(self, value):
        raise OfflineException('Point must be online to write')

    def write(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    def sim(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')

    def release(self, value, *, prop='presentValue', priority=''):
        raise OfflineException('Must be online to write')


class OfflineException(Exception):
    pass
