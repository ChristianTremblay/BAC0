Logging and debugging
=======================
All interactions with the user in the console is made using logging and an handler. Depending on 
the user desire, the level can be adjusted to limit or extend the verbosity of the app.

It is not recommended to set the stdout to logging.DEBUG level as it may fill the shell with messages
and make it very hard to enter commands. Typically, 'debug' is sent to the file (see below).

By default, stderr is set to logging.CRITICAL and is not used; stdout is set to logging.INFO; file is set to
logging.WARNING. The goal behind to not fill the file if it is not explicitly wanted.

Level
--------

You can change the logging level using ::

    import BAC0
    BAC0.log_level(level)
    # level being 'debug, info, warning, error'
    # or
    BAC0.log_leve(log_file=logging.DEBUG, stdout=logging.INFO, stderr=logging.CRITICAL)
    
File
--------
A log file will be created under your user folder (~) / .BAC0
It will contain warnings by default until you change the level.

Extract from the log file (with INFO level entries) ::

    2018-04-08 21:42:45,387 - INFO    | Starting app...
    2018-04-08 21:42:45,390 - INFO    | BAC0 started
    2018-04-08 21:47:21,766 - INFO    | Changing device state to <class 'BAC0.core.devices.Device.DeviceDisconnected'>
    2018-04-08 21:47:21,767 - INFO    | 
    2018-04-08 21:47:21,767 - INFO    | ###################################
    2018-04-08 21:47:21,767 - INFO    | # Read property
    2018-04-08 21:47:21,768 - INFO    | ###################################
    2018-04-08 21:47:22,408 - INFO    | value                datatype            
    2018-04-08 21:47:22,409 - INFO    | 'FX14 0005'          <class 'bacpypes.primitivedata.CharacterString'>
    2018-04-08 21:47:22,409 - INFO    | 
    2018-04-08 21:47:22,409 - INFO    | ###################################
    2018-04-08 21:47:22,409 - INFO    | # Read property
    2018-04-08 21:47:22,409 - INFO    | ###################################
    2018-04-08 21:47:23,538 - INFO    | value                datatype            
    2018-04-08 21:47:23,538 - INFO    | 'segmentedTransmit'  <class 'bacpypes.basetypes.Segmentation'>
    2018-04-08 21:47:23,538 - INFO    | Changing device state to <class 'BAC0.core.devices.Device.RPMDeviceConnected'>
    2018-04-08 21:47:29,510 - INFO    | ###################################
    2018-04-08 21:47:29,510 - INFO    | # Read Multiple
    2018-04-08 21:47:29,511 - INFO    | ###################################
    2018-04-08 21:47:30,744 - INFO    | 
    2018-04-08 21:47:30,744 - INFO    | ==================================================================================================================
    2018-04-08 21:47:30,744 - INFO    | 'analogValue' : 15
    2018-04-08 21:47:30,744 - INFO    | ==================================================================================================================
    2018-04-08 21:47:30,745 - INFO    | propertyIdentifier   propertyArrayIndex   value                          datatype            
    2018-04-08 21:47:30,745 - INFO    | ------------------------------------------------------------------------------------------------------------------
    2018-04-08 21:47:30,745 - INFO    | 'objectName'         None                 'nciPIDTPRdCTI'                <class 'bacpypes.primitivedata.CharacterString'>
    2018-04-08 21:47:30,745 - INFO    | 'presentValue'       None                 800.0                          <class 'bacpypes.primitivedata.Real'>
    2018-04-08 21:47:30,745 - INFO    | 'units'              None                 'seconds'                      <class 'bacpypes.basetypes.EngineeringUnits'>
    2018-04-08 21:47:30,746 - INFO    | 'description'        None                 'nciPIDTPRdCTI'                <class 'bacpypes.primitivedata.CharacterString'>
    2018-04-10 23:18:26,184 - DEBUG   | BAC0.core.app.ScriptApplication | ForeignDeviceApplication | ('do_IAmRequest %r', <bacpypes.apdu.IAmRequest(0) instance at 0x9064c88>)
