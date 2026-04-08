Local Objects
================

Until now, we've looked into the capability of BAC0 to act as a "client" device. This is not a very
good term in the context of BACnet but at least it is easy to understand. But BAC0 can also act as 
a BACnet device. It can be found in a network and will present its properties to every other BACnet devices.

What if you want to create a BACnet device with objects with BAC0 ?

You will need to provide local objects that will be added to the application part of the BAC0 instance.
This part is called `this_application`.

What are BACnet objects
-------------------------

BACnet objects are very diverse. You probably know the main ones like AnalogValue or BinaryInput or
AnalogOutput, etc.
But there are more. Depending on your needs, there will be an object that fits what you try to define
in your application.
The complete definition of all BACnet objects falls outside the scope of this document. Please refer to
the BACnet standard if you want to know more about them. For the sake of understanding, I'll cover
a few of them.

The definition of BACnet objects is provided by bacpypes3. You will need to import the
different classes of objects you need when you create the objects.

An object, like you probably know now, owes properties. Those properties can be read-only, writable,
mandatory or optional. This is defined in the standard. Typically, the actual value of an object is 
given by a property name `presentValue`. Another property called `relinquishDefault` would hold the 
value the object should give as a presentValue when all other priorityArray are null. PriorityArray 
is also a property of an object. When you create an object, you must know which properties you must
add to the object and how you will interact with those properties and how they will interact with 
one another.

This is a lot to know when you first want to create an object.

A place to start
------------------

The enormous complexity of BACnet objects led me to think of a way to generate objects with a good
basis. Just enough properties depending on the commandability of the object (do you need other devices
to write to those objects?). This decision has an impact on the chosen properties of a BACnet object.

For any commandable object, it would be reasonable to provide a priorityArray and a relinquishDefault.
Those properties make no sense for a non-commandable object.

For any analog object, an engineering unit should be provided.

Those basic properties, depending on the type of objects, the BAC0 user should not have to think about
them. They should just be part of the object.

Quick start: create a device and add local objects (async)
----------------------------------------------------------
Use the factory models from ``BAC0.core.devices.local.factory`` to declare objects, then add them to your running BACnet device.

Minimal example::

    import asyncio
    import BAC0
    from BAC0.core.devices.local.factory import (
        analog_input, binary_output, multistate_value, character_string, make_state_text,
    )

    async def main():
        async with BAC0.lite(deviceId=1234, port=47808, localObjName="MyDevice") as dev:
            # Declare objects (units via property strings)
            new_objects = analog_input(name="TW1", description="Water temperature 1", properties={"units": "degreesCelsius"})
            new_objects = binary_output(name="Night", description="Day/Night flag", properties={"inactiveText": "day", "activeText": "night"})

            # State text for multistate
            lang_states = make_state_text(["en", "fr"])
            new_objects = multistate_value(name="Language", description="Language for requests", presentValue=1, properties={"stateText": lang_states})

            # Commandable string
            new_objects = character_string(name="Application_Status", description="Health/status", presentValue="Normal")

            # Push all declared objects into the running application
            # (call add_objects_to_application on any created model)
            # _ = character_string  # to emphasize any model can be used for the call
            new_objects.add_objects_to_application(dev)

            # Update values at runtime
            dev["TW1"].presentValue = 21.5
            dev["Night"].presentValue = False
            await asyncio.sleep(60)

    asyncio.run(main())

Notes:
- Creation calls accumulate models internally; ``add_objects_to_application(device)`` registers all accumulated models at once.
- Access local objects by name via ``dev["Object_Name"]``.
- For strings/datetimes you can assign plain Python types or bacpypes3 primitives (CharacterString, Date/Time/DateTime) as needed.

Real-world patterns (from examples)
-----------------------------------

Weather device (OpenWeatherMap)
................................
Create many objects using models, then add them and periodically update::

    async with BAC0.lite(deviceId=_device_id, port=_port, localObjName="BAC0_OpenWeatherMap") as dev:
        from BAC0.core.devices.local.factory import (
            analog_input, binary_output, multistate_value, datetime_value, character_string, make_state_text,
        )

        # Declare groups of objects (see src/main.py for full list)
        for prefix in ["Current", "Day0", "Day1"]:
            analog_input(name=f"{prefix}_Temp", description=f"{prefix} Temperature", properties={"units": "degreesCelsius"})
            # ... declare more objects per prefix ...

        # Global objects
        binary_output(name="Night", description="Based on sunrise/sunset", properties={"inactiveText": "day", "activeText": "night"})
        lang = make_state_text(["en", "fr"])
        multistate_value(name="Language", description="Language for requests", presentValue=1, properties={"stateText": lang})
        character_string(name="Application_Status", description="Health", presentValue="Normal")

        # Register all declared objects
        character_string.add_objects_to_application(dev)

        # Periodic updates (set presentValue, statusFlags, and datetime fields)
        # dev["Current_Temp"].presentValue = 23.1
        # dev["Night"].presentValue = True
        # See src/main.py for update helpers (update_float_object, update_datetime)

Environment-driven device (Davignon)
....................................
Read connection parameters from environment and expose sensor values::

    IP, PORT, MASK, DEVICEID, NAME = os.getenv("BAC0_IP"), os.getenv("BAC0_PORT"), os.getenv("BAC0_MASK"), os.getenv("BAC0_DEVICEID"), os.getenv("BAC0_OBJECTNAME")
    async def start_device():
        dev = BAC0.lite(ip=IP, mask=MASK, port=PORT, deviceId=DEVICEID, localObjName=NAME)
        while not dev._initialized:
            await asyncio.sleep(0.01)

        from BAC0.core.devices.local.factory import analog_input, binary_input, character_string

        analog_input(name="hg1_last_level", description="Level in meters", properties={"units": "meters"})
        analog_input(name="Battery_Voltage", description="Voltage of battery", properties={"units": "volts"})
        binary_input(name="NOAA_ALARM", description="Problem retrieving data")
        character_string(name="Application_Status", description="Health", presentValue="Normal")
        # Commandable config strings
        character_string(name="NOAA_USERNAME", description="Username", presentValue="", is_commandable=True)
        character_string(name="NOAA_PASSWORD", description="Password", presentValue="", is_commandable=True)

        character_string.add_objects_to_application(dev)
        return dev

Updating values and flags
-------------------------
- Numeric points: assign floats/ints to ``presentValue`` and optionally update ``statusFlags``.
- Strings: assign plain strings or ``CharacterString``. For datetimes, update the ``date`` and ``time`` fields of a ``DateTime`` presentValue.

Example helpers::

    def update_float(obj_name, value, flags):
        dev[obj_name].presentValue = float(value)
        dev[obj_name].statusFlags = flags  # e.g., [0,0,0,0] for normal

    def update_datetime(obj_name, epoch_ts, flags):
        from bacpypes3.primitivedata import Date, Time
        import pytz, datetime as dt
        ref = dt.datetime.fromtimestamp(epoch_ts).astimezone(pytz.UTC).astimezone()
        dev[obj_name].presentValue.date = Date(ref.date().isoformat())
        dev[obj_name].presentValue.time = Time(ref.time().isoformat())
        dev[obj_name].statusFlags = flags

TrendLog objects
-----------------
If you declare a local ``trendlog`` object, you can append samples and refresh properties::

    from BAC0.core.devices.local.factory import trendlog
    trendlog(name="hg1", description="Level log", properties={"trendLog_datatype": "realValue"})
    trendlog.add_objects_to_application(dev)

    # Add samples; update the log object
    dev["hg1"]._local.add_data(timestamp, value, flag, interval=900000, update_after=False)
    dev["hg1"]._local.update_properties()

Models
==============
So it's possible to create objects but even using the object factory, things
are quite complex and you need to cover a lot of edge cases. What if you
want to create a lot of similar objects. What if you need to be sure each one
of them will have the basic properties you need.

To go one step further, BAC0 offers models that can be used to simplify (at
least to try to simplify) the creation of local objects.

Models are an opiniated version of BACnet objects that can be used to create
the objects you need in your device. There are still some features that are 
not implemented but a lot of features have been covered by those models.

Models use the ObjectFactory but with a supplemental layer of abstraction to
provide basic options to the objects.

For example, "analog" objects have common properties. But the objectType will
be different if you want an analogInput or an analogValue. By default, AnalogOutput
will be commandable, but not the analogInput (not in BAC0 at least as it doesn't 
support behavior that allows writing to the presentValue when the out_of_service 
property is True). Instead of letting the user thinking about all those details, 
you can simply create an `analogInput` and BAC0 will take care of the details.

Actually, BAC0 implements those models : 

    analog_input,
    analog_output,
    analog_value,
    binary_input,
    binary_output,
    binary_value,
    multistate_input,
    multistate_output,
    multistate_value,
    date_value,
    datetime_value,
    temperature_input,
    temperature_value,
    humidity_input,
    humidity_value,
    character_string,

Again, the best way to understand how things work is by looking at code. See the "Real-world patterns" section above for end-to-end examples.

Advanced: ObjectFactory
------------------------
The underlying implementation uses an ``ObjectFactory`` that assembles required properties, commandability (priorityArray, relinquishDefault), and optional features. While you can use it directly, the model helpers (``analog_input``, ``binary_output``, etc.) are the recommended interface.

State Text
===========
One important feature for multiState values is the state text property. This
define a text to shown in lieu of an integer. This adds a lot of clarity to
those objects. A device can tell a valve is "Open/Close", a fan is "Off/On", a
schedule is "Occupied/Unoccupied/Stanby/NotSet". It brings a lot of value.

To define state text, you must use the special function with a list of states
then pass this variable to the properties dict ::

    states = make_state_text(["Normal", "Alarm", "Super Emergency"])
    _new_object = multistate_value(
        description="An Alarm Value",
        properties={"stateText": states},
        name="BIG-ALARM",
        is_commandable=True,
    )


Engineering units
===================
Valid Engineering untis to be used are :

    ampereSeconds
    ampereSquareHours
    ampereSquareMeters
    amperes
    amperesPerMeter
    amperesPerSquareMeter
    bars
    becquerels
    btus
    btusPerHour
    btusPerPound
    btusPerPoundDryAir
    candelas
    candelasPerSquareMeter
    centimeters
    centimetersOfMercury
    centimetersOfWater
    cubicFeet
    cubicFeetPerDay
    cubicFeetPerHour
    cubicFeetPerMinute
    cubicFeetPerSecond
    cubicMeters
    cubicMetersPerDay
    cubicMetersPerHour
    cubicMetersPerMinute
    cubicMetersPerSecond
    currency1
    currency10
    currency2
    currency3
    currency4
    currency5
    currency6
    currency7
    currency8
    currency9
    cyclesPerHour
    cyclesPerMinute
    days
    decibels
    decibelsA
    decibelsMillivolt
    decibelsVolt
    degreeDaysCelsius
    degreeDaysFahrenheit
    degreesAngular
    degreesCelsius
    degreesCelsiusPerHour
    degreesCelsiusPerMinute
    degreesFahrenheit
    degreesFahrenheitPerHour
    degreesFahrenheitPerMinute
    degreesKelvin
    degreesKelvinPerHour
    degreesKelvinPerMinute
    degreesPhase
    deltaDegreesFahrenheit
    deltaDegreesKelvin
    farads
    feet
    feetPerMinute
    feetPerSecond
    footCandles
    grams
    gramsOfWaterPerKilogramDryAir
    gramsPerCubicCentimeter
    gramsPerCubicMeter
    gramsPerGram
    gramsPerKilogram
    gramsPerLiter
    gramsPerMilliliter
    gramsPerMinute
    gramsPerSecond
    gramsPerSquareMeter
    gray
    hectopascals
    henrys
    hertz
    horsepower
    hours
    hundredthsSeconds
    imperialGallons
    imperialGallonsPerMinute
    inches
    inchesOfMercury
    inchesOfWater
    jouleSeconds
    joules
    joulesPerCubicMeter
    joulesPerDegreeKelvin
    joulesPerHours
    joulesPerKilogramDegreeKelvin
    joulesPerKilogramDryAir
    kiloBtus
    kiloBtusPerHour
    kilobecquerels
    kilograms
    kilogramsPerCubicMeter
    kilogramsPerHour
    kilogramsPerKilogram
    kilogramsPerMinute
    kilogramsPerSecond
    kilohertz
    kilohms
    kilojoules
    kilojoulesPerDegreeKelvin
    kilojoulesPerKilogram
    kilojoulesPerKilogramDryAir
    kilometers
    kilometersPerHour
    kilopascals
    kilovoltAmpereHours
    kilovoltAmpereHoursReactive
    kilovoltAmperes
    kilovoltAmperesReactive
    kilovolts
    kilowattHours
    kilowattHoursPerSquareFoot
    kilowattHoursPerSquareMeter
    kilowattHoursReactive
    kilowatts
    liters
    litersPerHour
    litersPerMinute
    litersPerSecond
    lumens
    luxes
    megaBtus
    megabecquerels
    megahertz
    megajoules
    megajoulesPerDegreeKelvin
    megajoulesPerKilogramDryAir
    megajoulesPerSquareFoot
    megajoulesPerSquareMeter
    megAVoltAmpereHours
    megAVoltAmpereHoursReactive
    megAVoltAmperes
    megAVoltAmperesReactive
    megAVolts
    megawattHours
    megawattHoursReactive
    megawatts
    megohms
    meters
    metersPerHour
    metersPerMinute
    metersPerSecond
    metersPerSecondPerSecond
    microSiemens
    microgramsPerCubicMeter
    microgramsPerLiter
    microgray
    micrometers
    microsieverts
    microsievertsPerHour
    milesPerHour
    milliamperes
    millibars
    milligrams
    milligramsPerCubicMeter
    milligramsPerGram
    milligramsPerKilogram
    milligramsPerLiter
    milligray
    milliliters
    millilitersPerSecond
    millimeters
    millimetersOfMercury
    millimetersOfWater
    millimetersPerMinute
    millimetersPerSecond
    milliohms
    milliseconds
    millisiemens
    millisieverts
    millivolts
    milliwatts
    minutes
    minutesPerDegreeKelvin
    months
    nanogramsPerCubicMeter
    nephelometricTurbidityUnit
    newton
    newtonMeters
    newtonSeconds
    newtonsPerMeter
    noUnits
    ohmMeterPerSquareMeter
    ohmMeters
    ohms
    pH
    partsPerBillion
    partsPerMillion
    pascalSeconds
    pascals
    perHour
    perMille
    perMinute
    perSecond
    percent
    percentObscurationPerFoot
    percentObscurationPerMeter
    percentPerSecond
    percentRelativeHumidity
    poundsForcePerSquareInch
    poundsMass
    poundsMassPerHour
    poundsMassPerMinute
    poundsMassPerSecond
    powerFactor
    psiPerDegreeFahrenheit
    radians
    radiansPerSecond
    revolutionsPerMinute
    seconds
    siemens
    siemensPerMeter
    sieverts
    squareCentimeters
    squareFeet
    squareInches
    squareMeters
    squareMetersPerNewton
    teslas
    therms
    tonHours
    tons
    tonsPerHour
    tonsRefrigeration
    usGallons
    usGallonsPerHour
    usGallonsPerMinute
    voltAmpereHours
    voltAmpereHoursReactive
    voltAmperes
    voltAmperesReactive
    volts
    voltsPerDegreeKelvin
    voltsPerMeter
    voltsSquareHours
    wattHours
    wattHoursPerCubicMeter
    wattHoursReactive
    watts
    wattsPerMeterPerDegreeKelvin
    wattsPerSquareFoot
    wattsPerSquareMeter
    wattsPerSquareMeterDegreeKelvin
    webers
    weeks
    years