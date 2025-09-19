from datetime import datetime, timezone

import pytz
import typing as t
import os

from ..core.utils.lookfordependency import influxdb_if_available
from ..core.utils.notes import note_and_log

_INFLUX = False
_influx_Version = 0

class Point:
    ## Unknown for now... 
    def __init__(self, *args, **kwargs):
        pass

class InfluxDBClient:
    ## Unknown for now... 
    pass

class WriteOptions:
    ## Unknown for now... 
    def __init__(self, *args, **kwargs):
        pass


class InfluxDBMeta(type):
    """Metaclass that dispatches construction to InfluxDBv2 or InfluxDBv3 based on params."""

    def __call__(self, *args, **kwargs):
        # params may be passed positionally as the first arg or as keyword 'params'
        params = None
        if args and isinstance(args[0], dict):
            params = args[0]
        else:
            params = kwargs.get("params", {})

        if params is None:
            params = {}

        try:
            version = int(params.get("version", 2))
        except Exception:
            version = 2

        _INFLUX, _influx_Version, _influx_client = influxdb_if_available(version=version)
        if not _INFLUX:
            raise ImportError("Install influxdb to use this feature")

        # Choose concrete implementation class first (they are defined later in module)
        impl_name = "InfluxDBv3" if version == 3 else "InfluxDBv2"
        impl = globals().get(impl_name)
        if impl is None:
            raise RuntimeError(f"{impl_name} class not available")

        # Resolve real types and attach them to the implementation class so methods
        # can use self.Point / self.WriteOptions / self.InfluxDBClient safely.
        if _influx_Version == 2:
            from influxdb_client import Point as Pointv2, WriteOptions as WriteOptionsv2
            from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync as InfluxDBClientv2

            setattr(impl, "Point", Pointv2)
            setattr(impl, "InfluxDBClient", InfluxDBClientv2)
            setattr(impl, "WriteOptions", WriteOptionsv2)

        elif _influx_Version == 3:
            from influxdb_client_3 import (
                InfluxDBClient3,
                Point as Pointv3,
                WriteOptions as WriteOptionsv3,
            )

            setattr(impl, "Point", Pointv3)
            setattr(impl, "InfluxDBClient", InfluxDBClient3)
            setattr(impl, "WriteOptions", WriteOptionsv3)

        return impl(params)


@note_and_log
class InfluxDB(metaclass=InfluxDBMeta):
    """Factory proxy: calling this returns an instance of InfluxDBv2 or InfluxDBv3."""

    pass


class InfluxDBCommon:
    # These attributes will be attached to the concrete impl class at runtime
    # by the metaclass: Point, InfluxDBClient, WriteOptions
    points: t.List[t.Any]

    def clean_value(self, object_type, val, units_state):
        """
        Cleans and formats the value based on the object type.

        This method checks the object type and formats the value accordingly. If the object type contains "analog",
        the value is formatted to a string with three decimal places and the units state. If the object type contains "multi",
        the value is split on ":" and the second part is used.

        Parameters:
        object_type (str): The type of the object.
        val: The value to be cleaned.
        units_state: The units state of the object.

        Returns:
        tuple: A tuple containing the cleaned string value and the original value.

        Raises:
        Exception: If an error occurs while cleaning the value.
        """
        try:
            if "analog" in object_type:
                _string_value = f"{val:.3f} {units_state}"
                _value = val
            elif "multi" in object_type:
                _string_value = f"{val.split(':')[1]}"
                _value = int(val.split(":")[0])
            elif "binary" in object_type:
                try:
                    _string_value = f"{units_state[int(val.split(':'[0]))]}"
                except Exception:
                    try:
                        _value, _string_value = val.split(":")
                        _value = int(_value)
                    except Exception as error:
                        self._log.error(
                            f"Error while cleaning value {val} of object type {object_type}: {error}"
                        )
            else:
                _string_value = f"{val}"
                _value = val
            return (_value, _string_value)
        except AttributeError as error:
            self._log.error(
                f"Error while cleaning value {val} of object type {object_type}: {error}"
            )

    def prepare_point(self, list_of_points):
        for point in list_of_points:
            _object_name = point.properties.name
            _devicename = point.properties.device.properties.name
            _device_id = point.properties.device.properties.device_id
            _units_state = f"{point.properties.units_state}"
            _description = point.properties.description
            _object = f"{point.properties.type}:{point.properties.address}"
            _value, _string_value = self.clean_value(
                point.properties.type, point.lastValue, point.properties.units_state
            )
            _name = f"{_devicename}/{_object_name}"
            _id = f"Device_{_device_id}/{_object}"
            PointClass = getattr(self, "Point", None)
            if PointClass is None:
                # fallback to a lightweight dict-like point if no Point class
                _point = {
                    "measurement": self.table if self.version == 3 else _id,
                    "tags": {
                        "id": _id,
                        "object_name": _object_name,
                        "name": _name,
                        "description": _description,
                        "units_state": _units_state,
                        "object": _object,
                        "device": _devicename,
                        "device_id": _device_id,
                    },
                    "fields": {"value": _value, "string_value": _string_value},
                    "time": point.lastTimestamp.astimezone(pytz.UTC),
                }
            else:
                measurement = self.table if self.version == 3 else _id
                _point = (
                    PointClass(measurement)
                    .tag("object_name", _object_name)
                    .tag("name", _name)
                    .tag("description", _description)
                    .tag("units_state", _units_state)
                    .tag("object", _object)
                    .tag("device", _devicename)
                    .tag("device_id", _device_id)
                    .field("value", float(_value))
                    .field("string_value", _string_value)
                    .time(point.lastTimestamp.astimezone(pytz.UTC))
                )
                if self.version == 3:
                    _point.tag("id", _id)
            for each in point.tags:
                _tag_id, _tag_value = each
                # if using dict-like fallback, add tags there
                if isinstance(_point, dict):
                    _point["tags"][_tag_id] = _tag_value
                else:
                    _point.tag(_tag_id, _tag_value)
            self.points.append(_point)

    async def write_points_lastvalue_to_db(self, list_of_points) -> None:
        """
        Writes a list of points to the InfluxDB database.

        Args:
            list_of_points (list): A list of points to be written to the database.

        Returns:
            None
        """
        self.log(f"Writing to db: {self.points}", level="debug")
        success = await self.write(self.points)
        if success:
            self.points = []

    def read_flux(self, request, params):
        pass


@note_and_log
class InfluxDBv3(InfluxDBCommon):
    """
    This class provides a connection to an InfluxDB database version 3.

    It allows for writing to and reading from the database. The connection parameters such as the URL, port, token, organization,
    and bucket are specified as class attributes.

    Attributes:
    url (str): The URL of the InfluxDB server.
    port (int): The port on which the InfluxDB server is listening.
    token (str): The token for authentication with the InfluxDB server.
    org (str): The organization for the InfluxDB server.
    timeout (int): The timeout for requests to the InfluxDB server, in milliseconds.
    database (str): The default bucket to use for operations.
    tags_file (str): The file containing tags for the InfluxDB server.
    username (str): The username for authentication with the InfluxDB server.
    password (str): The password for authentication with the InfluxDB server.
    client (InfluxDBClientAsync): The client for interacting with the InfluxDB server.
    """

    url = None
    port = 8181
    token = None
    org = None
    timeout = 6000
    database = None
    tags_file = None
    bucket = None
    client: InfluxDBClient
    table: str

    def __init__(self, params):
        for k, v in params.items():
            setattr(self, k, v)

        if self.database is not None:
            os.environ["INFLUX_DATABASE"] = str(self.database)
        if self.bucket is not None:
            os.environ["INFLUX_DATABASE"] = str(self.bucket)
            self.log(
                f"InfluxDB version 3 now use database instead of bucket, please update your params dict: {self.bucket} will be used as database",
                level="warning",
            )
        # self.connect_to_db()
        self.points: list[t.Any] = []
        WriteOptionsClass = getattr(self, "WriteOptions", None)
        if WriteOptionsClass is None:
            # fallback to a simple dict for options
            self.write_options = {
                "batch_size": getattr(self, "batch_size", 25),
                "flush_interval": getattr(self, "flush_interval", 10_000),
                "jitter_interval": getattr(self, "jitter_interval", 2_000),
                "retry_interval": getattr(self, "retry_interval", 5_000),
                "max_retries": getattr(self, "max_retries", 5),
                "max_retry_delay": getattr(self, "max_retry_delay", 30_000),
                "exponential_base": getattr(self, "exponential_base", 2),
            }
        else:
            self.write_options = WriteOptionsClass(
                batch_size=getattr(self, "batch_size", 25),
                flush_interval=getattr(self, "flush_interval", 10_000),
                jitter_interval=getattr(self, "jitter_interval", 2_000),
                retry_interval=getattr(self, "retry_interval", 5_000),
                max_retries=getattr(self, "max_retries", 5),
                max_retry_delay=getattr(self, "max_retry_delay", 30_000),
                exponential_base=getattr(self, "exponential_base", 2),
            )

    async def write(self, record) -> bool:
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return False

        # Use the client context helpers provided by the client implementation
        try:
            with ClientClass.from_env() as client:
                if await self._health() is False:
                    self.log("InfluxDB connection is not healthy", level="error")
                    return False
                self.log(f"Write called for record: {record}", level="debug")
                client.write(record)
                return True
        except Exception as error:
            self.log(f"Error while writing to InfluxDB: {error}", level="error")
            return False

    async def query(self, query: str) -> t.AsyncIterator:
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return

        with ClientClass.from_env_properties() as client:
            if await self._health() is False:
                self.log("InfluxDB connection is not healthy", level="error")
                return
            records = await client.query_async(query)
            async for record in records:
                yield record

    async def _health(self) -> bool:
        """
        Asynchronously checks the health of the connection to the InfluxDB server.

        This method establishes a connection with the InfluxDB client and sends a ping request. If the server responds,
        it logs that the connection is ready.

        Example:
        await self._health()

        Raises:
        Exception: If an error occurs while pinging the server.
        """
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return False

        try:
            with ClientClass.from_env() as client:
                version = client.get_server_version()
                if version:
                    self.log("InfluxDB connection is ready", level="debug")
                    return True
                else:
                    self.log("InfluxDB connection is not ready", level="warning")
                    return False
        except Exception as error:
            self.log(f"Error while pinging InfluxDB: {error}", level="error")
            return False


@note_and_log
class InfluxDBv2(InfluxDBCommon):
    """
    This class provides a connection to an InfluxDB database version 2.

    It allows for writing to and reading from the database. The connection parameters such as the URL, port, token, organization,
    and bucket are specified as class attributes.

    Attributes:
    url (str): The URL of the InfluxDB server.
    port (int): The port on which the InfluxDB server is listening.
    token (str): The token for authentication with the InfluxDB server.
    org (str): The organization for the InfluxDB server.
    timeout (int): The timeout for requests to the InfluxDB server, in milliseconds.
    bucket (str): The default bucket to use for operations.
    tags_file (str): The file containing tags for the InfluxDB server.
    username (str): The username for authentication with the InfluxDB server.
    password (str): The password for authentication with the InfluxDB server.
    client (InfluxDBClientAsync): The client for interacting with the InfluxDB server.
    """

    url = None
    port = 8086
    token = None
    org = None
    timeout = 6000
    bucket = None
    tags_file = None
    username = None
    password = None
    client: InfluxDBClient

    def __init__(self, params):
        for k, v in params.items():
            setattr(self, k, v)
        if self.bucket is None:
            raise ValueError("Missing bucket name, please provide one in db_params")
        # self.connect_to_db()
        self.points: list[t.Any] = []
        WriteOptionsClass = getattr(self, "WriteOptions", None)
        if WriteOptionsClass is None:
            self.write_options = {
                "batch_size": getattr(self, "batch_size", 25),
                "flush_interval": getattr(self, "flush_interval", 10_000),
                "jitter_interval": getattr(self, "jitter_interval", 2_000),
                "retry_interval": getattr(self, "retry_interval", 5_000),
                "max_retries": getattr(self, "max_retries", 5),
                "max_retry_delay": getattr(self, "max_retry_delay", 30_000),
                "exponential_base": getattr(self, "exponential_base", 2),
            }
        else:
            self.write_options = WriteOptionsClass(
                batch_size=getattr(self, "batch_size", 25),
                flush_interval=getattr(self, "flush_interval", 10_000),
                jitter_interval=getattr(self, "jitter_interval", 2_000),
                retry_interval=getattr(self, "retry_interval", 5_000),
                max_retries=getattr(self, "max_retries", 5),
                max_retry_delay=getattr(self, "max_retry_delay", 30_000),
                exponential_base=getattr(self, "exponential_base", 2),
            )

    async def write(self, record) -> bool:
        """
        Asynchronously writes a record to the specified bucket in the InfluxDB database.

        This method establishes a connection with the InfluxDB client and attempts to write the provided record to the specified bucket.

        Parameters:
        bucket (str): The name of the bucket to which the record will be written.
        record: The record to be written to the bucket. The record should be in a format acceptable by the InfluxDB write API.

        Example:
        await bacnet.database.write(record=my_record)

        Raises:
        Exception: If an error occurs while writing to the database.
        """
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return False

        async with ClientClass.from_env_properties() as client:
            if await self._health() is False:
                self.log("InfluxDB connection is not healthy", level="error")
                return False
            try:
                self.log(f"Write called for record: {record}", level="debug")
                write_api = client.write_api()
                success = await write_api.write(
                    bucket=self.bucket, org=self.org, record=record
                )
                self.log(f"Write response: {success}", level="debug")
                return success
            except Exception as error:
                self.log(f"Error while writing{record} to db: {error}", level="error")
                return False

    async def query(self, query: str) -> t.AsyncIterator:
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return

        async with ClientClass.from_env_properties() as client:
            if await self._health() is False:
                self.log("InfluxDB connection is not healthy", level="error")
                return
            query_api = client.query_api()
            records = await query_api.query_stream(query)
            async for record in records:
                yield record

    async def delete(
        self,
        predicate: str,
        value: str,
        start: datetime = datetime.fromtimestamp(0, timezone.utc),
        stop: datetime = datetime.now(timezone.utc),
        bucket: t.Optional[str] = None,
    ) -> bool:
        """
         Asynchronously delete data from the specified bucket in the InfluxDB database.

        This method deletes all records that match the specified predicate and value
        within the given time range (start and stop).

        Parameters:
        predicate (str): The field to match for deletion.
        value (str): The value that the predicate field should have for a record to be deleted.
        start (datetime, optional): The start of the time range for deletion. Defaults to the Unix epoch.
        stop (datetime, optional): The end of the time range for deletion. Defaults to the current time.
        bucket (str, optional): The name of the bucket from which to delete. If not provided, defaults to the instance's bucket.

        Example:
        await bacnet.database.delete(predicate="object", value="virtual:73195493", bucket="BAC0_Test")

        Returns:
        bool: True if the deletion was successful, False otherwise.

        Raises:
        Exception: If an error occurs while deleting.
        """
        if bucket is None:
            bucket = self.bucket
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return False

        async with ClientClass.from_env_properties() as client:
            if await self._health() is False:
                self.log("InfluxDB connection is not healthy", level="error")
                return False
            try:
                start = start
                stop = stop
                # Delete data with location = 'Prague'
                successfully = await client.delete_api().delete(
                    start=start,
                    stop=stop,
                    bucket=bucket,
                    predicate=f'{predicate} = "{value}"',
                )
                return successfully
            except Exception as error:
                self.log(f"Error while deleting from db: {error}", level="error")
                return False

    async def _health(self) -> bool:
        """
        Asynchronously checks the health of the connection to the InfluxDB server.

        This method establishes a connection with the InfluxDB client and sends a ping request. If the server responds,
        it logs that the connection is ready.

        Example:
        await self._health()

        Raises:
        Exception: If an error occurs while pinging the server.
        """
        ClientClass = getattr(self, "InfluxDBClient", None)
        if ClientClass is None:
            self.log("InfluxDB client class not available", level="error")
            return False

        async with ClientClass.from_env_properties() as client:
            try:
                ready = await client.ping()
                if ready:
                    self.log("InfluxDB connection is ready", level="debug")
                    return True
                else:
                    self.log("InfluxDB connection is not ready", level="warning")
                    return False
            except Exception as error:
                self.log(f"Error while pinging InfluxDB: {error}", level="error")
                return False

    def read_last_value_from_db(self, id=None):
        # example id : Device_5004/analogInput:1
        # maybe use device name and object name ?
        # This must be easy

        f"""
        from(bucket: {self.bucket}")
        |> range(start: -100y)
        |> filter(fn: (r) => r["description"] == "DA-T")
        |> filter(fn: (r) => r["_field"] == "value")
        |> last()
        |> yield(name: "last")
        """
        pass


class ConnectionError(Exception):
    pass
