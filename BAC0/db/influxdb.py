from datetime import datetime

import pytz

from ..core.utils.lookfordependency import influxdb_if_available
from ..core.utils.notes import note_and_log


_INFLUX, _ = influxdb_if_available()
if _INFLUX:
    from influxdb_client import Point, WriteOptions
    from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
else:
    raise ImportError("Install influxdb to use this feature")


@note_and_log
class InfluxDB:
    """
    This class provides a connection to an InfluxDB database.

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

    async def write(self, bucket: str, record) -> bool:
        """
        Asynchronously writes a record to the specified bucket in the InfluxDB database.

        This method establishes a connection with the InfluxDB client and attempts to write the provided record to the specified bucket.

        Parameters:
        bucket (str): The name of the bucket to which the record will be written.
        record: The record to be written to the bucket. The record should be in a format acceptable by the InfluxDB write API.

        Example:
        await bacnet.database.write(bucket="BAC0_Test", record=my_record)

        Raises:
        Exception: If an error occurs while writing to the database.
        """
        async with InfluxDBClientAsync.from_env_properties() as client:
            try:
                self.log(f"Write called for record: {record}", level="debug")
                write_api = client.write_api()
                success = await write_api.write(
                    bucket=bucket, org=self.org, record=record
                )
                self.log(f"Write response: {success}", level="debug")
                return success
            except Exception as error:
                self.log(f"Error while writing{record} to db: {error}", level="error")
                return False

    async def query(self, query: str) -> list:
        async with InfluxDBClientAsync.from_env_properties() as client:
            query_api = client.query_api()
            records = await query_api.query_stream(query)
            async for record in records:
                yield record

    async def delete(
        self,
        predicate: str,
        value: str,
        start: datetime = datetime.utcfromtimestamp(0),
        stop: datetime = datetime.now(),
        bucket: str = None,
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
        async with InfluxDBClientAsync.from_env_properties() as client:
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
        async with InfluxDBClientAsync.from_env_properties() as client:
            ready = await client.ping()
            if ready:
                self.log("InfluxDB connection is ready", level="info")
                return True
            else:
                self.log("InfluxDB connection is not ready", level="error")
                return False

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
        _points = []

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

        self.log(f"Writing to db: {self.points}", level="debug")
        success = await self.write(self.bucket, self.points)
        if success:
            self.points = []

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
