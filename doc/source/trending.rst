Trends
======
Trending is a nice feature when you want to see what's going on. Until now,
it was possible to use matplotlib directly in Jupyter_ to show trends.

Matplotlib
----------
Matplotlib_ is a well know library for plotting with python. As historical data are
pandas Series or DataFrame, it's possible to use Matplotlib with BAC0.
Show a chart using matplotlib::

    %matplotlib notebook
    # or matplotlib inline for a basic interface
    controller['nvoAI1'].history.plot()

|matplotlib|

Bokeh
-----
But I recently got aware of Bokeh_ which brings a complete new set of wonderful
features to see trends. Best of all, the ability to see Live Trends of your data.

Default trending features of BAC0 now depends on Bokeh_ library

Bokeh serve
-----------
To be able to use live trending features, a bokeh server needs to run locally on the machine.
When the application starts, a bokeh server will be started in a subprocess.
This server is available on localhost:5006, on your machine.

It's a shortcut so the user don't have to think about starting the server using::

    bokeh serve

Note : Once started, the bokeh server won't be stopped by the BAC0. It will terminate when
Jupyter session will be closed.

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

At startup, the script will give you the complete address to reach to get access
to the trends ::

    Click here to open Live Trending Web Page
    http://localhost:5006/?bokeh-session-id=f9OdQd0LWSPXsnuNdCqVSoEa5xxwd32cZR0ioi9ACXzl

Bokeh Features
--------------
You'll get access to live stream of data and all the features of bokeh (zooming, span, etc.)
For more details, see http://www.bokehplots.com

Numerous options are provided by Bokeh plots like a hover tool.

|bokeh_hover|

And a lot of other options like pan, box zoom, mouse wheel zoom, save, etc...

|bokeh_tools|

By default, x-axis will be a timeseries and will be linked between trends. So if you span one, 
or zoom one, the other plots will follow, giving you the eaxct same x-axis for every plots.

.. |bokeh_plots| image:: images/bokeh_trends_1.png
.. |bokeh_tools| image:: images/bokeh_tools.png
.. |bokeh_hover| image:: images/bokeh_hover.png
.. |matplotlib| image:: images/matplotlib.png
.. _Bokeh : http://www.bokehplots.com
.. _Jupyter : http://jupyter.org
.. _Matplotlib : http://matplotlib.org