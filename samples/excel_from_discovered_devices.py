import BAC0
import time
import pandas as pd
from BAC0.core.proprietary_objects.jci import tec_short_point_list

"""
This sample creates an Excel file containing one sheet per controller found on the network
Each sheet contyains all the points known by BAC0. Some proprietary point could not display here.
"""

EXCEL_FILE_NAME = "all_controllers_and_points.xlsx"


def create_data(discovered_devices, network):
    devices = {}
    dataframes = {}
    for each in discovered_devices:
        name, vendor, address, device_id = each

        # try excep eventually as we may have some issues with werid devices
        if "TEC3000" in name:
            custom_obj_list = tec_short_point_list()
        else:
            custom_obj_list = None
        devices[name] = BAC0.device(
            address, device_id, network, poll=0, object_list=custom_obj_list
        )

        # While we are here, make a dataframe with device
        dataframes[name] = make_dataframe(devices[name])
    return (devices, dataframes)


def make_dataframe(dev):
    lst = {}
    for each in dev.points:
        lst[each.properties.name] = {
            "value": each.lastValue,
            "units or states": each.properties.units_state,
            "description": each.properties.description,
            "object": "{}:{}".format(each.properties.type, each.properties.address),
        }
    df = pd.DataFrame.from_dict(lst, orient="index")
    return df


def make_excel(dfs):
    with pd.ExcelWriter(EXCEL_FILE_NAME) as writer:
        for k, v in dfs.items():
            v.to_excel(writer, sheet_name=k)


def main():
    bacnet = BAC0.lite()
    bacnet.discover()
    print("Creating DATA")
    devices, dataframes = create_data(bacnet.devices, network=bacnet)
    print("Creating and Excel File")
    make_excel(dataframes)


if __name__ == "__main__":
    main()
