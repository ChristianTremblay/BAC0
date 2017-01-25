#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    from . import core
    from . import tasks
    from .scripts.BasicScript import BasicScript 
    from .scripts.ReadWriteScript import ReadWriteScript as connect
    #from .core.functions.GetIPAddr import HostIP as ip
    from .core.devices.Device import Device as device
    from .core.devices.Device import DeviceLoad as load
    from .tasks.Poll import SimplePoll as poll
    from .tasks.Match import Match as match
    from .bokeh.BokehRenderer import BokehPlot as chart
    from .infos import __version__ as version
except ImportError as error:
    print(error)
    # Not installed yet