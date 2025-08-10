Trends
======
Trending is a nice feature when you want to see how a points value changed over time.
You can plot quick histories in notebooks with Matplotlib_/Seaborn_ and, for live dashboards,
stream point values to InfluxDB and visualize them in the InfluxDB UI or Grafana. See the Database page for full setup and usage:

- InfluxDB overview and connection: :ref:`database_influxdb` and :ref:`database_influxdb_connection`
- Write cadence and data model: :ref:`database_influxdb_writing_cadence`
- Viewing data and dashboards: :ref:`database`

Note: The legacy Bokeh-based web interface has been removed from BAC0. Use InfluxDB for live trending.

Matplotlib
----------
Matplotlib_ is a well known data plotting library for Python. As BAC0's historical point data 
are pandas Series and DataFrames, it's possible to use Matplotlib with BAC0.
i.e. Showing a chart using matplotlib::

    %matplotlib notebook
    # or matplotlib inline for a basic interface
    controller['nvoAI1'].history.plot()

|matplotlib|

Seaborn
-------
Seaborn_ is a library built over Matplotlib_ that extends the possibilities of creating statistical
trends of your data. I strongly suggest you have a look to this library.

Live trends with InfluxDB
-------------------------
BAC0 can periodically write point values to InfluxDB and you can create live charts in the InfluxDB UI or Grafana.
For step-by-step setup, data model, write cadence, and dashboard examples, see :ref:`database_influxdb`.


.. |matplotlib| image:: images/matplotlib.png
.. _Jupyter : http://jupyter.org
.. _Matplotlib : http://matplotlib.org
.. _Seaborn : http://seaborn.pydata.org
.. _berryconda : https://github.com/jjhelmus/berryconda
