Saving your data
================
When doing some tests, it can be useful to go back in time and see what
happened before. BAC0 allow you to save your progress (historical data) to a file
so you'll be able to re-open your device later.

Use ::

    controller.save()

and voila ! 2 new files will be created. One sqlite with all the histories, and
one bin file with all the details and properties of the device so it can be 
rebuilt when needed.

By default, the 'object name' of the device will be used as the filename. But you can specify a name ::

    controller.save(db='new_name')

Offline mode
------------
As already explained, a device in BAC0, if not connected (cannot be reached) will be
created as an offline device. If a database exist for this device, it will be
created and every points and histories will be available just like if you were
connected to the network.

You can also force a connection to the database if needed. Given a connected device use ::

    controller.connect(db='db_name')

Please note that it's actually an experimental feature.

Saving Data to Excel
--------------------
Using the module called xlwings, it's possible to export all the data of the controller
to an Excel Workbook.

Example ::

    controller.to_excel()