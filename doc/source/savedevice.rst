Saving your data
================
When doing tests, it can be useful to go back in time and see what
happened before. BAC0 allows you to save your progress (historical data) to a file
that you'll be able to re-open in your device later.

Use ::

    controller.save()

and voila! Two files are created. One (an SQLite file) contains all the histories, and
one binary file containing all the details and properties of the device so the details can be 
rebuilt when needed.

By default, the 'object name' of the device is used as the filename. But you can specify a name ::

    controller.save(db='new_name')

Offline mode
------------
As already explained, a device in BAC0, if not connected (or cannot be reached) will be
created as an offline device. If a database exists for this device, it will automatically 
loaded and all the points and histories will be available just as if if you were actually 
connected to the network.

You can also force a connection to use an existing database if needed. 
Provide connect function with the desired database's name.::

    controller.connect(db='db_name')

Please note: this feature is experimental.

Saving Data to Excel
--------------------
Thought the use of the Python module xlwings [https://www.xlwings.org/], it's possible to export all 
the data of a controller into an Excel Workbook.

Example ::

    controller.to_excel()
