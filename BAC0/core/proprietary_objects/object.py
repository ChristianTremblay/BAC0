from bacpypes.object import Object, Property, register_object_type

# Prochaine étape : créer une focntion qui va lire "all" et se redéfinir dynamiquement
def create_proprietary_object(params):
    try:
        _validate_params(params)
    except:
        raise
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
