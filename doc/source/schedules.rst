Schedules in BAC0
====================

Schedules object in BAC0 are supported by using two specific functions ::

    bacnet.read_weeklySchedule(address, instance)
    # and
    bacnet.write_weeklySchedule(address, instance, schedule)

This is required by the complexity of the object itself which is composed of
multiple elements.

First, as you notice, actually, BAC0 support the "weeklySchedule" which is a property
of the bacnet object ScheduleObject. The exceptionSchedule is not yet supported. Neither 
the calendar.

The weeklySchedule property is generally used locally inside the controller and is
often synchronized from a supervisory controller if required.

weeklySchedule are made of 7 DailySchedules. Thoses schedules are made from lists
of events written as TimeValues (a time of day, a value to be in).

This level of nesting would be very hard to write as a string to be passed to `bacnet.write`
so this is why we provide 2 specific functions. 

Python representation
------------------------
One challenge in BAC0 is finding a good way to represent a BACnet object in the terminal. With 
schedules, the challenge was the quantity of elements important to understand what is going on 
with the schedule, what are the events, what is the actual value, the priorityForWriting, etc...
Important informations when you interact with a controller. But also, we needed a simple format
allowing easy editing to be written to the controlle.

The dict was simple enough to hold all the information and the chosen format is ::

    schedule_example_multistate = {
        "states": {"Occupied": 1, "UnOccupied": 2, "Standby": 3, "Not Set": 4},
        "week": {
            "monday": [("1:00", "Occupied"), ("17:00", "UnOccupied")],
            "tuesday": [("2:00", "Occupied"), ("17:00", "UnOccupied")],
            "wednesday": [("3:00", "Occupied"), ("17:00", "UnOccupied")],
            "thursday": [("4:00", "Occupied"), ("17:00", "UnOccupied")],
            "friday": [("5:00", "Occupied"), ("17:00", "UnOccupied")],
            "saturday": [("6:00", "Occupied"), ("17:00", "UnOccupied")],
            "sunday": [("7:00", "Occupied"), ("17:00", "UnOccupied")],
        },
    }
    schedule_example_binary = {
        "states": {"inactive": 0, "active": 1},
        "week": {
            "monday": [("1:00", "active"), ("16:00", "inactive")],
            "tuesday": [("2:00", "active"), ("16:00", "inactive")],
            "wednesday": [("3:00", "active"), ("16:00", "inactive")],
            "thursday": [("4:00", "active"), ("16:00", "inactive")],
            "friday": [("5:00", "active"), ("16:00", "inactive")],
            "saturday": [("6:00", "active"), ("16:00", "inactive")],
            "sunday": [("7:00", "active"), ("16:00", "inactive")],
        },
    }
    schedule_example_analog = {
        "states": "analog",
        "week": {
            "monday": [("1:00", 22), ("18:00", 19)],
            "tuesday": [("2:00", 22), ("18:00", 19)],
            "wednesday": [("3:00", 22), ("18:00", 19)],
            "thursday": [("4:00", 22), ("18:00", 19)],
            "friday": [("5:00", 22), ("18:00", 19)],
            "saturday": [("6:00", 22), ("18:00", 19)],
            "sunday": [("7:00", 22), ("18:00", 19)],
        },
    }

.. note::
    Those examples are all available by calling `bacnet.schedule_example_analog` or `bacnet.schedule_example_binary` or
    `bacnet.schedule_example_multistate`. This make a quick way to get access to a template.

Missing informations
----------------------
Those templates, are simple models to be edited and should be used to write to schedules. But when you read weeklySchedule from
a controller, you will notice that more information will be retrieved. 

No worries, you can take what's coming from the controller, edit the week events and send it back. When writing to a weeklySchedule
BAC0 will only use the **states** and **week** element of the dict.

Example of a weeklySchedule from a controller ::

    {'object_references': [('multiStateValue', 59)],
    'references_names': ['OCC-SCHEDULE'],
    'states': {'Occupied': 1, 'UnOccupied': 2, 'Standby': 3, 'Not Set': 4},
    'reliability': 'noFaultDetected',
    'priority': 15,
    'presentValue': 'UnOccupied (2)',
    'week': {'monday': [('01:00', 'Occupied'), ('17:00', 'UnOccupied')],
            'tuesday': [('02:00', 'Occupied'), ('17:00', 'UnOccupied')],
            'wednesday': [('03:00', 'Occupied'), ('17:00', 'UnOccupied')],
            'thursday': [('04:00', 'Occupied'), ('17:00', 'UnOccupied')],
            'friday': [('05:00', 'Occupied'), ('17:00', 'UnOccupied')],
            'saturday': [('06:00', 'Occupied'), ('17:00', 'UnOccupied')],
            'sunday': [('07:00', 'Occupied'), ('17:00', 'UnOccupied')]}}

As you can see, more information is available and can be used.

How things work
------------------
The ScheduleObject itself doesn't give all the information about the details and
to build this representation, multiple network reading will occur. 

object_references
********************
The ScheduleObject will provide a list of Object property references. Those are the points inside the
controller connected to the schedule.

references_names
*****************
For clarity, the names of the point, in the same order than the object_references so it's easy to
tell which point is controlled by this scedule 

States
********
BAC0 will read the first object_references and retrieve the states from this point. This way, we'll 
know the meaning of the integer values inside the schedule itself. "Occupied" is clearer 
than "1".

When using an **analog** schedule. States are useless as the value will consists on a floating value.
If using an analog schedule, `states = 'analog'`.

When using **binary** schedules, BAC0 will consider fixed states (standard binary terms) `['inactive': 0, 'active' : 1]`

reliability
************
This is the reliability property of the schedule object exposed here for information

priority
************
This is the **priorityForWriting** property of the schedule. This tells at what priority the schedule
will write to a point linked to the schedule (see object_references). If you need to override the
internal schedule, you will need to use a higher priority for your logic to work.

PresentValue
*************
Lnowing the states, BAC0 will give both the value and the name of the state for the presentValue.

week
*************
This is the core of the weeklySchedule. This is a dict containing all days of the week (from monday to sunday, 
the order is VERY important.
Each day consists of a list of event presented as tuple containing a string representation of the time and the value ::

    {'monday': [('00:00', 'UnOccupied'),('07:00', 'Occupied'), ('17:00', 'UnOccupied')],
    'tuesday': [('07:00', 'Occupied'), ('17:00', 'UnOccupied')],
    'wednesday': [('07:00', 'Occupied'), ('17:00', 'UnOccupied')],
    'thursday': [('07:00', 'Occupied'), ('17:00', 'UnOccupied')],
    'friday': [('07:00', 'Occupied'), ('17:00', 'UnOccupied')],
    'saturday': [],
    'sunday': []}}

Writing to the weeklySchedule
------------------------------
When your schedule dict is created, simply send it to the controller schedule by providing the address
and the instance number of the schedule on which you want to write ::

    bacnet.write_weeklySchedule("2:5", 10001, schedule)