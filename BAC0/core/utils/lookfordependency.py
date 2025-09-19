import importlib.util
from typing import Type, Callable, Any


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
        _RICH = False
        return (_RICH, FakeRich)
    try:
        rich_spec = importlib.util.find_spec("rich")
        if rich_spec is not None:
            rich = import_module("rich")
            _RICH = True
        else:
            _RICH = False
    except ImportError:
        _RICH = False
        rich = False
    return (_RICH, rich)


def influxdb_if_available(version:int = 2) -> tuple[bool, int, Any]:
    if version == 2:
        if not check_dependencies(["influxdb_client"]):
            _INFLUXDB = False
            return (_INFLUXDB, 2, FakeInflux)
        try:
            influxdb_spec = importlib.util.find_spec("influxdb_client")
            if influxdb_spec is not None:
                influxdb_client = import_module("influxdb_client")
                _INFLUXDB = True
            else:
                _INFLUXDB = False
        except ImportError:
            _INFLUXDB = False
            influxdb_client = False
        return (_INFLUXDB, 2, influxdb_client)
    elif version == 3:
        if not check_dependencies(["influxdb_client_3"]):
            _INFLUXDB = False
            return (_INFLUXDB, 3, FakeInflux)
        try:
            influxdb_spec = importlib.util.find_spec("influxdb_client_3")
            if influxdb_spec is not None:
                influxdb_client = import_module("influxdb_client_3.InfluxDBClient3")
                _INFLUXDB = True
            else:
                _INFLUXDB = False
        except ImportError:
            _INFLUXDB = False
            influxdb_client = False
        return (_INFLUXDB, 3, influxdb_client)
    return (False, 0, False)


def pandas_if_available() -> tuple[bool, Type, Callable, Callable]:
    if not check_dependencies(["pandas"]):
        _PANDAS = False
        return (_PANDAS, FakePandas, FakePandas.sql, FakePandas.Timestamp)

    try:
        pd = import_module("pandas")
        sql = import_module("pandas.io.sql")

        Timestamp = pd.Timestamp
        _PANDAS = True

    except ImportError:
        _PANDAS = False
        pd = FakePandas
        sql = FakePandas.sql
        Timestamp = FakePandas.Timestamp
    return (_PANDAS, pd, sql, Timestamp)


class FakePandas:
    "Typing in Device requires pandas, but it is not available"

    class DataFrame:
        id = "fake"

    def sql(self):
        return None

    def Timestamp(self):
        return None


class FakeInflux:
    "Typing in Device requires influxdb_client, but it is not available"
    pass


class FakeRich:
    pass
