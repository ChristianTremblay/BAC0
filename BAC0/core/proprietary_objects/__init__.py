#!/usr/bin/python
# -*- coding: utf-8 -*-
from .jci import JCIDeviceObject, JCIAnalogValueObject
from .object import create_proprietary_object

create_proprietary_object(JCIAnalogValueObject)
create_proprietary_object(JCIDeviceObject)