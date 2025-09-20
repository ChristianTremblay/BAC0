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
BAC0 supports InfluxDB v2.0 OSS and InfluxDB v3.0. 
Example setup could be a RaspberryPi 4 running Ubuntu Server 64-bit
Or a Docker container running on any machine.


InfluxDB is installed on the RPi using default options.
BAC0 will point to a Bucket (ex. named BAC0) using a token created 
in the InfluxDB web interface (ex. http://ip_of_rpi:8086)

To create the dashboard, I use [Grafana](https://grafana.com/oss/)
which is also installed on the same RaspberryPi. (ex. http://ip_of_rpi:3000)

.. note:: 
    The python client used works also for InfluxDB v1.8+. You must pass a username and a password in db_params. That said, I will not support versions below 2

.. _database_influxdb_connection:

Connection 
............
For BAC0 to connect to the InfluxDB server, it needs to know where to send the data.
This information can be given by using a dict ::

    _params = {"name": "InfluxDB",
               "version": 2, # set to 2 or 3 depending on your InfluxDB server
               "url" : "http://ip_of_rpi",
               "port" : 8086,
               "token" : "token_created in influxDB web interface",
               "org" : "the organization you created",
               "bucket" : "BAC0",
                }

    .. note::
        For InfluxDB v3 instances the field name `bucket` has been replaced by `database`.
        If you are using version 3, provide the database name using::

            _params = {"name": "InfluxDB",
                       "database": "BAC0",
                       "version": 3,
                       # other connection keys (url/token/org) ...
                      }

Then you pass this information when you instantiate `bacnet`

    bacnet = BAC0.start(db_params=_params)

The information can also be provided as environment variables. In that
case, you must still provide name and bucket (or database) ::

    _params = {"name": "InfluxDB",
               "version": 3,
               "database" : "BAC0"
               }

Note
::::
    It is required to include the database client version in your `db_params` using the `version` key. Use

    ``"version": 2``  or  ``"version": 3``

    to select the client implementation. If omitted some code paths may default to v2, so prefer setting it explicitly.

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

Additional InfluxDB v3 notes
----------------------------
When creating the database helper via `db_params` ensure you set ``"version": 3`` in the params dict so the v3 client implementation will be used.


Support for InfluxDB v3 core is available (optional dependency). When using v3 you can provide connection
information via environment variables (the project ships an example `.env~`):

    INFLUX_HOST=192.168.1.10:8181
    INFLUX_ORG=my-org
    INFLUX_DATABASE=my_database
    INFLUX_TOKEN=123456789abcdefg

On Windows: gRPC DNS resolver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

InfluxDB v3 uses gRPC for some operations. On Windows, the gRPC DNS resolver may fail in some environments. Set:

    GRPC_DNS_RESOLVER=native

in your environment (for example in your `.env` file) to force gRPC to use the platform native resolver and avoid DNS errors when querying.

Example usage (InfluxDB v3)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's a small example showing how to acquire a client from environment and run a query. Adjust the query to your schema and client library semantics:

.. code-block:: python

    dbc = bacnet.database.InfluxDBClient
    with dbc.from_env() as client:
        # health helper returns True/False depending on client availability
        print(await bacnet.database._health())
        print(client.get_server_version())
        resp = client.query("SELECT * FROM 'Device_5221/analog-input:10056' WHERE time >= now() - interval '5 minutes'")
        print(resp)

Table (Measurement) strategy (v2 vs v3)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As of the latest change, the v3 implementation writes all points into a single shared measurement (table) rather than creating one measurement per variable. This simplifies queries and is the recommended default for new deployments. Identification of variables is preserved using tags (for example `device_id`, `object`, `object_name`, `name`, etc.), so queries should filter by tags instead of by measurement name.

Example query (v3, single table with a name provided in params)::

    SELECT time, name, value
    FROM myTable
    WHERE name IN ('${Names:csv}') AND time > $__timeFrom and time < $__timeTo

.. note:: 
    Here, Names would be a variable created in Grafana, see below. Dashes are critical to escape special characters.

Compatibility note
------------------

The older v2 behavior (one measurement per variable) is still supported for v2 instances. When migrating to v3, update dashboards and queries to use tag-based filtering against the single measurement.

Grafana variable
-----------------
To get all Names in a Variable (so it can be used in a dashboard query):

    SELECT DISTINCT name from myTable

Configuration note
^^^^^^^^^^^^^^^^^^^

If you provide both a host which already includes a port (for example `192.168.1.10:8181`) and a separate `port` configuration, the constructed URI can end up with two ports (for example `grpc+tcp://docker.servisys.com:8181:443`) producing a syntax error. Prefer one of the following:

- Pass a full URL/host including port and do not set a separate `port` field.
- Or pass host and a numeric `port` separately (host without a trailing `:port`).

If you prefer, a small normalization helper can be added to the code to automatically sanitize host+port combinations before creating the client.

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

Viewing data and dashboards (Version 2)
----------------------------------------
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

Viewing data and dashboards (Version 3)
----------------------------------------
InfluxDB3 do not provide a web dashboard tool anymore.
InfluxDB 3 does not include a built-in dashboard UI. Use Grafana to build dashboards.

- Install Grafana (Docker or package).
- Add a data source for “InfluxDB v3 / Flight SQL.” If not listed, install the official InfluxDB v3/Flight SQL Grafana plugin.
- Configure the data source with your InfluxDB 3 host, TLS settings, database name, and token.
- Build panels using SQL queries. Example patterns:
  
  - Numeric trend:
  
    ::
      
      SELECT time, value
      FROM my_measurement
      WHERE device_id = '4221'
      ORDER BY time

  - Binary/multistate:
  
    ::
      
      SELECT time, string_value AS state
      FROM my_measurement
      WHERE object_name = 'ZN-T'
      ORDER BY time

Tip: Expose tags (e.g., ``zone``, ``floor``) as Grafana template variables to filter panels.

Default tags and fields written by BAC0
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When BAC0 writes points it attaches a set of default tags and fields that are useful for filtering and dashboarding. The typical chain (using the client Point API) looks like:

    - object_name
    - name
    - description
    - units_state
    - object
    - device
    - device_id


Use these tags in your Grafana/SQL queries to filter and group results (for v3 the single-measurement design relies on tags to target subsets of data).
