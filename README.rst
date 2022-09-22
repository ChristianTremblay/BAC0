BAC0 |build-status| |coverage| |docs|
=====================================

.. image:: https://badges.gitter.im/ChristianTremblay/BAC0.svg
   :alt: Join the chat at https://gitter.im/ChristianTremblay/BAC0
   :target: https://gitter.im/ChristianTremblay/BAC0?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

BAC0 is a Python 3 (3.6 and over) scripting application that uses BACpypes_ to process BACnet™ messages on a IP network. 
This library brings out simple commands to browse a BACnet network, read properties from BACnet devices or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled to BACnet, it becomes a great 
tool to test devices an interact with controllers.

BAC0 takes its name from the default IP port used by BACnet/IP communication which is port 47808. In hexadecimal, it's written 0xBAC0.

Test driven development (TDD) for DDC controls
==============================================
BAC0 is made for building automation system (BAS) programmers. Controllers used in this field are commonly called DDC Controllers (Direct Digital Control).

Typical controllers can be programmed in different ways, depending on the manufacturer selling them (block programming, basic "kinda" scripts, C code, etc...). 
BAC0, is a unified way, using Python language and BACnet/IP communication, to interact with those controllers once their sequence is built.

BAC0 allows users to simply test an application even if sensors are not connected to the controller. Using the out_of_service
property, it's easy to write a value to the input so the controller will think an input is conencted. 

It's also possible to do "manual commands" on output (often called overrides). In fact, every variable is exposed and seen by BAC0 and 
it's possible to interact with them using a simple scripting language or a complete unit test suite (like Pytest).

Without a program like BAC0, you can rely on your DDC programming tool... but it is often slow and
every test must be done manually. That means also that if you want to repeat the tests, the more complicated they are, the less chance you'll be able to do so.

Now you can write your test and run them as often as you want. We'll show you how it works.

Better start-up with data acquisition
=====================================
As you will discover, when you define a controller in BAC0, you will get access to historical data of
every variables in the controllers. Every points are trended every 10 seconds by default. Which means 
that you can do data analysis on everything while you're doing your startup. It allows to see performances and
trouble really fast.

This make BAC0 not only a good tool to test your sequence while your in the office.
But also a really good tool to assist your startup, test and balancing. Using Jupyter Notebook, you'll
even be able to create nice looking report right from your code.

InfluxDB native support
========================
Connect BAC0 histories directly to a InfluxDB_ v2.0 instance. It's then possible to use Grafana_ to explore your data.

Web features included
=====================
BAC0 includes a local web page that will help the user providing basic informations about the netwok seen by the script and also provide a simple interface to historical trends. Flask is used to render the web page and a Bokeh server is also provided to serve live trends to the user.


.. note::
   BACnet™ is a trademark of ASHRAE. 

.. |build-status| image:: https://github.com/ChristianTremblay/BAC0/workflows/Build%20&%20Test/badge.svg?branch=master
   :target: https://github.com/ChristianTremblay/BAC0/actions
   :alt: Build status
     
.. |docs| image:: https://readthedocs.org/projects/bac0/badge/?version=latest
   :target: http://bac0.readthedocs.org/
   :alt: Documentation
   
.. |coverage| image:: https://coveralls.io/repos/github/ChristianTremblay/BAC0/badge.svg?branch=master
   :target: https://coveralls.io/github/ChristianTremblay/BAC0?branch=master
   :alt: Coverage

.. _bacpypes : https://github.com/JoelBender/bacpypes

.. _bokeh : http://www.bokehplots.com

.. _InfluxDB : https://www.influxdata.com

.. _Grafana : https://grafana.com

