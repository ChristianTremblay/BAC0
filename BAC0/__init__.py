#!/usr/bin/python
# -*- coding: utf-8 -*-
from . import core
from . import tasks
from .scripts.BasicScript import BasicScript 
from .scripts.ReadWriteScript import ReadWriteScript as connect
#from .core.functions.GetIPAddr import getIPAddr as ip
from .core.devices.Device import Device as device
from .tasks.Poll import Poll as poll
from .tasks.Match import Match as match