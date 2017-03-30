Trends
======
Trending is a nice feature when you want to see how a points value changed over time.
Until now, this was only possible using matplotlib directly in Jupyter_.
But I recently became aware of Bokeh_ [http://bokeh.pydata.org/en/latest/] which brings 
a complete set of wonderful features for visualizing point histories (a.k.a. trends). 
The best feature of all - the ability to see Live Trends of your data as it occurs.

Matplotlib
----------
Matplotlib_ is a well known data plotting library for Python. As BAC0's historical point data 
are pandas Series and DataFrames, it's possible to use Matplotlib with BAC0.
i.e. Showing a chart using matplotlib::

    %matplotlib notebook
    # or matplotlib inline for a basic interface
    controller['nvoAI1'].history.plot()

|matplotlib|


Bokeh
-----
Bokeh is a Python interactive visualization library targeting modern web browsers for presentation. 
Its goal is to provide elegant, concise graphics, with high-performance interactivity over very large 
or streaming datasets. Bokeh can help anyone who would like to quickly create interactive plots, dashboards, 
and data applications.

BAC0 trending features use Bokeh by default.


Bokeh serve
-----------
To use the live trending features, a bokeh server needs to be running locally on your computer.
When the BAC0 starts, it starts a bokeh server for you, running locally.  This server is available 
at localhost:5006, on your machine.

The server can be started manually, from the command line via::

    bokeh serve

Note : Once started, the bokeh server won't be stopped by the BAC0. It will terminate when your 
Jupyter session is closed.


Add plots to Bokeh Document
---------------------------
The web page seen on the server is called a document. You open it through a session which is
given by the script at startup.
Empty at first, you need to send the data you want to the server using ::

    # This script will add four plots to the server
    lst = ['nvoAI1', 'nvoAI2', 'nvoDO1', 'nvoTempRdC']
    fx.chart(lst, title = 'First Floor temperature')
    
    lst2 = ['nvoAI3']
    fx.chart(lst2, title = 'Outdoor Temp')
    
    lst3 = ['nvoPCCTAli', 'nvoAI1']
    fx.chart(lst3, title = 'Discharge Air Temp and setpoint')
    
    lst4 = ['nvoEffTempEtage', 'nvoEffPCEtage']
    fx.chart(lst4, title = 'Heating second floor')

|bokeh_plots|

At startup, BAC0 prints the complete URL address for your web browser to view trends ::

    Click here to open Live Trending Web Page
    http://localhost:5006/?bokeh-session-id=f9OdQd0LWSPXsnuNdCqVSoEa5xxwd32cZR0ioi9ACXzl


Bokeh Features
--------------
Bokeh has an extensive set of features. Exploring them is beyond the scope of this documentation.
Instead you may discover them yourself at [http://www.bokehplots.com].
A couple of its features are highlighted below.

Hover tool:

|bokeh_hover|

And a lot of other options like pan, box zoom, mouse wheel zoom, save, etc...:

|bokeh_tools|

By default, x-axis will be a timeseries and will be linked between trends. So if you span one, 
or zoom one, the other plots will follow, giving you the eaxct same x-axis for every plots.

Bokeh Demo
----------
Here is a working demo of Bokeh. It's taken from a real life test. You can use all the features (zoom, pan, etc.)
Please note that the hover suffers from a little bug in this "saved" version of the trends... Working to solve this.

.. raw:: html
   :file: images/demo1.html


.. |bokeh_plots| image:: images/bokeh_trends_1.png
.. |bokeh_tools| image:: images/bokeh_tools.png
.. |bokeh_hover| image:: images/bokeh_hover.png
.. |matplotlib| image:: images/matplotlib.png
.. _Bokeh : http://www.bokehplots.com
.. _Jupyter : http://jupyter.org
.. _Matplotlib : http://matplotlib.org