#!/usr/bin/python
# -*- coding: utf-8 -*-
import importlib.util
import os

if importlib.util.find_spec("bacpypes3") is not None:
    import bacpypes3

else:
    # Using print here or setup.py will fail
    print("=" * 80)
    print(
        'bacpypes module missing, please install latest version using \n    $ "pip install bacpypes"'
    )
    print("\nDiscard this message if you are actually installing BAC0.")
    print("=" * 80)

if importlib.util.find_spec("dotenv") is not None:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.getcwd(), ".env"))
else:
    print("You need to pip install python-dotenv to use your .env file")

try:
    from . import core, tasks
    from .core.devices.Device import DeviceLoad as load
    from .core.devices.Device import device as device
    from .core.devices.Trends import TrendLog as TrendLog
    from .core.utils.notes import update_log_level as log_level
    from .infos import __version__ as version
    from .scripts.Base import Base
    from .tasks.Devices import AddDevice as add_device
    from .tasks.Match import Match as match
    from .tasks.Poll import SimplePoll as poll

    from .scripts.Lite import Lite as lite  # to maintain compatibility with old code

    # from .scripts.Lite import Lite as app
    # Import proprietary classes
    # from .core.proprietary_objects.legacy import jci

except ImportError as error:
    print("=" * 80)
    print(
        'Import Error, refer to documentation or reinstall using \n    $ "pip install BAC0"\n {}'.format(
            error
        )
    )
    print("\nDiscard this message if you are actually installing BAC0.")
    print("=" * 80)
    # Probably installing the app...
