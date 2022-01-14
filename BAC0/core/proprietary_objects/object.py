from bacpypes.object import (
    Object,
    Property,
    register_object_type,
    registered_object_types,
)

# Prochaine étape : créer une focntion qui va lire "all" et se redéfinir dynamiquement
def create_proprietary_object(params):

    try:
        _validate_params(params)
    except:
        raise
    # Prevent breaking change for existing code, since issue #311
    try:
        props = [
            Property(v["obj_id"], v["datatype"], mutable=v["mutable"])
            for k, v in params["properties"].items()
        ]
    except KeyError:
        props = [
            Property(v["obj_id"], v["primitive"], mutable=v["mutable"])
            for k, v in params["properties"].items()
        ]

    new_class = type(
        params["name"],
        (params["bacpypes_type"],),
        {"objectType": params["objectType"], "properties": props},
    )
    register_object_type(new_class, vendor_id=params["vendor_id"])
    if "BAC0" not in registered_object_types.keys():
        registered_object_types["BAC0"] = {}

    registered_object_types["BAC0"][params["name"]] = params["properties"]


def _validate_params(params):
    if not params["name"]:
        raise ValueError(
            "Proprietary definition dict must contains a name key with a custom class name"
        )
    if not params["vendor_id"]:
        raise ValueError("Vendor ID is mandatory")
    if not isinstance(params["properties"], dict):
        raise TypeError(
            "The definition must include a dict of properties. It can be empty."
        )
    if not issubclass(params["bacpypes_type"], Object):
        raise TypeError("bacpypes_type must be a subclass of bacpypes.object.Object")
    return True
