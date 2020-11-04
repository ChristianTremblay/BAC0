Histories in BAC0
====================

Histories in BAC0 were first introduced as the result of every reading the software made on
each points, to keep trace of what was going on. It is different from the BACnet TrendLog object
that may be configured in a device to keep history records in the memory of the controller.

Everytime a value is read in BAC0, the value will be stored in memory as what will be called
from here : history.

TrendLog will also being accessible but for now, let's focus on BAC0's histories.

BAC0 uses the Python Data Analysis library **pandas** [http://pandas.pydata.org/] to 
maintain histories of point values over time.  All points are saved by BAC0 in a **pandas** 
Series every 10 seconds (by default).  This means you will automatically have historical data 
from the moment you connect to a BACnet device.

Access the contents of a point's history is very simple.::
    
    controller['pointName'].history

Example ::

    controller['Temperature'].history
    2017-03-30 12:50:46.514947    19.632507
    2017-03-30 12:50:56.932325    19.632507
    2017-03-30 12:51:07.336394    19.632507
    2017-03-30 12:51:17.705131    19.632507
    2017-03-30 12:51:28.111724    19.632507
    2017-03-30 12:51:38.497451    19.632507
    2017-03-30 12:51:48.874454    19.632507
    2017-03-30 12:51:59.254916    19.632507
    2017-03-30 12:52:09.757253    19.536366
    2017-03-30 12:52:20.204171    19.536366
    2017-03-30 12:52:30.593838    19.536366
    2017-03-30 12:52:40.421532    19.536366
    dtype: float64


.. note:: 
    **pandas** is an extensive data analysis tool, with a vast array of data manipulation operators.
    Exploring these is beyond the scope of this documentation.  Instead we refer you to this 
    cheat sheet [https://github.com/pandas-dev/pandas/blob/master/doc/cheatsheet/Pandas_Cheat_Sheet.pdf] and 
    the pandas website [http://pandas.pydata.org/].

History Size
--------------
By default, BAC0 provides an unlimited history_size per points (number of records). But it could be 
useful in certain cases when the script will run for a long period of time and you want to keep
control over memory ::

    dev = BAC0.device('2:4',4,bacnet,history_size=2)
    # or after...
    dev.update_history_size(100)
    # or just on one point : 
    dev['point'].properties.history_size = 30

Resampling data
--------------- 
One common task associated with point histories is preparing it for use with other tools.
This usually involves (as a first step) changing the frequency of the data samples - called 
**resampling** in pandas terminology.

Since the point histories are standard pandas data structures (DataFrames, and Series), you can 
manipulate the data with pandas operators, as follows.::

    # code snipet showing use of pandas operations on a BAC0 point history.
   
    # Resample (consider the mean over a period of 1 min)    
    tempPieces = {
            '102_ZN-T' : local102['ZN-T'].history.resample('1min'),
            '102_ZN-SP' : local102['ZN-SP'].history.resample('1min'),
            '104_ZN-T' : local104['ZN-T'].history.resample('1min'),
            '104_ZN-SP' : local104['ZN-SP'].history.resample('1min'),
            '105_ZN-T' : local105['ZN-T'].history.resample('1min'),
            '105_ZN-SP' : local105['ZN-SP'].history.resample('1min'),
            '106_ZN-T' : local106['ZN-T'].history.resample('1min'),
            '106_ZN-SP' : local106['ZN-SP'].history.resample('1min'),
            '109_ZN-T' : local109['ZN-T'].history.resample('1min'),
            '109_ZN-SP' : local109['ZN-SP'].history.resample('1min'),
            '110_ZN-T' : local110['ZN-T'].history.resample('1min'),
            '110_ZN-SP' : local110['ZN-SP'].history.resample('1min'),    
           }
    # Remove any NaN values
    temp_pieces = pd.DataFrame(tempPieces).fillna(method = 'ffill').fillna(method = 'bfill')
    
    # Create a new column in the DataFrame which is the error between setpoint and temperature
    temp_pieces['Erreur_102'] = temp_pieces['102_ZN-T'] - temp_pieces['102_ZN-SP']
    temp_pieces['Erreur_104'] = temp_pieces['104_ZN-T'] - temp_pieces['104_ZN-SP']
    temp_pieces['Erreur_105'] = temp_pieces['105_ZN-T'] - temp_pieces['105_ZN-SP']
    temp_pieces['Erreur_106'] = temp_pieces['106_ZN-T'] - temp_pieces['106_ZN-SP']
    temp_pieces['Erreur_109'] = temp_pieces['109_ZN-T'] - temp_pieces['109_ZN-SP']
    temp_pieces['Erreur_110'] = temp_pieces['110_ZN-T'] - temp_pieces['110_ZN-SP']

    # Create a new dataframe from results and show some statistics    
    temp_erreurs = temp_pieces[['Erreur_102', 'Erreur_104', 'Erreur_105', 'Erreur_106', 'Erreur_109', 'Erreur_110']]
    temp_erreurs.describe()

TrendLog
========
BACnet TrendLog is an object that a controller may implement. Once configured, it'll keep in memory
a certain number of records for one particular point. Often though, as the controller memory may be
limited, we'll have access to a limited number of records and the interval between each record may
have been configured long enough to optimize the time frame coverage of the records. For example,
taking records every 10 minutes instead of every 2 minutes will give 5 times longer time interval.
Using a total of 2000 number of records, it will represent almost 14 days (10 min) vs less than 3 days
(2 min).

BAC0 supports the reading of TrendLog objects and will convert the records to pandas Series if possible.
This will allow to use **pandas** syntax over histories and make analysis easier for the user.

TrendLog objects have also been made compatible with the format required to be added as Bokeh Chart
in the web interface.::

   # Manually create a TrendLog
   import BAC0
   bacnet = BAC0.connect()
   device = BAC0.device('2:5',5,bacnet)

   # Given a TrendLog object at address 1 for device
   trend = BAC0.TrendLog(1,device)

   # Retrieve pandas serie
   trend.history

   # Adding this object to live trends
   trend.chart()
