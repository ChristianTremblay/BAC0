#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    from . import core
    from . import tasks
    from .scripts.BasicScript import BasicScript
    from .scripts.ReadWriteScript import ReadWriteScript as connect
    from .core.devices.Device import Device as device
    from .core.devices.Device import DeviceLoad as load
    from .tasks.Poll import SimplePoll as poll
    from .tasks.Match import Match as match
    from .infos import __version__ as version
except ImportError as error:
    print(error)
    # Not installed yet
