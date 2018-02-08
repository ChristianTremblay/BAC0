#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import core
from . import tasks
from .scripts.Base import Base
from .core.devices.Device import Device as device
from .core.devices.Device import DeviceLoad as load
from .tasks.Poll import SimplePoll as poll
from .tasks.Match import Match as match
from .infos import __version__ as version

# To be able to use the complete version pandas, flask and bokeh must be installed.
try:
    import pandas
    import bokeh
    import flask
    _COMPLETE = True
except ImportError:
    _COMPLETE = False

if _COMPLETE:
    from .scripts.Complete import Complete as connect
    from .scripts.Lite import Lite as lite
else:
    from .scripts.Lite import Lite as connect
