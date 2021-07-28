try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions

except ImportError:
    raise ImportError("Install influxdb to use this feature")

import pytz


class InfluxDB:
    """
    Connection to InfluxDB to write to DB or to read from it
    """

    url = None
    port = 8086
    token = None
    org = None
    bucket = None
    tags_file = None

    def __init__(self, params):
        # params should be a dict with name=InfluxDB and bucket=valid_bucket_to_use.
        # optional params : url, port, token and org may be provided
        # if they are not provided, BAC0 will try to get them from environment
        # variables that shoudl have been provided in a .env file, which is loaded
        # when BAC0 is imported.
        for k, v in params.items():
            setattr(self, k, v)
        if self.bucket is None:
            raise ValueError("Missing bucket name, please provide one in db_params")
        if self.url is None:
            # Will try environment variables
            self.client = InfluxDBClient.from_env_properties()
        else:
            _url = "{}:{}".format(self.url, self.port)
            self.client = InfluxDBClient(url=_url, token=self.token)

        self.write_api = self.client.write_api(
            write_options=WriteOptions(
                batch_size=getattr(self, "batch_size", 25),
                flush_interval=getattr(self, "flush_interval", 10_000),
                jitter_interval=getattr(self, "jitter_interval", 2_000),
                retry_interval=getattr(self, "retry_interval", 5_000),
                max_retries=getattr(self, "max_retries", 5),
                max_retry_delay=getattr(self, "max_retry_delay", 30_000),
                exponential_base=getattr(self, "exponential_base", 2),
            )
        )

    def clean_value(self, object_type, val, units_state):
        if "analog" in object_type:
            _string_value = "{:.3f} {}".format(val, units_state)
            _value = val
        elif "multi" in object_type:
            _string_value = "{}".format(val.split(":")[1])
            _value = "{}".format(val.split(":")[0])
        elif "binary" in object_type:
            try:
                _string_value = "{}".format(units_state[int(val.split(":"[0]))])
            except:
                _string_value = "{}".format(val.split(":")[1])
            _value = "{}".format(val.split(":")[0])
        else:
            _string_value = "{}".format(val)
            _value = val
        return (_value, _string_value)

    def write_points_lastvalue_to_db(self, list_of_points):
        _points = []

        for point in list_of_points:
            _object_name = point.properties.name
            _devicename = point.properties.device.properties.name
            _device_id = point.properties.device.properties.device_id
            _name = "{}/{}".format(_devicename, _object_name)
            _units_state = "{}".format(point.properties.units_state)
            _description = point.properties.description
            _object = "{}:{}".format(point.properties.type, point.properties.address)
            _value, _string_value = self.clean_value(
                point.properties.type, point.lastValue, point.properties.units_state
            )
            _point = (
                Point(_name)
                .tag("object_name", _object_name)
                .tag("description", _description)
                .tag("units_state", _units_state)
                .tag("object", _object)
                .tag("device", _devicename)
                .tag("device_id", _device_id)
                .field("value", _value)
                .field("string_value", _string_value)
                .time(point.lastTimestamp.astimezone(pytz.UTC))
            )
            # TODO: At this point, it would be cool to add more tags coming from an external source...
            _points.append(_point)
        self.write_api.write(self.bucket, self.org, _points)

    def write_all_to_db(self, device):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("You need pandas and numpy to write all histories to db")
        _value = None

        for each in device:
            _object = "{}:{}".format(each.properties.type, each.properties.address)
            _object_name = each.properties.name
            _description = each.properties.description
            _units_state = each.properties.units_state
            _devicename = each.properties.device.properties.name
            _device_id = each.properties.device.properties.device_id
            _name = "{}/{}".format(_devicename, _object_name)
            _data = {"value": each.history}
            _df = pd.DataFrame(_data)
            _df.index = _df.index.tz_convert(pytz.utc)
            _df["value"] = _df.apply(
                lambda x: self.clean_value(
                    each.properties.type, x["value"], each.properties.units_state
                )[0],
                axis=1,
            )
            _df["string_value"] = _df.apply(
                lambda x: self.clean_value(
                    each.properties.type, x["value"], each.properties.units_state
                )[1],
                axis=1,
            )
            _df["object_name"] = _object_name
            _df["description"] = _description
            _df["units_state"] = "{}".format(_units_state)
            _df["object"] = _object
            _df["device"] = _devicename
            _df["device_id"] = _device_id
            try:
                # print(_name)
                self.write_api.write(
                    self.bucket,
                    org=self.org,
                    record=_df,
                    data_frame_measurement_name=_name,
                    data_frame_tag_columns=[
                        "object_name",
                        "description",
                        "units_state",
                        "object",
                        "device",
                        "device_id",
                    ],
                )
            except Exception as error:
                # print('Oups', _name, error)
                continue

    def read_last_value_from_db(self, value):
        pass
