# BAC0

[![Build status](https://img.shields.io/github/actions/workflow/status/ChristianTremblay/BAC0/build-and-test.yml?branch=main&label=build&style=flat-square)](https://github.com/ChristianTremblay/BAC0/actions)
[![Coverage](https://coveralls.io/repos/github/ChristianTremblay/BAC0/badge.svg?branch=master)](https://coveralls.io/github/ChristianTremblay/BAC0?branch=master)
[![Documentation Status](https://readthedocs.org/projects/bac0/badge/?version=stable)](https://bac0.readthedocs.io/en/stable/)
[![Gitter](https://badges.gitter.im/ChristianTremblay/BAC0.svg)](https://gitter.im/ChristianTremblay/BAC0)

BAC0 is an asynchronous Python 3 (3.10 and over) scripting application that uses
[BACpypes3](https://github.com/JoelBender/BACpypes3) to process BACnet™ messages
on an IP network. This library provides simple commands to browse a BACnet
network, read properties from BACnet devices, and write to them.

Python is a simple language to learn and a very powerful tool for data processing.
Coupled with BACnet, it becomes a great tool to test devices and interact with
controllers.

BAC0 takes its name from the default IP port used by BACnet/IP communication:
port 47808 (0xBAC0).

## Test driven development (TDD) for DDC controls

BAC0 is made for building automation system (BAS) programmers. Controllers used
in this field are commonly called DDC Controllers (Direct Digital Control).

Typical controllers can be programmed in different ways depending on the
manufacturer (block programming, basic scripts, C code, etc.). BAC0 provides a
unified Python interface to interact with those controllers once their
sequences are built.

BAC0 allows users to easily test an application even if sensors are not
connected to the controller. Using the `out_of_service` property, it's simple to
write a value to an input so the controller will behave as if an input is
connected.

## Quick links

- Documentation: https://bac0.readthedocs.io/
- Source: https://github.com/ChristianTremblay/BAC0
- Chat: https://gitter.im/ChristianTremblay/BAC0

## Contributing

See the documentation for development, testing and contribution guidelines.

## License

Licensed under LGPLv3. See the `LICENSE` file in the project root for details.
