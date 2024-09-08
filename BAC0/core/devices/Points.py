#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Points.py - Definition of points so operations on Read results are more convenient.
"""

import asyncio
import typing as t
from collections import namedtuple

# --- standard Python modules ---
from datetime import datetime, timedelta

from bacpypes3.basetypes import BinaryPV, PropertyIdentifier
from bacpypes3.pdu import Address

# --- 3rd party modules ---
from bacpypes3.primitivedata import Boolean, CharacterString, ObjectIdentifier

from ...tasks.Match import Match, Match_Value

# --- this application's modules ---
from ...tasks.Poll import SimplePoll as Poll
from ..io.IOExceptions import (
    NoResponseFromController,
    RemovedPointException,
    UnknownPropertyError,
    WritePropertyException,
)
from ..utils.lookfordependency import pandas_if_available
from ..utils.notes import note_and_log

_PANDAS, pd, sql, Timestamp = pandas_if_available()
# ------------------------------------------------------------------------------


class PointProperties(object):
    """
    A container for point properties.
    """

    def __init__(self):
        self.device = None
        self.name = None
        self.type = ""
        self.address = -1
        self.description = None
        self.units_state = None
        self.simulated: t.Tuple[bool, t.Optional[int]] = (False, None)
        self.overridden: t.Tuple[bool, t.Optional[int]] = (False, None)
        self.priority_array = None
        self.history_size = None
        self.bacnet_properties = {}
        self.status_flags = None

    def __repr__(self):
        return f"{self.asdict}"

    @property
    def asdict(self):
        return self.__dict__


# ------------------------------------------------------------------------------


@note_and_log
class Point:
    """
    Represents a device BACnet point.  Used to NumericPoint, BooleanPoint and EnumPoints.

    Each point implements a history feature. Each time the point is read, its value (with timestamp)
    is added to a history table. Histories capture the changes to point values over time.
    """

    _cache_delta = timedelta(seconds=5)
    _last_cov_identifier = 0
    _running_cov_tasks = {}

    def __init__(
        self,
        device=None,
        pointType=None,
        pointAddress=None,
        pointName=None,
        description=None,
        presentValue=None,
        units_state=None,
        history_size=None,
        tags=[],
    ):
        self._history = namedtuple("_history", ["timestamp", "value"])
        self.properties = PointProperties()

        self._polling_task = namedtuple("_polling_task", ["task", "running"])
        self._polling_task.task = None
        self._polling_task.running = False

        self._match_task = namedtuple("_match_task", ["task", "running"])
        self._match_task.task = None
        self._match_task.running = False

        self._history.timestamp = []
        self._history.value = []
        # self._history.value = [presentValue]
        # self._history.timestamp.append(datetime.now().astimezone())

        self.properties.history_size = history_size

        self.properties.device = device
        self.properties.name = str(pointName)
        self.properties.type = pointType
        self.properties.address = pointAddress

        self.properties.description = str(description)
        self.properties.units_state = units_state
        self.properties.simulated = (False, 0)
        self.properties.overridden = (False, 0)

        self.cov_registered = False

        self.tags = tags

        self._cache: t.Dict[str, t.Tuple[t.Optional[datetime], t.Any]] = {
            "_previous_read": (None, None)
        }

    @property
    async def value(self):
        """
        Retrieve value of the point
        """
        if (
            self._cache["_previous_read"][0]
            and datetime.now().astimezone() - self._cache["_previous_read"][0]
            < Point._cache_delta
        ):
            return self._cache["_previous_read"][1]

        try:
            res = await self.properties.device.properties.network.read(
                "{} {} {} presentValue".format(
                    self.properties.device.properties.address,
                    self.properties.type,
                    str(self.properties.address),
                ),
                vendor_id=self.properties.device.properties.vendor_id,
            )
            # self._trend(res)
        except Exception:
            raise
        self._cache["_previous_read"] = (datetime.now().astimezone(), res)
        return res

    async def read_priority_array(self):
        """
        Retrieve priority array of the point
        """
        if self.properties.priority_array is not False:
            try:
                res = await self.properties.device.properties.network.read(
                    "{} {} {} priorityArray".format(
                        self.properties.device.properties.address,
                        self.properties.type,
                        str(self.properties.address),
                    ),
                    vendor_id=self.properties.device.properties.vendor_id,
                )
                self.properties.priority_array = []
                for i, each in enumerate(res):
                    _t = each.__dict__["_choice"]
                    val = each.__dict__[_t]
                    self.properties.priority_array.append(
                        {
                            "priority": i + 1,
                            "priorityValue": each,
                            "value": val,
                            "choice": _t,
                        }
                    )
            except (ValueError, UnknownPropertyError):
                self.properties.priority_array = False
            except Exception as e:
                raise Exception(f"Problem reading : {self.properties.name} | {e}")

    async def read_property(self, prop):
        try:
            return await self.properties.device.properties.network.read(
                "{} {} {} {}".format(
                    self.properties.device.properties.address,
                    self.properties.type,
                    str(self.properties.address),
                    prop,
                ),
                vendor_id=self.properties.device.properties.vendor_id,
            )
        except Exception as e:
            raise Exception(f"Problem reading : {self.properties.name} | {e}")

    async def update_bacnet_properties(self):
        """
        Retrieve bacnet properties for this point
        To retrieve something general, forcing vendor id 0
        """
        try:
            res = await self.properties.device.properties.network.readMultiple(
                "{} {} {} all".format(
                    self.properties.device.properties.address,
                    self.properties.type,
                    str(self.properties.address),
                ),
                vendor_id=self.properties.device.properties.vendor_id,
                show_property_name=True,
            )
            for each in res:
                if not each:
                    continue
                v, prop = each
                self.properties.bacnet_properties[prop] = v

        except Exception as e:
            raise Exception(f"Problem reading : {self.properties.name} | {e}")

    @property
    async def bacnet_properties(self):
        if not self.properties.bacnet_properties:
            await self.update_bacnet_properties()
        return self.properties.bacnet_properties

    @property
    def is_overridden(self):
        self.read_priority_array()
        if self.properties.priority_array is False:
            return False
        if self.priority(8) or self.priority(1):
            self.properties.overridden = (True, self.value)
            return True
        else:
            return False

    async def priority(self, priority=None):
        if self.properties.priority_array is False:
            return None

        await self.read_priority_array()
        if priority is None:
            return self.properties.priority_array
        if priority < 1 or priority > 16:
            raise IndexError("Please provide priority to read (1-16)")

        else:
            val = self.properties.priority_array[priority - 1]["value"]._value
            if isinstance(val, tuple) and len(val) == 0:
                return None
            return val

    def _trend(self, res: t.Union[float, int, str]) -> None:
        now = datetime.now().astimezone()
        self._history.timestamp.append(now)
        self._history.value.append(res)
        if self.properties.device.properties.network.database:
            self.properties.device.properties.network.database.prepare_point([self])

        if self.properties.history_size is None:
            return
        else:
            if self.properties.history_size < 1:
                self.properties.history_size = 1
            if len(self._history.timestamp) >= self.properties.history_size:
                try:
                    self._history.timestamp = self._history.timestamp[
                        -self.properties.history_size :  # noqa E203
                    ]
                    self._history.value = self._history.value[
                        -self.properties.history_size :  # noqa E203
                    ]
                    assert len(self._history.timestamp) == len(self._history.value)

                except Exception:
                    self._log.exception("Can't append to history")

    @property
    def units(self):
        """
        Should return units
        """
        raise Exception("Must be overridden")

    @property
    def lastValue(self):
        """
        returns: last value read
        """
        if _PANDAS:
            last_val = self.history.dropna()
            last_val_clean = None if len(last_val) == 0 else last_val.iloc[-1]
            return last_val_clean
        else:
            return self._history.value[-1]

    @property
    def lastTimestamp(self):
        """
        returns: last timestamp read
        """
        if _PANDAS:
            last_val = self.history.dropna()
            last_val_clean = None if len(last_val) == 0 else last_val.index[-1]
            return last_val_clean
        else:
            return self._history.timestamp[-1]

    @property
    def history(self) -> t.Dict[datetime, t.Union[int, float, str]]:
        """
        returns : (pd.Series) containing timestamp and value of all readings
        """
        if not _PANDAS:
            return dict(zip(self._history.timestamp, self._history.value))
        idx = self._history.timestamp.copy()
        his_table = pd.Series(index=idx, data=self._history.value[: len(idx)])
        del idx
        his_table.name = ("{}/{}").format(
            self.properties.device.properties.name, self.properties.name
        )
        his_table.units = self.properties.units_state
        if self.properties.name in self.properties.device.binary_states:
            his_table.states = "binary"
        elif self.properties.name in self.properties.device.multi_states:
            his_table.states = "multistates"
        else:
            his_table.states = "analog"
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

    @property
    def status(self):
        return self.properties.status_flags

    async def __getitem__(self, key):
        """
        Way to get points... presentValue, status, flags, etc...

        :param key: state
        :returns: list of enum states
        """
        if str(key).lower() in ["unit", "units", "state", "states"]:
            key = "units_state"
        try:
            return getattr(self.properties, key)
        except AttributeError:
            try:
                if "@prop_" in key:
                    key = key.split("prop_")[1]
                return await self.read_property(key)
            except Exception:
                raise ValueError(f"Cannot find property named {key}")

    async def write(
        self, value: t.Any, *, prop: str = "presentValue", priority: str = "16"
    ):
        """
        Write to present value of a point

        :param value: (float) numeric value
        :param prop: (str) property to write. Default = presentValue
        :param priority: (int) priority to which write.

        """
        if prop == "description":
            await self.update_description(value)
        else:
            if priority != "":
                if (
                    isinstance(float(priority), float)
                    and float(priority) >= 1
                    and float(priority) <= 16
                ):
                    priority = f"{priority}"
                else:
                    raise ValueError("Priority must be a number between 1 and 16")
            req = f"{self.properties.device.properties.address} {self.properties.type} {self.properties.address} {prop} {value} - {priority}"
            # self.log(req, level='info')
            try:
                await self.properties.device.properties.network._write(
                    req,
                    vendor_id=self.properties.device.properties.vendor_id,
                )
            except NoResponseFromController:
                raise

            # Read after the write so history gets updated.
            await self.value

    async def default(self, value):
        await self.write(value, prop="relinquishDefault")

    async def sim(self, value, *, force=False):
        """
        Simulate a value.  Sets the Out_Of_Service property- to disconnect the point from the
        controller's control.  Then writes to the Present_Value.
        The point name is added to the list of simulated points (self.simPoints)

        :param value: (float) value to simulate
        """
        if (
            not self.properties.simulated[0]
            or self.properties.simulated[1] != value
            or force is not False
        ):
            await self.properties.device.properties.network.sim(
                f"{self.properties.device.properties.address} {self.properties.type} {self.properties.address} presentValue {value}"
            )
            self.properties.simulated = (True, value)

    async def out_of_service(self):
        """
        Sets the Out_Of_Service property [to True].
        """
        await self.properties.device.properties.network.out_of_service(
            f"{self.properties.device.properties.address} {self.properties.type} {self.properties.address} outOfService True"
        )
        self.properties.simulated = (True, None)

    async def is_out_of_service(self):
        """
        Check if the Out_Of_Service property is true.
        """
        res = await self.properties.device.properties.network.is_out_of_service(
            f"{self.properties.device.properties.address} {self.properties.type} {self.properties.address} outOfService"
        )
        self.properties.simulated = (True, None)
        return res

    async def release(self):
        """
        Clears the Out_Of_Service property [to False] - so the controller regains control of the point.
        """
        await self.properties.device.properties.network.release(
            f"{self.properties.device.properties.address} {self.properties.type} {self.properties.address} outOfService inactive"
        )
        self.properties.simulated = (False, None)

    def ovr(self, value):
        asyncio.create_task(self.write(value, priority=8))
        self.properties.overridden = (True, value)

    def auto(self):
        asyncio.create_task(self.write("null", priority=8))
        self.properties.overridden = (False, 0)

    def release_ovr(self):
        asyncio.create_task(self.write("null", priority=1))
        asyncio.create_task(self.write("null", priority=8))
        self.properties.overridden = (False, None)

    async def _setitem(self, value):
        """
        Called by _set, will trigger right function depending on
        point type to write to the value and make tests.
        This is default behaviour of the point  :
        AnalogValue are written to
        AnalogOutput are overridden
        """
        self.log(f"Setting to {value}", level="debug")
        if "characterstring" in self.properties.type:
            await self.write(value)

        elif "value" in self.properties.type:
            if str(value).lower() == "auto":
                raise ValueError(
                    "Value was not simulated or overridden, cannot release to auto"
                )
            # analog value must be written to
            await self.write(value)

        elif "output" in self.properties.type:
            # analog output must be overridden
            if str(value).lower() == "auto":
                self.auto()
            else:
                self.ovr(value)
        else:
            # input are left... must be simulated
            if str(value).lower() == "auto":
                await self.release()
            else:
                self.log(f"Simulating to {value}", level="debug")
                await self.sim(value)

    async def _set(self, value):
        """
        Allows the syntax:
            device['point'] = value
        """
        raise NotImplementedError("Must be overridden")

    def poll(self, command="start", *, delay: int = 10) -> None:
        asyncio.create_task(self._poll(command=command, delay=delay))

    async def _poll(self, command="start", *, delay: int = 10) -> None:
        """
        Poll a point every x seconds (delay=x sec)
        Stopped by using point.poll('stop') or .poll(0) or .poll(False)
        or by setting a delay = 0
        """
        if (
            str(command).lower() == "stop"
            or command is False
            or command == 0
            or delay == 0
        ):
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
            raise RuntimeError("Stop polling before redefining it")

    def match(self, point, *, delay=5):
        asyncio.create_task(self._match(point=point, delay=delay))

    async def _match(self, point, *, delay=5):
        """
        This allow functions like :
            device['status'].match('command')

        A fan status for example will follow the command...
        """
        if self._match_task.task is None:
            self._match_task.task = Match(command=point, status=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay > 0:
            await self._match_task.task.stop()
            self._match_task.running = False
            await asyncio.sleep(1)

            self._match_task.task = Match(command=point, status=self, delay=delay)
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay == 0:
            await self._match_task.task.stop()
            self._match_task.running = False

        else:
            raise RuntimeError("Stop task before redefining it")

    def match_value(self, value, *, delay=5, use_last_value=False):
        asyncio.create_task(
            self._match_value(value=value, delay=delay, use_last_value=use_last_value)
        )

    async def _match_value(self, value, *, delay=5, use_last_value=False):
        """
        This allow functions like :
            device['point'].match('value')

        A sensor will follow a calculation...
        """
        if self._match_task.task is None:
            self._match_task.task = Match_Value(
                value=value, point=self, delay=delay, use_last_value=use_last_value
            )
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay > 0:
            await self._match_task.task.stop()
            self._match_task.running = False
            await asyncio.sleep(1)

            self._match_task.task = Match_Value(
                value=value, point=self, delay=delay, use_last_value=use_last_value
            )
            self._match_task.task.start()
            self._match_task.running = True

        elif self._match_task.running and delay == 0:
            await self._match_task.task.stop()
            self._match_task.running = False

        else:
            raise RuntimeError("Stop task before redefining it")

    def __len__(self):
        """
        Length of a point = # of history records
        """
        return len(self.history)

    async def subscribe_cov(self, confirmed: bool = False, lifetime: int = 900):
        """
        Subscribes to the Change of Value (COV) service for this point.

        The COV service allows the device to notify the application of changes to the value of a property.
        This method sets up the subscription and starts an asynchronous task to listen for these notifications.

        Args:
            confirmed (bool, optional): If True, the device will wait for a confirmation from the application
                after sending a COV notification. Defaults to True.
            lifetime (int, optional): The lifetime of the subscription in seconds. If None, the subscription
                will last indefinitely. Defaults to None.
            callback (function, optional): A function to be called when a COV notification is received.
                The function should accept two arguments: the sender (the device) and the args (the notification).

        Raises:
            RuntimeError: If the task is already running, a RuntimeError will be raised.

        Returns:
            None
        """
        self.cov_task = COVSubscription(
            point=self, confirmed=confirmed, lifetime=lifetime
        )
        Point._running_cov_tasks[self.cov_task.process_identifier] = self.cov_task
        self.cov_task.task = asyncio.create_task(self.cov_task.run())

    async def cancel_cov(self):
        self.log(f"Canceling COV subscription for {self.properties.name}", level="info")
        process_identifer = self.cov_task.process_identifier

        if process_identifer not in Point._running_cov_tasks:
            await self.response("COV subscription not found")
            return
        cov_subscription = Point._running_cov_tasks.pop(process_identifer)
        cov_subscription.stop()
        # await cov_subscription.task

    def update_description(self, value):
        asyncio.create_task(self._update_description(value=value))

    async def _update_description(self, value):
        """
        This will write to the BACnet point and modify the description
        of the object
        """
        await self.properties.device.properties.network.send_text_write_request(
            addr=self.properties.device.properties.address,
            obj_type=self.properties.type,
            obj_inst=int(self.properties.address),
            value=value,
            prop_id="description",
        )
        self.properties.description = str(self.read_property("description"))

    def tag(self, tag_id, tag_value, lst=None):
        """
        Add tag to point. Those tags can be used to make queries,
        add information, etc.
        They will be included if InfluxDB is used.
        """
        if lst is None:
            self.tag.append((tag_id, tag_value))
        else:
            for each in lst:
                tag_id, tag_value = each
                self.tag.append((tag_id, tag_value))

    async def _update_value(self):
        await asyncio.wait_for(self.value, timeout=1.0)

    def _update_value_if_required(self):
        value_too_old = (
            self._history.timestamp[-1]
            > datetime.now().astimezone() - Point._cache_delta
        )
        if value_too_old:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._update_value())
            except Exception as e:
                self.log(f"Error updating value : {e}", level="error")
                return self.lastValue
        if datetime.now().astimezone() - self._history.timestamp[-1] > timedelta(
            seconds=60
        ):
            self.log(
                f"Last known value {self._history.value[-1]} with timestamp of {self._history.timestamp[-1]}, older than 10sec {datetime.now().astimezone()}. Consider using dev['point'].lastValue if you trust polling of device of manage a up to date read in asynchronous side of your app for better precision",
                level="warning",
            )
        return self.lastValue


# ------------------------------------------------------------------------------


class NumericPoint(Point):
    """
    Representation of a Numeric value
    """

    def __init__(
        self,
        device=None,
        pointType=None,
        pointAddress=None,
        pointName=None,
        description=None,
        presentValue=None,
        units_state=None,
        history_size=None,
    ):
        Point.__init__(
            self,
            device=device,
            pointType=pointType,
            pointAddress=pointAddress,
            pointName=pointName,
            description=description,
            presentValue=presentValue,
            units_state=units_state,
            history_size=history_size,
        )

    #    @property
    #    def val(self):
    #        res = asyncio.run_coroutine_threadsafe(self.value)
    #        return res.result()

    @property
    async def value(self):
        res = await super().value
        self._trend(res)
        return res

    @property
    def units(self):
        return self.properties.units_state

    async def _set(self, value):
        if str(value).lower() == "auto":
            await self._setitem(value)
        else:
            try:
                if isinstance(value, Point):
                    value = value.lastValue
                val = float(value)
                if isinstance(val, float):
                    await self._setitem(value)
            except Exception as error:
                raise WritePropertyException(f"Problem writing to device : {error}")

    def __repr__(self):
        try:
            polling = self.properties.device.properties.pollDelay
            if (polling < 90 and polling > 0) or self.cov_registered:
                val = float(self.lastValue)
            else:
                asyncio.gather(self.value, asyncio.sleep(1))
                val = float(self.lastValue)
        except ValueError:
            self._log.error(
                "Cannot convert value {}. Device probably disconnected or the response is inconsistent".format(
                    self.value
                )
            )
            # Probably disconnected
            return "{}/{} : (n/a) {}".format(
                self.properties.device.properties.name,
                self.properties.name,
                self.properties.units_state,
            )

        return "{}/{} : {:.2f} {}".format(
            self.properties.device.properties.name,
            self.properties.name,
            val,
            self.properties.units_state,
        )

    def __add__(self, other):
        self._update_value_if_required()
        return self.lastValue + other

    __radd__ = __add__

    def __sub__(self, other):
        return self._update_value_if_required() - other

    def __rsub__(self, other):
        return other - self._update_value_if_required()

    def __mul__(self, other):
        return self._update_value_if_required() * other

    __rmul__ = __mul__

    def __truediv__(self, other):
        return self._update_value_if_required() / other

    def __rtruediv__(self, other):
        return other / self._update_value_if_required()

    def __lt__(self, other):
        return self._update_value_if_required() < other

    def __le__(self, other):
        return self._update_value_if_required() <= other

    def __eq__(self, other):
        return self._update_value_if_required() == other

    def __gt__(self, other):
        return self._update_value_if_required() > other

    def __ge__(self, other):
        return self._update_value_if_required() >= other


# ------------------------------------------------------------------------------


class BooleanPoint(Point):
    """
    Representation of a Boolean value
    """

    def __init__(
        self,
        device=None,
        pointType=None,
        pointAddress=None,
        pointName=None,
        description=None,
        presentValue=None,
        units_state=None,
        history_size=None,
    ):
        Point.__init__(
            self,
            device=device,
            pointType=pointType,
            pointAddress=pointAddress,
            pointName=pointName,
            description=description,
            presentValue=presentValue,
            units_state=units_state,
            history_size=history_size,
        )
        self.properties.units_state = tuple(str(x) for x in units_state)

    def _trend(self, res):
        res = "1: active" if res == BinaryPV.active else "0: inactive"
        super()._trend(res)

    @property
    async def value(self):
        """
        Read the value from BACnet network
        """
        res = await super().value
        self._trend(res)

        if res == BinaryPV.inactive:
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
        if ":" in self.lastValue:
            _val = int(self.lastValue.split(":")[0])
        else:
            _val = self.lastValue
        if _val in [1, "active"]:
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

    async def _set(self, value):
        try:
            if value is True:
                await self._setitem("active")
            elif value is False:
                await self._setitem("inactive")
            elif str(value) in ["inactive", "active"] or str(value).lower() == "auto":
                await self._setitem(value)
            else:
                raise ValueError(
                    'Value must be boolean True, False or "active"/"inactive"'
                )
        except (Exception, ValueError) as error:
            raise WritePropertyException(f"Problem writing to device : {error}")

    def __repr__(self):
        polling = self.properties.device.properties.pollDelay
        if (polling >= 90 or polling <= 0) and not self.cov_registered:
            # Force reading
            self._log.warning(
                "Cannot read in __repr__ as it need an asynchronous call, using lastValue"
            )
            self.lastValue
        return "{}/{} : {}".format(
            self.properties.device.properties.name, self.properties.name, self.boolValue
        )

    def __or__(self, other):
        self._update_value_if_required()
        return self.boolValue | other

    def __and__(self, other):
        self._update_value_if_required()
        return self.boolValue & other

    def __xor__(self, other):
        self._update_value_if_required()
        return self.boolValue ^ other

    def __eq__(self, other):
        self._update_value_if_required()
        if isinstance(other, str):
            if ":" in other:
                return self.lastValue == other
            elif other in ("inactive", "active"):
                return self.lastValue.split(":")[1] == other
            else:
                return False
        elif isinstance(other, bool):
            return self.boolValue == other
        elif isinstance(other, int):
            return int(self.lastValue.split(":")[0]) == other
        else:
            return False


# ------------------------------------------------------------------------------


class EnumPoint(Point):
    """
    Representation of an Enumerated (multiState) value
    """

    def __init__(
        self,
        device=None,
        pointType=None,
        pointAddress=None,
        pointName=None,
        description=None,
        presentValue=None,
        units_state=None,
        history_size=None,
    ):
        Point.__init__(
            self,
            device=device,
            pointType=pointType,
            pointAddress=pointAddress,
            pointName=pointName,
            description=description,
            presentValue=presentValue,
            units_state=units_state,
            history_size=history_size,
        )
        self.properties.units_state = (
            [str(x) for x in units_state] if units_state else []
        )

    def _trend(self, res):
        res = f"{res}: {self.get_state(res)}"
        super()._trend(res)

    @property
    async def value(self):
        res = await super().value
        # self.log("Value : {}".format(res), level='info')
        # self.log("EnumValue : {}".format(self.get_state(res)), level='info')
        self._trend(res)
        return res

    def get_state(self, v):
        try:
            # errors caught below
            return self.properties.units_state[v - 1]  # type: ignore[index]
        except (TypeError, IndexError):
            return "n/a"

    @property
    def enumValue(self):
        """
        returns: (str) Enum state value
        """
        try:
            if ":" in self.lastValue:
                _val = int(self.lastValue.split(":")[0])
                return self.get_state(_val)
        except TypeError:
            # probably first occurence of history... retry
            return self.get_state(self.lastValue)
        except IndexError:
            value = "unknown"
        except ValueError:
            value = "NaN"
        return value

    @property
    def units(self):
        """
        Enums have 'state text' instead of units.
        """
        return None

    async def _set(self, value):
        try:
            if isinstance(value, int):
                await self._setitem(value)
            elif str(value) in self.properties.units_state:  # type: ignore[operator]
                await self._setitem(self.properties.units_state.index(value) + 1)
            elif str(value).lower() == "auto":
                await self._setitem("auto")
            else:
                raise ValueError(
                    "Value must be integer or correct enum state : {}".format(
                        self.properties.units_state
                    )
                )
        except (Exception, ValueError) as error:
            raise WritePropertyException(f"Problem writing to device : {error}")

    def __repr__(self):
        polling = self.properties.device.properties.pollDelay
        if (polling >= 90 or polling <= 0) and not self.cov_registered:
            # Force reading
            self.value
        return "{}/{} : {}".format(
            self.properties.device.properties.name, self.properties.name, self.enumValue
        )

    def __eq__(self, other):
        self._update_value_if_required()
        if isinstance(other, str):
            if ":" in other:
                return self.lastValue == other
            else:
                return self.enumValue == other
        elif isinstance(other, int):
            return int(self.lastValue.split(":")[0]) == other
        else:
            return self.lastValue == other


class StringPoint(Point):
    """
    Representation of CharacterString value
    """

    def __init__(
        self,
        device=None,
        pointType=None,
        pointAddress=None,
        pointName=None,
        description=None,
        units_state=None,
        presentValue=None,
        history_size=None,
    ):
        Point.__init__(
            self,
            device=device,
            pointType=pointType,
            pointAddress=pointAddress,
            pointName=pointName,
            description=description,
            presentValue=presentValue,
            history_size=history_size,
        )

    @property
    def units(self):
        """
        Characterstring value do not have units or state text
        """
        return None

    def _trend(self, res):
        super()._trend(res)

    @property
    async def value(self):
        res = await super().value
        self._trend(res)
        return res

    async def _set(self, value):
        try:
            if isinstance(value, str):
                await self._setitem(value)
            elif isinstance(value, CharacterString):
                await self._setitem(value.value)
            else:
                raise ValueError("Value must be string or CharacterString")
        except (Exception, ValueError) as error:
            raise WritePropertyException(f"Problem writing to device : {error}")

    def __repr__(self):
        try:
            polling = self.properties.device.properties.pollDelay
            if (polling < 90 and polling > 0) or self.cov_registered:
                val = str(self.lastValue)
            else:
                val = str(self.value)
        except ValueError:
            self.log(
                "Cannot convert value. Device probably disconnected", level="error"
            )
            # Probably disconnected
            val = None
        return "{}/{} : {}".format(
            self.properties.device.properties.name, self.properties.name, val
        )

    def __eq__(self, other):
        self._update_value_if_required()
        return self.lastValue == other.value


class DateTimePoint(Point):
    """
    Representation of DatetimeValue value
    """

    def __init__(
        self,
        device=None,
        pointType=None,
        pointAddress=None,
        pointName=None,
        description=None,
        units_state=None,
        presentValue=None,
        history_size=None,
    ):
        Point.__init__(
            self,
            device=device,
            pointType=pointType,
            pointAddress=pointAddress,
            pointName=pointName,
            description=description,
            presentValue=presentValue,
            history_size=history_size,
        )

    @property
    def units(self):
        """
        Characterstring value do not have units or state text
        """
        return None

    def _trend(self, res):
        # super()._trend(res)
        return

    @property
    async def value(self):
        res = await super().value
        # self._trend(res)
        year, month, day, dayofweek = res.date
        hour, minutes, seconds, ms = res.time
        res = datetime(year + 1900, month, day, hour, minutes, seconds)
        return res

    def _set(self, value):
        # try:
        #    if isinstance(value, str):
        #        self._setitem(value)
        #    elif isinstance(value, CharacterString):
        #        self._setitem(value.value)
        #    else:
        #        raise ValueError("Value must be string or CharacterString")
        # except (Exception, ValueError) as error:
        #    raise WritePropertyException("Problem writing to device : {}".format(error))`
        raise NotImplementedError("Writing to Datetime is not supported yet")

    async def __repr__(self):
        try:
            # polling = self.properties.device.properties.pollDelay
            # if (polling < 90 and polling > 0) or self.cov_registered:
            #    val = str(self.lastValue)
            # else:
            val = await self.value
        except ValueError:
            self.log(
                "Cannot convert value. Device probably disconnected", level="error"
            )
            # Probably disconnected
            val = None
        return "{}/{} : {}".format(
            self.properties.device.properties.name, self.properties.name, val
        )

    def __eq__(self, other):
        self._update_value_if_required()
        return self.lastValue == other.value

    def __ge__(self, other):
        self._update_value_if_required()
        return self.lastValue >= other.value

    def __le__(self, other):
        self._update_value_if_required()
        return self.lastValue <= other.value

    def __gt__(self, other):
        self._update_value_if_required()
        return self.lastValue > other.value

    def __lt__(self, other):
        self._update_value_if_required()
        return self.lastValue < other.value


# ------------------------------------------------------------------------------


class OfflinePoint(Point):
    """
    When offline (DB state), points needs to behave in a particular way
    (we can't read on bacnet...)
    """

    def __init__(self, device, name):
        self.properties = PointProperties()
        self.properties.device = device
        dev_name = self.properties.device.properties.db_name
        try:
            props = self.properties.device.read_point_prop(dev_name, name)
        except RemovedPointException:
            raise

        self.properties.name = props["name"]
        self.properties.type = props["type"]
        self.properties.address = props["address"]

        self.properties.description = props["description"]
        self.properties.units_state = props["units_state"]
        self.properties.simulated = (True, None)
        self.properties.overridden = (False, None)

        if "analog" in self.properties.type:
            self.new_state(NumericPointOffline)
        elif "multi" in self.properties.type:
            self.new_state(EnumPointOffline)
        elif "binary" in self.properties.type:
            self.new_state(BooleanPointOffline)
        elif "string" in self.properties.type:
            self.new_state(StringPointOffline)
        else:
            raise TypeError("Unknown point type")

    def new_state(self, newstate):
        self.__class__ = newstate


class NumericPointOffline(NumericPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql(
            'select * from "history"',
            self.properties.device.properties.db_name,
        )
        his.index = his["index"].apply(Timestamp)
        return his.set_index("index")[self.properties.name]

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

    def write(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def sim(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def release(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    @property
    def units(self):
        return self.properties.units_state

    def _set(self, value):
        raise OfflineException("Must be online to write")

    def __repr__(self):
        return "{}/{} : {:.2f} {}".format(
            self.properties.device.properties.name,
            self.properties.name,
            self.value,
            self.properties.units_state,
        )


class BooleanPointOffline(BooleanPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql(
            'select * from "history"',
            self.properties.device.properties.db_name,
        )
        his.index = his["index"].apply(Timestamp)
        return his.set_index("index")[self.properties.name]

    @property
    def value(self):
        try:
            value = self.lastValue
        except IndexError:
            value = "NaN"
        return value

    def _set(self, value):
        raise OfflineException("Point must be online to write")

    def write(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def sim(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def release(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")


class EnumPointOffline(EnumPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql(
            'select * from "history"',
            self.properties.device.properties.db_name,
        )
        his.index = his["index"].apply(Timestamp)
        return his.set_index("index")[self.properties.name]

    @property
    def value(self):
        """
        Take last known value as the value
        """
        try:
            value = self.lastValue
        except IndexError:
            value = "NaN"
        except ValueError:
            value = "NaN"
        return value

    @property
    def enumValue(self):
        """
        returns: (str) Enum state value
        """
        try:
            value = self.properties.units_state[int(self.lastValue) - 1]  # type: ignore[index]
        except IndexError:
            value = "unknown"
        except ValueError:
            value = "NaN"
        return value

    def _set(self, value):
        raise OfflineException("Point must be online to write")

    def write(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def sim(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def release(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")


class StringPointOffline(EnumPoint):
    @property
    def history(self):
        his = self.properties.device._read_from_sql(
            'select * from "history"',
            self.properties.device.properties.db_name,
        )
        his.index = his["index"].apply(Timestamp)
        return his.set_index("index")[self.properties.name]

    @property
    def value(self):
        """
        Take last known value as the value
        """
        try:
            value = self.lastValue
        except IndexError:
            value = "NaN"
        except ValueError:
            value = "NaN"
        return value

    def _set(self, value):
        raise OfflineException("Point must be online to write")

    def write(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def sim(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")

    def release(self, value, *, prop="presentValue", priority=""):
        raise OfflineException("Must be online to write")


class COVSubscription:
    def __init__(
        self, point: Point = None, lifetime: int = 900, confirmed: bool = False
    ):
        self.address = Address(point.properties.device.properties.address)
        self.cov_fini = asyncio.Event()
        self.task = None
        self.obj_identifier = ObjectIdentifier(
            (point.properties.type, int(point.properties.address))
        )
        self._app = point.properties.device.properties.network.this_application.app
        self.process_identifier = Point._last_cov_identifier + 1
        Point._last_cov_identifier = self.process_identifier

        self.point = point
        self.lifetime = lifetime
        self.confirmed = confirmed

    async def run(self):
        self.point.cov_registered = True
        self.point.log(
            f"Subscribing to COV for {self.point.properties.name}", level="info"
        )

        try:
            async with self._app.change_of_value(
                self.address,
                self.obj_identifier,
                self.process_identifier,
                self.confirmed,
                self.lifetime,
            ) as scm:
                cov_fini_task_monitor = asyncio.create_task(self.cov_fini.wait())
                while not self.cov_fini.is_set():
                    incoming: asyncio.Future = asyncio.ensure_future(scm.get_value())
                    done, pending = await asyncio.wait(
                        [
                            incoming,
                        ],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()

                    if incoming in done:
                        property_identifier, property_value = incoming.result()
                        self.point.log(
                            f"COV notification received for {self.point.properties.name} | {property_identifier} -> {type(property_identifier)} with value {property_value} | {property_value} -> {type(property_value)}",
                            level="info",
                        )
                        if property_identifier == PropertyIdentifier.presentValue:
                            val = extract_value_from_primitive_data(property_value)
                            self.point._trend(val)
                        elif property_identifier == PropertyIdentifier.statusFlags:
                            self.point.properties.status_flags = property_value
                        else:
                            self.point._log.warning(
                                f"Unsupported COV property identifier {property_identifier}"
                            )
                await cov_fini_task_monitor
        except Exception as e:
            self.point.log(f"Error in COV subscription : {e}", level="error")

    def stop(self):
        self.point.log(
            f"Stopping COV subscription class for {self.point.properties.name}",
            level="debug",
        )
        self.cov_fini.set()
        self.point.cov_registered = False


class OfflineException(Exception):
    pass


def extract_value_from_primitive_data(value):
    if isinstance(value, float):
        return float(value)
    elif isinstance(value, Boolean):
        if value == int(1):
            return True
        else:
            return False
    elif isinstance(value, int):
        return int(value)
    elif isinstance(value, str):
        return str(value)
    else:
        return value
