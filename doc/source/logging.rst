Logging and debugging
=======================
Level
--------

You can change the logging level using ::

    BAC0.log_level(level)
    # level being 'debug, info, warning, error'
    
File
--------
A log file will be created under your user folder / .BAC0
It will contain warning by default until you change the level.

Extract from the log file ::

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
