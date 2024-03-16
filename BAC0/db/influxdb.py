try:
    from influxdb_client import Point, WriteOptions
    from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
except ImportError:
    raise ImportError("Install influxdb to use this feature")

import pytz
import asyncio

from ..core.utils.notes import note_and_log
from ..core.devices.Virtuals import VirtualPoint


@note_and_log
class InfluxDB:
    """
    Connection to InfluxDB to write to DB or to read from it
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
    client: InfluxDBClientAsync

    def __init__(self, params):
        for k, v in params.items():
            setattr(self, k, v)
        if self.bucket is None:
            raise ValueError("Missing bucket name, please provide one in db_params")
        # self.connect_to_db()
        self.points = []
        self.write_options = WriteOptions(
            batch_size=getattr(self, "batch_size", 25),
            flush_interval=getattr(self, "flush_interval", 10_000),
            jitter_interval=getattr(self, "jitter_interval", 2_000),
            retry_interval=getattr(self, "retry_interval", 5_000),
            max_retries=getattr(self, "max_retries", 5),
            max_retry_delay=getattr(self, "max_retry_delay", 30_000),
            exponential_base=getattr(self, "exponential_base", 2),
        )

    async def write(self, bucket, record):
        async with InfluxDBClientAsync.from_env_properties() as client:
            try:
                self._log.info(f"Write called for record: {record}")
                write_api = client.write_api()
                response = await write_api.write(
                    bucket=bucket, org=self.org, record=record
                )
                self._log.info(f"Write response: {response}")
            except Exception as error:
                self._log.error(f"Error while writing to db: {error}")

    async def query(self, query):
        async with InfluxDBClientAsync.from_env_properties() as client:
            query_api = client.query_api()
            records = await query_api.query_stream(query)
            async for record in records:
                yield record

    async def _health(self):
        async with InfluxDBClientAsync.from_env_properties() as client:
            ready = await client.ping()
            if ready:
                self._log.info("InfluxDB connection is ready")

    def clean_value(self, object_type, val, units_state):
        try:
            if "analog" in object_type:
                _string_value = "{:.3f} {}".format(val, units_state)
                _value = val
            elif "multi" in object_type:
                _string_value = "{}".format(val.split(":")[1])
                _value = int(val.split(":")[0])
            elif "binary" in object_type:
                try:
                    _string_value = "{}".format(units_state[int(val.split(":"[0]))])
                except Exception:
                    try:
                        _value, _string_value = val.split(":")
                        _value = int(_value)
                    except Exception as error:
                        self._log.error(
                            f"Error while cleaning value {val} of object type {object_type}: {error}"
                        )
            else:
                _string_value = "{}".format(val)
                _value = val
            return (_value, _string_value)
        except AttributeError as error:
            self._log.error(
                f"Error while cleaning value {val} of object type {object_type}: {error}"
            )

    def prepare_point(self, list_of_points):
        _points = []

        for point in list_of_points:
            _object_name = point.properties.name
            _devicename = point.properties.device.properties.name
            _device_id = point.properties.device.properties.device_id
            _units_state = "{}".format(point.properties.units_state)
            _description = point.properties.description
            _object = "{}:{}".format(point.properties.type, point.properties.address)
            _value, _string_value = self.clean_value(
                point.properties.type, point.lastValue, point.properties.units_state
            )
            _name = "{}/{}".format(_devicename, _object_name)
            _id = "Device_{}/{}".format(_device_id, _object)
            _point = (
                Point(_id)
                .tag("object_name", _object_name)
                .tag("name", _name)
                .tag("description", _description)
                .tag("units_state", _units_state)
                .tag("object", _object)
                .tag("device", _devicename)
                .tag("device_id", _device_id)
                .field("value", _value)
                .field("string_value", _string_value)
                .time(point.lastTimestamp.astimezone(pytz.UTC))
            )
            for each in point.tags:
                _tag_id, _tag_value = each
                _point.tag(_tag_id, _tag_value)
            self.points.append(_point)

    async def write_points_lastvalue_to_db(self, list_of_points):
        """
        Writes a list of points to the InfluxDB database.

        Args:
            list_of_points (list): A list of points to be written to the database.

        Returns:
            None
        """

        self._log.debug(f"Writing to db: {self.points}")
        success = await self.write(self.bucket, self.points)
        if success:
            self.points = []

    def read_last_value_from_db(self, id=None):
        # example id : Device_5004/analogInput:1
        # maybe use device name and object name ?
        # This must be easy

        """
        from(bucket: {}")
        |> range(start: -100y)
        |> filter(fn: (r) => r["description"] == "DA-T")
        |> filter(fn: (r) => r["_field"] == "value")
        |> last()
        |> yield(name: "last")
        """.format(
            self.bucket
        )
        pass

    #    def example(self, device_name, object_name):
    #        p = {"_bucket": self.bucket,
    #             "_start": datetime.timedelta(hours=-1),
    #             "_location": "Prague",
    #             "_desc": True,
    #             "_floatParam": 25.1,
    #             "_every": datetime.timedelta(minutes=5)
    #            }
    #
    #        tables = self.query_api.query('''
    #            from(bucket:_bucket) |> range(start: _start)
    #                |> filter(fn: (r) => r["_measurement"] == "my_measurement")
    #                |> filter(fn: (r) => r["_field"] == "temperature")
    #                |> filter(fn: (r) => r["location"] == _location and r["_value"] > _floatParam)
    #                |> aggregateWindow(every: _every, fn: mean, createEmpty: true)
    #                |> sort(columns: ["_time"], desc: _desc)
    #        ''', params=p)
    #        return tables

    def read_flux(self, request, params):
        pass


class ConnectionError(Exception):
    pass
