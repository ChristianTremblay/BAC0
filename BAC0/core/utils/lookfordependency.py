import importlib.util


# Function to dynamically import a module
def import_module(module_name, package=None):
    spec = importlib.util.find_spec(module_name, package)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_dependencies(module_name: list) -> bool:
    for each in module_name:
        _available = importlib.util.find_spec(each)
        if _available is None:
            return False
    return True


def rich_if_available():
    if not check_dependencies(["rich"]):
        return None
    try:
        rich_spec = importlib.util.find_spec("rich")
        if rich_spec is not None:
            rich = import_module("rich")
            _RICH = True
        else:
            _RICH = False
    except ImportError:
        _RICH = False
    return (_RICH, rich)


def influxdb_if_available():
    if not check_dependencies(["influxdb_client"]):
        return None
    try:
        influxdb_spec = importlib.util.find_spec("influxdb_client")
        if influxdb_spec is not None:
            influxdb_client = import_module("influxdb_client")
            _INFLUXDB = True
        else:
            _INFLUXDB = False
    except ImportError:
        _INFLUXDB = False
    return (_INFLUXDB, influxdb_client)


def pandas_if_available():
    global _PANDAS
    if not check_dependencies(["pandas"]):
        return None

    try:
        pd = import_module("pandas")
        sql = import_module("pandas.io.sql")
        Timestamp = None
        timestamp_spec = importlib.util.find_spec("pandas.Timestamp")
        if timestamp_spec is not None:
            Timestamp = pd.Timestamp
        else:
            timestamp_lib_spec = importlib.util.find_spec("pandas.lib.Timestamp")
            if timestamp_lib_spec is not None:
                Timestamp = import_module("pandas.lib").Timestamp

        _PANDAS = True
    except ImportError:
        _PANDAS = False
    return (_PANDAS, pd, sql, Timestamp)


def xlwings_if_available():
    if not check_dependencies(["xlwings"]):
        return None
    try:
        xlwings_spec = importlib.util.find_spec("xlwings")
        if xlwings_spec is not None:
            xlwings = import_module("xlwings")
            _XLWINGS = True
        else:
            _XLWINGS = False
    except ImportError:
        _XLWINGS = False
    return (_XLWINGS, xlwings)
