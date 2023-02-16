#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import bacpypes
except ImportError:
    # Using print here or setup.py will fail
    print("=" * 80)
    print(
        'bacpypes module missing, please install latest version using \n    $ "pip install bacpypes"'
    )
    print("\nDiscard this message if you are actually installing BAC0.")
    print("=" * 80)

try:
    from . import core, tasks
    from .core.devices.Device import Device as device
    from .core.devices.Device import DeviceLoad as load
    from .core.devices.Trends import TrendLog as TrendLog
    from .core.utils.notes import update_log_level as log_level
    from .infos import __version__ as version
    from .scripts.Base import Base
    from .tasks.Devices import AddDevice as add_device
    from .tasks.Match import Match as match
    from .tasks.Poll import SimplePoll as poll

    # To be able to use the complete version pandas, flask and bokeh must be installed.
    try:
        import bokeh
        import flask
        import flask_bootstrap
        import pandas

        _COMPLETE = True
    except ImportError:
        _COMPLETE = False

    try:
        #
        import os

        if os.path.isfile("{}/.env".format(os.getcwd())):
            from dotenv import load_dotenv

            load_dotenv(os.path.join(os.getcwd(), ".env"))
    except ImportError:
        print("You need to pip install python-dotenv to use your .env file")

    from .scripts.Lite import Lite as lite

    if _COMPLETE:
        from .scripts.Complete import Complete as gui

        connect = gui
    else:
        connect = lite  # type: ignore[assignment, misc]
        web = lambda: print(
            "All features not available to run BAC0.web(). Some modules are missing (flask, flask-bootstrap, bokeh, pandas). See docs for details. To start BAC0, use BAC0.lite()"
        )

    # Import proprietary classes
    from .core.proprietary_objects import jci

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
