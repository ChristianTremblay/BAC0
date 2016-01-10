Histories in BAC0
====================
As said, every points get saved in a pandas Series every 10 seconds by default.
This means that you can look for historical data from the moment you connect to a device.
Access a historyTable::
    
    controller['nvoAI1'].history

Result example ::

    controller['nvoAI1'].history
    Out[8]:
    2015-09-20 21:41:37.093985    21.740000
    2015-09-20 21:42:23.672387    21.790001
    2015-09-20 21:42:34.358801    21.790001
    2015-09-20 21:42:45.841596    21.790001
    2015-09-20 21:42:56.308144    21.790001
    2015-09-20 21:43:06.897034    21.790001
    2015-09-20 21:43:17.593321    21.790001
    2015-09-20 21:43:28.087180    21.790001
    2015-09-20 21:43:38.597702    21.790001
    2015-09-20 21:43:48.815317    21.790001
    2015-09-20 21:44:00.353144    21.790001
    2015-09-20 21:44:10.871324    21.790001

Resampling data
---------------
As those are pandas DataFrame or Series, you can resample data::

    # This piece of code show what can of operation can be made using Pandas
    
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
    # Remove any NaN value
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