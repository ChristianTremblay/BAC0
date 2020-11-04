Time Sync
==========
You can use BAC0 to send time synchronisation requests to the network ::

    bacnet.time_sync()
    # or
    bacnet.time_sync('2:5') # <- Providing an address
    
BAC0 will not accept requests from other devices.