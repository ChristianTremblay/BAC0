#!/usr/bin/python
# -*- coding: utf-8 -*-
import importlib.util
import os

if importlib.util.find_spec("bacpypes3") is not None:
    import bacpypes3  # noqa: F401

else:
    # Using print here or setup.py will fail
    print("=" * 80)
    print(
        'BACpypes3 module missing, please install latest version using \n    $ "pip install BACpypes3"'
    )
    print("\nDiscard this message if you are actually installing BAC0.")
    print("=" * 80)

if importlib.util.find_spec("dotenv") is not None:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.getcwd(), ".env"))
else:
    print("You need to pip install python-dotenv to use your .env file")

try:
    from . import core, tasks  # noqa: F401
    from .core.devices.Device import DeviceLoad as load  # noqa: F401
    from .core.devices.Device import device as device  # noqa: F401
    from .core.devices.Trends import TrendLog as TrendLog  # noqa: F401
    from .core.utils.notes import update_log_level as log_level  # noqa: F401
    from .infos import __version__ as version  # noqa: F401
    from .scripts.Base import Base  # noqa: F401

    # Kept for compatibility
    from .scripts.Lite import Lite as connect  # noqa: F401
    from .scripts.Lite import Lite as lite  # noqa: F401

    # New preferred way to start
    from .scripts.Lite import Lite as start  # noqa: F401
    from .tasks.Devices import AddDevice as add_device  # noqa: F401
    from .tasks.Match import Match as match  # noqa: F401
    from .tasks.Poll import SimplePoll as poll  # noqa: F401

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
