.. _database:

Database
================
By default, all data is saved on a SQLite instance where BAC0 run. 
In some circumstances, it could be required to send data to a more powerful database.
For that reason, support for [InfluxDB](https://docs.influxdata.com/influxdb/v2.0/) has been added to BAC0.
I'm trying to make that flexible to allow other databases to be use eventually, using the same db_params 
argument when creating the network object.

This is still a work in progress.

SQL
------------
Technically, BAC0 sends everything to SQLite locally. It would be possible to make some configuration changes 
to connect to a SQL database as SQLite share mostly the same commands (This is not actually implemented). 
Even if another database is configured, the local SQLite file will be used.


.. _database_influxdb:

InfluxDB
--------------------
Work is done using InfluxDB v2.0 OSS. 
My setup is a RaspberryPi 4 running Ubuntu Server 64-bit

InfluxDB is installed on the RPi using default options.
BAC0 will point to a Bucket (ex. named BAC0) using a token created 
in the InfluxDB web interface (ex. http://ip_of_rpi:8086)

To create the dashboard, I use [Grafana](https://grafana.com/oss/)
which is also installed on the same RaspberryPi. (ex. http://ip_of_rpi:3000)

.. note:: 
    The python client used works also for InfluxDB v1.8+. Connecting to this version
    is supported and you must pass a username and a password in db_params

.. _database_influxdb_connection:

Connection 
............
For BAC0 to connect to the InfluxDB server, it needs to know where to send the data.
This information can be given by using a dict ::

    _params = {"name": "InfluxDB",
               "url" : "http://ip_of_rpi",
               "port" : 8086,
               "token" : "token_created in influxDB web interface",
               "org" : "the organization you created",
               "bucket" : "BAC0"
               # (V1.8) "user" : " ",
               # (v1.8) "password" : "",
               }

Then you pass this information when you instantiate `bacnet`

    bacnet = BAC0.lite(db_params=_params)

The information can also be provided as environment variables. In that
case, you must still provide name and bucket ::

    _params = {"name": "InfluxDB",
               "bucket" : "BAC0"
               }

To use environment variables, BAC0 will count on python-dotenv to 
load a .env file in the folder when BAC0 is used.

The .env file must contain ::

    # InfluxDB Params Example .env file
    INFLUXDB_V2_URL=http://192.168.1.10:8086
    INFLUXDB_V2_ORG=my-org
    INFLUXDB_V2_TOKEN=123456789abcdefg
    # INFLUXDB_V2_TIMEOUT= 
    # INFLUXDB_V2_VERIFY_SSL= 
    # INFLUXDB_V2_SSL_CA_CERT= 
    # INFLUXDB_V2_CONNECTION_POOL_MAXSIZE= 
    # INFLUXDB_V2_AUTH_BASIC=
    # INFLUXDB_V2_PROFILERS=

.. note:: 
    The name parameters in db_params would be use if any other implementation is made for another product.
    For now, only InfluxDB is valid. 

.. _database_influxdb_write_options:

Write Options configuration
............................
Other options can be provided in the db_params dict to fine tune the configuration of the write_api.

    * batch_size (default = 25)
    * flush_interval (default =10 000)
    * jitter_interval (default = 2 000)
    * retry_interval (default = 5 000)
    * max_retries (default = 5)
    * max_retry_delay (default = 30 000)
    * exponential_base (default = 2)

Please refer to InfluxDB documentation for all the details regarding those parameters.

ex. ::

        _params = {"name": "InfluxDB",
                "bucket" : "BAC0",               
                "batch_size" : 25,
                "flush_interval" : 10000,
                "jitter_interval" : 2000,
                "retry_interval" : 5000,
                "max_retries" : 5,
                "max_retry_delay" : 30000,
                "exponential_base" : 2,
               }

Timestamp
..............
Now all timestamps in BAC0 will be timezone aware. As long as you are using 
in-memory data, the actual timezone will be used. I didn't want to mess with 
the timestamp for day to day work requiring only quick histories and minor tests.
But all timestamps that will be sent to InfluxDB will be converted to UTC. 
This is a requirement and makes things work well with Grafana.

API
.............
BAC0 will use the Python package named influxdb-client, which must be pip installed.

    pip install 'influxdb-client'

Refer to [documentation](https://github.com/influxdata/influxdb-client-python) for details.

In my actual tests, I haven't work with ciso8601, RxPy neither. 

The API will accumulate write requests and write them in batch that are configurable. The actual 
implementation use 25 as the batch parameters. This is subject to change.

Write all
.............
I have included a function that write all histories to InfluxDB. This function takes
all the Pandas Series and turn them into a DataFrame which is then sent to InfluxDB.

I'm not sure if it's really useful as the polling takes care of sending the data 
constantly. 

.. _database_influxdb_writing_cadence:

Writing cadence
........................
BAC0 batches point values in memory and writes them to InfluxDB on a periodic background task:

- Each new point value read is added to a batch in memory.
- A background task flushes batched points to InfluxDB every ``write_interval`` seconds (set via ``db_params``).
- If the database is temporarily unavailable, the task logs the error and restarts.

ID of the record
.................
The ID of the record will be ::

    Device_{device_id}/{object} 

For example ::

    Device_5004/analogInput:1

This choice was made to make sure all records ID were unique as using name could lead to errors. As name, 
device name, etc are provided as tags, I suggest using them in the Flux requests. 

Tags and fields
..................
InfluxDB allows the usage of tags and multiple fields for values. This allows making requests 
based on tags when creating dashboard. I chose to add some information in the form of tags 
when writing to the database : 

 * object_name
 * description
 * units_state (units of measure or state text for multiState and Binary)
 * object instance (ex. analogInput:1)
 * device_name (the name of the controller)
 * device_id (the device instance)

value
...........

Two value fields are included. A value field and a string_value field.
This way, when working with binary or multistate, it's possible to use
aggregation functions using the numerical value (standard value), but it is
also possible to make database request on the string_value field and get 
a more readable result (ex. Occupied instead of 0)

Viewing data and dashboards
---------------------------
You can explore data and build dashboards directly in the InfluxDB UI or in Grafana.

InfluxDB UI (Data Explorer)
............................
Build Flux queries by measurement or tags.

- Filter by a specific object instance (measurement)::

    from(bucket: "BAC0")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "Device_5004/analogInput:1")
        |> filter(fn: (r) => r._field == "value")

- Filter all analog inputs for a device by tag::

    from(bucket: "BAC0")
        |> range(start: -1h)
        |> filter(fn: (r) => r.device_id == "5004")
        |> filter(fn: (r) => r.object =~ /analog/)
        |> filter(fn: (r) => r._field == "value")

Grafana
........
- Add InfluxDB 2.x as a data source (URL, org, token).
- Create panels using Flux queries like the examples above.

Tips
.....
- Ensure BAC0 devices are being polled so values update and get batched.
- Use point tags (e.g., zone, floor) to simplify filtering in dashboards.
- For binary/multistate displays, plot ``string_value`` or map numeric ``value``.

