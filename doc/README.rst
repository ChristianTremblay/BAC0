BAC0
====

.. image:: https://github.com/ChristianTremblay/BAC0/workflows/Build%20&%20Test/badge.svg?branch=master
    :alt: Build status
.. image:: https://coveralls.io/repos/github/ChristianTremblay/BAC0/badge.svg?branch=master
    :alt: Coverage
.. image:: https://readthedocs.org/projects/bac0/badge/?version=latest
    :alt: Documentation

.. image:: https://badges.gitter.im/ChristianTremblay/BAC0.svg
    :target: https://gitter.im/ChristianTremblay/BAC0?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
    :alt: Join the chat at https://gitter.im/ChristianTremblay/BAC0

BAC0 is an asynchronous Python 3 (3.10 and over) scripting application that uses `BACpypes3 <https://github.com/JoelBender/BACpypes3>`_ to process BACnet™ messages on an IP network. This library brings out simple commands to browse a BACnet network, read properties from BACnet devices, or write to them.

Python is a simple language to learn and a very powerful tool for data processing. Coupled with BACnet, it becomes a great tool to test devices and interact with controllers.

BAC0 takes its name from the default IP port used by BACnet/IP communication which is port 47808. In hexadecimal, it's written 0xBAC0.

Test driven development (TDD) for DDC controls
----------------------------------------------

BAC0 is made for building automation system (BAS) programmers. Controllers used in this field are commonly called DDC Controllers (Direct Digital Control).

Typical controllers can be programmed in different ways, depending on the manufacturer selling them (block programming, basic "kinda" scripts, C code, etc...). BAC0 is a unified way, using Python language and BACnet/IP communication, to interact with those controllers once their sequence is built.

BAC0 allows users to simply test an application even if sensors are not connected to the controller. Using the out_of_service property, it's easy to write a value to the input so the controller will think an input is connected.