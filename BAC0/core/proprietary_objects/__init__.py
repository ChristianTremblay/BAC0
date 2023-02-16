#!/usr/bin/python
# -*- coding: utf-8 -*-
from .jci import (
    JCIAnalogInputObject,
    JCIAnalogOutputObject,
    JCIAnalogValueObject,
    JCIDeviceObject,
)
from .object import create_proprietary_object

create_proprietary_object(JCIAnalogValueObject)
create_proprietary_object(JCIAnalogInputObject)
create_proprietary_object(JCIAnalogOutputObject)
create_proprietary_object(JCIDeviceObject)
