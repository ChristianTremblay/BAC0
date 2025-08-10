How to start BAC0
===================================================
Intro
----------------------------------------

BAC0 is a library that allows you to interact with BACnet devices. It relies on bacpypes3 and uses asyncio to provide fast and efficient communication with BACnet devices.

To start using BAC0, you will need to import the library and create a BAC0 object. This object will be the main object that will allow you to interact with the BACnet network.

More than one BAC0 object can be created but only one connection by interface is supported.

Typically, we'll call this object 'bacnet' to illustrate that it represents the access point to the BACnet network. But you can call it whatever you want.

This object will be used to interact with the BACnet network. It will be used to discover devices, read and write properties, trend points, etc.

This object can also act as a BACnet device itself, serving BACnet objects to the network.

To create a BAC0 object, use start(). You can either:

- use it as an async context manager (recommended) which connects and cleans up automatically
- or assign it directly to a variable and manage cleanup yourself

.. note :: 
    Legacy BAC0 had two flavors: lite and complete. This is no longer the case. All web services have been deprecated; use external tools (e.g., Grafana or InfluxDB) for trending.

When creating the connection to the network, BAC0 needs to know the IP network of the interface it will use. It also needs the subnet mask (BACnet often uses broadcast messages). If you don't provide one, BAC0 will try to detect an interface for you.

.. note::
    Pythonista (iOS) is not supported.

How to run async code
----------------------------------------

To run async code interactively (so you can explore the library or your BACnet network), there are a few options. Running standalone scripts is slightly different and covered below.

- Use the asyncio REPL: run `python -m asyncio` and then await coroutines directly.
- Use a Jupyter Notebook: most modern IPython kernels support top-level await.

Define a bacnet application
----------------------------------------

Example (async context manager)::

    import asyncio
    import BAC0

    async def main():
        # auto-detect interface
        async with BAC0.start() as bacnet:
            # or specify IP/mask: async with BAC0.start(ip='192.168.1.10/24') as bacnet:
            # do work, e.g. discovery
            await bacnet._discover(global_broadcast=True)

    asyncio.run(main())

Example (direct assignment)::

    import asyncio
    import BAC0

    async def main():
        # create and start immediately
        bacnet = BAC0.start()  # aliases: BAC0.connect(), BAC0.lite()

        try:
            # you can use bacnet right away
            await bacnet._discover(global_broadcast=True)
        finally:
            # when not using a context manager, disconnect explicitly
            await bacnet._disconnect()  # or: await bacnet.disconnect()

    asyncio.run(main())

.. note::
    The context manager waits until the instance is fully initialized before entering. If you don't use a context manager, most operations work immediately, but a few convenience features may not be ready until the instance has announced itself on the network. If needed, prefer the context manager or wait briefly before the first network calls.

Dependencies and nice-to-have features
--------------------------------------------
BAC0 relies on bacpypes3 for BACnet/IP. BAC0 wraps and simplifies common tasks.

Optional packages that improve the experience:
- rich: prettier console output
- pandas: convenient handling of historical data
- python-dotenv: load environment variables from a .env file
- sqlite3/InfluxDB: optional storage for histories (external services required for InfluxDB)

Asynchronous programming
**************************
BAC0 is based on bacpypes3 which relies on asyncio. Calls that read from the network are async and must be awaited. Some operations (like bacnet.write()) are fire-and-forget helpers that schedule the write in the background; use await bacnet._write(...) to await completion.

Lite vs Complete vs connect vs start
************************************
This version of BAC0 presents a single way to create a BAC0 instance. Use `start()`, which returns an async context manager. For compatibility, `connect()` and `lite()` are aliases of `start()`.


Start
.............

When you start BAC0, you get a BAC0 object that can discover devices, read and write properties, trend points, etc. Using the correct subnet is important because BACnet relies on broadcasts. If omitted, BAC0 will try to auto-detect.

If you need to reach a network on a different subnet, you can register as a foreign device with a BBMD (BACnet Broadcast Management Device) or provide router info (see below).

Basic start::

    async with BAC0.start(ip='xxx.xxx.xxx.xxx/mask') as bacnet:
        ...


> Device ID 
> 
> You can set the device ID of your BAC0 instance with `deviceId`, e.g. `async with BAC0.start(ip='x.x.x.x/mask', deviceId=1234) as bacnet:`.
    

Use BAC0 on a different subnet (Foreign Device)
***************************************************
In some situations (like using BAC0 with a VPN using TUN) your BAC0 instance
will run on a different subnet than the BACnet/IP network.

BAC0 support being used as a foreign device to cover those cases.

You must register to a BBMD (BACnet Broadcast Management Device) that will organize
broadcast messages so they can traverse different subnets and reach BAC0.

To do so, use the syntax::

    my_ip = '10.8.0.2/24'
    bbmdIP = '192.168.1.2:47808'
    bbmdTTL = 900
    # note the parameter name is bbmdAddress
    async with BAC0.start(ip=my_ip, bbmdAddress=bbmdIP, bbmdTTL=bbmdTTL) as bacnet:
        ...

BBMDs vs Foreign Devices (when and how)
***************************************
BACnet/IP uses BBMDs (BACnet Broadcast Management Devices) to propagate broadcast traffic across routed IP networks. Clients that are not on the same subnet as the devices can:

- Register as a Foreign Device (FD) to a BBMD: your BAC0 instance will receive broadcast traffic via the BBMD and can participate in Who-Is/I-Am.
- Or operate a BBMD and populate a Broadcast Distribution Table (BDT) so multiple subnets share broadcasts.

Configure Foreign Device registration:

Example::

    async with BAC0.start(
        ip="10.8.0.2/24",                # your VPN/TUN interface
        bbmdAddress="192.168.1.2:47808", # BBMD on site
        bbmdTTL=900                        # lifetime seconds
    ) as bacnet:
        await bacnet._discover(global_broadcast=True)

Notes:
- FD registration makes your BAC0 reachable for broadcast-based discovery through the BBMD.
- TTL must be renewed periodically; BAC0 handles registering at start. If your session is long, consider re-registering before TTL expiry (BAC0 may renew depending on link-layer behavior).

Operate as or with a BBMD using a BDT
*************************************
If you need to interconnect multiple subnets, you can provide a Broadcast Distribution Table (BDT) when starting BAC0 so it participates in BBMD distribution.

Example (multiple peers)::

    bdt = [
        "192.168.211.201:47808",
        "192.168.210.253:47808",
    ]
    async with BAC0.start(bdtable=bdt) as bacnet:
        await bacnet._discover()

A BDT is provided to reach multiple subnets. Use FD registration when you’re a client off-subnet; use BDT when linking subnets for broadcast propagation.

Troubleshooting BBMD/FD:
- Verify the BBMD address and UDP port (default 47808) and that UDP is allowed between you and the BBMD.
- Confirm your BAC0 ip/mask matches your local interface, and that NAT/firewalls don’t drop UDP 47808.
- If discovery still misses devices, combine with `await bacnet.whois_router_to_network()` and `await bacnet.use_router(...)` to add unicast routes for remote networks.
    
Discovering devices on a network
*********************************
BACnet protocole relies on "whois" and "iam" messages to search and find devices. Typically, 
those are broadcast messages that are sent to the network so every device listening will be 
able to answer to whois requests by a iam request.

By default, BAC0 will use "local broadcast" whois messages. This means that in some situations,
you will not see by default the global network. Local broadcast will not traverse subnets and 
won't propagate to MSTP network behind BACnet/IP-BACnet/MSTP router that are on the same subnet
than BAC0.

This is done on purpose because using "global broadcast" by default can create a large amount
of traffic on big BACnet network when all devices will send their "iam" response at the same
time.

Instead, it is recommended to be careful and try to find devices on BACnet networks one at a time.
For that though, you have to "already know" what is on your network. Which is not always the case.
This is why BAC0 will still be able to issue global broadcast whois request if explicitly told to do so.

The recommended function to initiate a discovery is ::

    bacnet.discover(networks=['listofnetworks'], limits=(0,4194303), global_broadcast=False)
    # networks can be a list of integers, a simple integer, or 'known'
    # By default global_broadcast is False
    # The limits bound the device instance range for Who-Is


This function schedules an async discovery in the background. It also emits a 'What-Is-Network-Number' request to learn the local network number (not all devices support this).

To block until discovery completes, call the coroutine directly::

    await bacnet._discover(networks='known')

BAC0 stores learned network numbers in `bacnet.known_network_numbers`. You can then 
use this list to work with discover and find everything on the network without issuing global broadcasts.
To make a discover on known networks, use ::

    bacnet.discover(networks='known')

All found devices are listed in `bacnet.discoveredDevices`.

BAC0 also provides a helper to print a nice table of devices (name, vendor, address). It performs extra reads, so it may be slow on large networks.

Show the table::

    await bacnet.devices

Get the list instead of printing::

    lst = await bacnet._devices(_return_list=True)

.. note::
    `await bacnet.devices` issues many reads (objectName, vendorName, ...). On large networks, prefer starting with who-is discovery and inspecting `bacnet.discoveredDevices`.

BAC0 also support the 'Who-Is-Router-To-Network' request so you can ask the network and you will see the address
of the router for this particular BACnet network. The request 'Initialize-Router-Table' will be triggered on the 
reception of the 'I-Am-Router-To-Network' answer.

Once BAC0 knows which router leads to a network, the requests for that network will be 
sent directly to the router as unicast messages. For example ::

    # if router for network 3 is 192.168.1.2
    bacnet.whois('3:*') 
    # will send the request to 192.168.1.2, even if by default, a local broadcast would sent the request
    # to 192.168.1.255 (typically with a subnet 255.255.255.0 or /24)

How BACnet/IP broadcast works (and why subnets matter)
******************************************************
BACnet/IP Who-Is and other discovery messages are broadcast at the IP layer on UDP/47808.

- Local broadcast: goes to your interface’s broadcast address (derived from ip/mask) and is not routed by typical IP routers. Only devices on the same IP subnet will see it.
- Global broadcast: an IP-wide broadcast that many networks block and that still won’t traverse most routed networks without BBMDs.
- Routers (BACnet/IP to BACnet/MSTP, etc.) do not automatically forward IP broadcasts into other BACnet networks.

Implications for discovery:
- Your BAC0 ip/mask must match the target subnet for local broadcast discovery to work. Example: if devices are on 192.168.10.0/24, running BAC0 on 192.168.11.10/24 won’t see them with local broadcasts.
- If you’re on a VPN with a TUN interface (different subnet), broadcasts will not reach the remote site. Use a BBMD or register as a Foreign Device (next section).
- Prefer scoped discovery: use known network numbers and unicast to routers, or ask for router info, to avoid global storms on large sites.

Practical tips:
- Always provide the correct ip/mask when starting BAC0 (e.g., '192.168.10.15/24').
- If you don’t know the subnet, start with local broadcast and then learn network numbers and routers, or use the BBMD/Foreign Device approach.

Routing Table
***************
BACnet communication trough different networks is made possible by the different 
routers creating "routes" between the subnet where BAC0 live and the other networks.
When a network discovery is made by BAC0, informations about the detected routes will
be saved (actually by the bacpypes stack itself) and for reference, BAC0 offers a way 
to extract the information ::

    await bacnet.routing_table

This returns a dict with available routing information, e.g.::

    await bacnet.routing_table
    {'192.168.211.3': Source Network: None | Address: 192.168.211.3 | Destination Networks: {303: 0} | Path: (1, 303)}

Manually declare a router (use_router)
**************************************
If auto-discovery doesn’t find a path to a remote BACnet network, you can declare a router manually.

`use_router` tells BAC0 which IP/Port routes to which destination network numbers (dnets). After registration, BAC0 unicast-sends requests to that router for the given networks and updates its routing cache accordingly.

Signature: `await bacnet.use_router((address, dnets[, snet]))`

- address: router IP and UDP port as a string (e.g., '192.168.1.2:47808') or an Address
- dnets: a single destination network number (int) or a list of ints
- snet (optional): source network number if you need to pin one

Examples::

    # One destination network
    await bacnet.use_router(("192.168.1.2:47808", 3))

    # Multiple destination networks
    await bacnet.use_router(("192.168.1.2:47808", [3, 5, 7]))

    # Provide a specific source network number
    await bacnet.use_router(("192.168.1.2:47808", 3, 1))

Notes:
- BAC0 first sends a who-is to the router address; if it doesn’t answer, the mapping is not applied.
- When applied, routes are added to the internal router info cache and to `known_network_numbers`.
- This is session-scoped; restart or disconnect to clear. There is no explicit “remove router” helper.
- You can combine this with `await bacnet.whois_router_to_network(network=NN)` and `await bacnet.init_routing_table(address)` to discover and validate router entries.

Multiple BAC0 instances on one machine
************************************************************
BAC0 binds one BACnet/IP socket per instance. You cannot start two instances on the same IP and same UDP port (47808) at once. Options:

1) Add multiple IPs to the same network interface
- Assign distinct IP addresses on your NIC (same subnet or different, as needed).
- Start one BAC0 per IP, all using default port 47808. Broadcast discovery works across devices on that subnet.

2) Use a different BACnet/IP port (e.g., 47809) on the same IP
- Start the second instance on port 47809. This avoids the bind conflict and both instances can run.
- Important: in BACnet/IP, a different UDP port is considered a different BACnet network. Broadcast-based discovery will not cross ports. You must reference the remote device using its explicit ip:port.

Specifying a custom port
You can specify a port in two ways:
- In the IP string: '192.168.1.10/24:47809'
- Or as a named argument: `BAC0.start(ip='192.168.1.10/24', port=47809)`

Example: two instances talking together on the same host
This mirrors the sandbox example with one instance acting as a small local device and another as the client. Because ports differ, use an explicit address with port when creating the device handle::

    ADDRESS = '10.138.103.17/16'

    async with BAC0.start(ip=ADDRESS, deviceId=123) as bacnet:
        async with BAC0.start(ip=ADDRESS, port=47809, deviceId=456) as fake_device:
            # ... add local objects to fake_device ...

            # Discovery across ports won't work (different BACnet network)
            # await bacnet._discover()  # won't find fake_device

            # Explicitly point to ip:port to communicate
            dev = await BAC0.device(f"{ADDRESS}:47809", 456, bacnet)
            value = await dev['AI1'].value

Guidance:
- Prefer multiple IPs on the interface when you want discovery and normal BACnet/IP behavior (same port 47808).
- Use alternate ports when you only need explicit, point-to-point communication and accept that broadcast discovery won’t cross ports.

Ping devices (monitoring feature)
**********************************
BAC0 includes a way to ping constantly the devices that have been registered. 
This way, when devices go offline, BAC0 will disconnect them until they come back
online. This feature can be disabled if required when declaring the network ::

    bacnet = BAC0.start(ping=False)
    
By default, the feature is activated.

When reconnecting after a disconnect, a complete rebuild of the device is done.
This way, if the device have changed (a download have been done and point list changed)
new points will be available. Old one will not.

.. note::
    When BAC0 disconnects a device, it will try to save the device to SQL (if configured).

See also: creating devices and interacting with points in :ref:`devices-and-points`.

