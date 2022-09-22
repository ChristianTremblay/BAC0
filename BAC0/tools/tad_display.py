from . import const

FILE_HEADER = const.FILE_HEADER
FILE_FOOTER = const.FILE_FOOTER
TAG = const.TAG

template_example = {
    "names": [("name", "dev_id")],
}


def convert(d, device_name=None, make_template=False):
    """
    Template : If true, will not populate name and device id so the file
    can be reused to create a dictionnary in T3 Studio with multiple
    devices. This will prevents us from switching dictionnary all the time.
    """
    list_of_tags = []
    device_id = None
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

    if make_template:
        device_name = "$DEVICE_NAME"
        device_id = "$DEVICE_ID"

    data = {}
    for each in d.points:
        name = device_name if device_name else d.properties.name
        data["name"] = "{}/{}".format(name, each.properties.name)
        data["group"] = ""
        data["object_type"] = OBJECT_TYPE[each.properties.type]
        data["object_instance"] = each.properties.address
        data["device_id"] = device_id if device_id else d.properties.device_id
        data["data_type"] = DATATYPES[data["object_type"]]
        data["object_property"] = 85
        data["write_priority"] = WRITE_PRIORITY[data["object_type"]]
        data["cov"] = "false"
        data["refresh_time"] = 1000
        data["access_mode"] = "READ"
        data["active"] = "false"
        data["comment"] = each.properties.description
        data["array_index"] = -1
        list_of_tags.append(TAG.format(d=data))

    return (name, list_of_tags)


def build_from_templates(list_of_tags, config={}):
    """
    Config must be a list of tuple (name, device_id)
    """
    _lst_of_tags = []
    for each in config:
        name, device_id = each
        for tag in list_of_tags:
            if "$DEVICE_NAME" in tag:
                tag.replace("$DEVICE_NAME", name)
            if "$DEVICE_ID" in tag:
                tag.replace("DEVICE_ID", device_id)
            _lst_of_tags.append(tag)
    return _lst_of_tags


def merge_templates(lst=[]):
    _lst = []
    for each in lst:
        _lst.extend(each)
    return _lst


def write_tags_import_file(name, list_of_tags):
    _content = FILE_HEADER
    for tag in list_of_tags:
        _content += tag
    _content += FILE_FOOTER
    with open("{}.xml".format(name), "w") as xml_file:
        xml_file.write(_content)
