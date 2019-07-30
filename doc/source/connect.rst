How to start BAC0
===================================================
Define a bacnet network
----------------------------------------

Once imported, BAC0 will rely on a 'network' variable that will connect to the BACnet network you want to reach. This variable will be tied to a network interface (that can be a network card or a VPN connection) and all the traffice will pass on this variable.

More than one network variable can be created but only one connection by interface is supported.

Typically, we'll call this variable 'bacnet' to illustrate that it represents the network. But you can call it like you want.

This variable will also be passed to some functions when you will define a device for example. As the device needs to know on which network it can be found.

When creating the connection to the network, BAC0 needs to know the ip network of the interface on which it will work. It also needs to know the subnet mask (as BACnet operations often use broadcast messages).If you don't provide one, BAC0 will try to detect the interface for you.

..Note

    If you use ios, you will need to provide a ip manually. The script is unable to detect the subnet mask yet.

By default, if Bokeh, Pandas and Flask are installed, using the connect script will launch the complete version. But you can also use the lite version if you want something simple.
    
Example::

    import BAC0
    bacnet = BAC0.connect()
    # or specify the IP you want to use / bacnet = BAC0.connect(ip='192.168.1.10/24')
    # by default, it will attempt an internet connection and use the network adapter
    # connected to the internet.
    # Specifying the network mask will allow the usage of a local broadcast address
    # like 192.168.1.255 instead of the global broadcast address 255.255.255.255
    # which could be blocked in some cases.
    # You can also use :
    # bacnet = BAC0.lite() to force the script to load only minimum features.
    # Please note that if Bokeh, Pandas or Flask are not installed, using connect() will in fact call the lite version.


    

Lite vs Complete
*****************

Lite
.............

Use Lite if you only want to interact with some devices without using the web 
interface or the live trending features. 
On small devices like Raspberry Pi on which Numpy and Pandas are not installed, 
it will run without problem.

To do so, use the syntax::

    bacnet = BAC0.lite(ip='xxx.xxx.xxx.xxx/mask')

On a device without all the module sufficient to run the "complete" mode, using
this syntax will also run BAC0 in "Lite" mode::

    bacnet = BAC0.connect()
    
Complete
............

Complete will launch a web server with bokeh trending features. You will be able to 
access the server from another computer if you want.

To do so, use the syntax::

    bacnet = BAC0.connect(ip='xxx.xxx.xxx.xxx/mask')

And log to the web server pointing your browser to http://localhost:8111

.. note::
   To run BAC0 in "complete" mode, you need to install supplemental packages :
       * flask
       * flask-bootstrap
       * bokeh
       * pandas (numpy)
   To install bokeh, using "conda install bokeh" works really well. User will also needs to "pip install" everything else.

.. note::
   To run BAC0 in "complete" mode using a RaspberryPi_, I strongly recommend using the package
   berryconda_. This will install Pandas, numpy, already compiled for the Pi and give you access
   to the "conda" tool. You'll then be able to "conda install bokeh" and everythin will be working fine. If you try
   to "pip install pandas" you will face issues as the RPi will have to compile the source and it is
   a hard taks for a so small device. berryconda_ gives access to a great amount of packages already
   compiled for the Raspberry Pi.


Use BAC0 on a different subnect (Foreign Device)
*************************************************
In some situations (like using BAC0 with a VPN using TUN) your BAC0 instance
will run on a different subnet than the BACnet/IP network.

BAC0 support being used as a foreign device to cover those cases.

You must register to a BBMD (BACnet Broadcast Management Device) that will organize
broadcast messages so they can be sent through diferent subnet and be available for BAC0.

To do so, use the syntax::

    my_ip = '10.8.0.2/24'
    bbmdIP = '192.168.1.2'
    bbmdTTL = 900
    bacnet = BAC0.connect(ip='xxx.xxx.xxx.xxx/mask', bbdmAddress=bbmdIP, bbmdTTL=bbmdTTL)
    
Quick Discover
****************
Once your bacnet network is connected, you can use ::

    bacnet.whois()
    
and get a simple list of network:mac/device_instances on your network. 
Perfect for quick checkup.

Or you can get a more detailed view using ::

    bacnet.devices

..note::
    WARNING. `bacnet.devices` may in some circumstances, be a bad choice when you want to discover
    devices on a network. A lot of read requests are made to look for manufacturer, object name, etc
    and if a lot of devices are on the network, it is recommended to use whois() and start from there.

Time Sync
****************
You can use BAC0 to send time synchronisation requests to the network ::

    bacnet.time_sync()
    # or
    bacnet.time_sync('2:5') # <- Providing an address
    
BAC0 will not accept requests from other devices.

.. _berryconda : https://github.com/jjhelmus/berryconda  
.. _RaspberryPi : http://www.raspberrypi.org
