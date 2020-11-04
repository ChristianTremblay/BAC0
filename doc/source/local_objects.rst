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
But there are more. Depending on your needs, there will be an object that fit what you try to define
in your application.
The complet definition of all BACnet objects fall outside the scope of this document. Please refer to
the BACnet standard if you want to know more about them. For the sake of understanding, I'll cover
a few of them.

The definition of the BACnet obejcts is provided by `bacpypes.object`. You will need to import the 
different classes of objects you need when you will create the objects.

An object, like you probably know now, owes properties. Those properties can be read-only, writable,
mandatory or optional. This is defined in the standard. Typically, the actual value of an object is 
given by a property name `presentValue`. Another property called `relinquishDefault` would hold the 
value the object should give as a presentValue when all other priorityArray are null. PriorityArray 
is also a property of an object. When you create an object, you must know which properties you must
add to the object and how you will interact with thoses properties and how they will interact with 
one another.

This makes a lot to know when you first want to create one object.

A place to start
------------------

The enormous complexity of BACnet objects led me to think of a way to generate objects with a good
basis. Just enough properties depending on the commandability of the object (do you need other devices
to write to those objects ?). This decision hAVe an impact on the chosen properties of a BACnet object.

For any commandable object, it would be reasonable to provide a priorityArray and a relinquishDefault.
Those propoerties make no sense for a non-commandable object.

For any analog object, an engineering unit should be provided.

Those basic properties, depending on the type of objects, the BAC0's user should not hAVe to think about
them. They should just be part of the object.

Working in the factory
------------------------

BAC0 will allow the creation of BACnet objects with a special class named ObjectFactory. This class will take
as argument the objectType, instance, name, description, properties, etc and create the object. This object 
will then be added to a class variable (a dict) that will be used later to populate the application will all 
the created objects.

The factory will take as an argument `is_commandable` (boolean) and will modify the base type of object to 
make it commandable if required. This part is pretty complex as a subclass with a Commandable mixin must be
created fot each objectType. ObjectFactory uses a special decorator that will recreate a new subclass with
eveything that is needed to make the point commandable.

Another decorator will also allow the addition of custom properties (that would not be provided by default)
if it's required. 

Another decorator will allow the addition of "features" to the objects. Thos will need to be defined but we 
can think about event generation, alarms, MinOfOff behAViour, etc.

The user will not hAVe to think about the implementation of the decorators as everything is handled by the
ObjectFactory. But that said, nothing prevent you to create your own implementation of a factory using those
decorators.

An example
-----------

A good way to understand how things work is by giving an example. This code is part of the tests folder and
will give you a good idea of the way objects can be defined inside a BAC0's instance ::

    def build():
        bacnet = BAC0.lite(deviceId=3056235)

        new_obj = ObjectFactory(
            AnalogValueObject,
            0,
            "AV0",
            properties={"units": "degreesCelsius"},
            presentValue=1,
            description="Analog Value 0",
        )
        ObjectFactory(
            AnalogValueObject,
            1,
            "AV1",
            properties={"units": "degreesCelsius"},
            presentValue=12,
            description="Analog Value 1",
            is_commandable=True,
        )
        ObjectFactory(
            CharacterStringValueObject,
            0,
            "cs0",
            presentValue="Default value",
            description="String Value 0",
        )
        ObjectFactory(
            CharacterStringValueObject,
            1,
            "cs1",
            presentValue="Default value",
            description="Writable String Value 1",
            is_commandable=True,
        )

        new_obj.add_objects_to_application(bacnet.this_application)
        return bacnet

Models
==============
So it's possible to create objects but even using the object factory, things
are quite complex and you need to cover a lot of edge cases. What if you
want to create a lot of similar objects. What if you need to be sure each one
of them will hAVe the basic properties you need.

To go one step further, BAC0 offers models that can be used to simplify (at
least to try to simplify) the creation of local objects.

Models are an opiniated version of BACnet objects that can be used to create
the objects you need in your device. There are still some features that are 
not implemented but a lot of features hAVe been covered by those models.

Models use the ObjectFactory but with a supplemental layer of abstraction to
provide basic options to the objects.

For example, "analog" objects hAVe common properties. But the objectType will
be different if you want an analogInput or an analogValue. By default, AnalogOutput
will be commandable, but not the analogInput (not in BAC0 at least as it doesn't 
support behAViour that allows to write to the presentValue when the out_of_service 
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

Again, the best way to understand how things work, is by looking at code sample :
 
    # code here

State Text
===========
One important feature for multiState values is the state text property. This
define a text to shown in lieu of an integer. This adds a lot of clarity to
those objects. A device can tell a valve is "Open/Close", a fan is "Off/On", a
schedule is "Occupied/Unoccupied/Stanby/NotSet". It brings a lot of value.

To define state text, you must use the special function with a list of states
then you pass this variable to the properties dict : 

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