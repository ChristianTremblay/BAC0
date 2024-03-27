import typing as t

from . import const

FILE_HEADER = const.FILE_HEADER
FILE_FOOTER = const.FILE_FOOTER
TAG = const.TAG


def convert(d, device_name=None):
    list_of_tags = []
    OBJECT_TYPE = {
        "analogValue": "AV",
        "analogInput": "AI",
        "analogOutput": "AO",
        "binaryInput": "BI",
        "binaryValue": "BV",
        "binaryOutput": "BO",
        "multiStateInput": "MI",
        "multiStateValue": "MV",
        "multiStateOutput": "MO",
    }
    DATATYPES = {
        "AI": "float",
        "AO": "float",
        "AV": "float",
        "BI": "boolean",
        "BO": "boolean",
        "BV": "boolean",
        "MI": "unsignedInt",
        "MO": "unsignedInt",
        "MV": "unsignedInt",
    }

    WRITE_PRIORITY = {
        "AI": 0,
        "AO": 8,
        "AV": 10,
        "BI": 0,
        "BO": 8,
        "BV": 10,
        "MI": 0,
        "MO": 8,
        "MV": 10,
    }

    for each in d.points:
        data: t.Dict[str, t.Union[str, int]] = {}
        name = device_name if device_name else d.properties.name
        obj_type = OBJECT_TYPE[each.properties.type]
        data["name"] = f"{name}/{each.properties.name}"
        data["group"] = ""
        data["object_type"] = obj_type
        data["object_instance"] = each.properties.address
        data["device_id"] = d.properties.device_id
        data["data_type"] = DATATYPES[obj_type]
        data["object_property"] = 85
        data["write_priority"] = WRITE_PRIORITY[obj_type]
        data["cov"] = "false"
        data["refresh_time"] = 1000
        data["access_mode"] = "READ"
        data["active"] = "false"
        data["comment"] = each.properties.description
        data["array_index"] = -1
        list_of_tags.append(TAG.format(d=data))

        file = FILE_HEADER
        for tag in list_of_tags:
            file += tag
        file += FILE_FOOTER
        write_tags_import_file(name, file)


def write_tags_import_file(name, file):
    with open(f"{name}.xml", "w") as xml_file:
        xml_file.write(file)
