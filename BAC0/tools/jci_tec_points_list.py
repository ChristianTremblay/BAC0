def tec_short_point_list(unit_type="2-pipe"):
    """
    unit_type can be :
        - 4-pipe
        - 2-pipe
        - VAV
    """
    _lst = [
        ("binaryInput", 30827),
        ("binaryInput", 30828),
        ("binaryOutput", 86908),
        ("binaryOutput", 86909),
        ("binaryOutput", 86910),
        ("binaryOutput", 86911),
        ("binaryOutput", 86912),
        ("binaryOutput", 87101),
        ("binaryOutput", 87102),
        ("multiStateValue", 29501),
        ("multiStateValue", 29500),
        ("multiStateValue", 29509),
        ("multiStateValue", 29517),
        ("multiStateValue", 29518),
        ("multiStateValue", 29519),
        ("multiStateValue", 29520),
        ("multiStateValue", 29524),
        ("multiStateValue", 29525),
        ("multiStateValue", 29527),
        ("multiStateValue", 29712),
        ("multiStateValue", 29700),
        ("multiStateValue", 29709),
        ("multiStateValue", 29708),
        ("analogValue", 29505),
        # ("analogValue", 29502),
        # ("analogValue", 29503),
        ("analogValue", 29504),
        ("analogValue", 29506),
        ("analogValue", 29507),
        ("analogValue", 29508),
        ("analogValue", 29515),
        ("analogValue", 29522),
        ("analogValue", 29529),
        ("analogValue", 29530),
        ("analogValue", 29532),
        ("analogValue", 29701),
        ("analogValue", 29703),
        ("analogValue", 29705),
        ("analogValue", 29706),
        ("analogValue", 29707),
        ("analogValue", 29714),
        ("analogValue", 29717),
        ("analogValue", 29725),
        ("analogValue", 29726),
        ("analogValue", 29727),
        ("analogOutput", 86905),
        ("multiStateValue", 6),
        ("trendLog", 101010),
    ]
    if unit_type == "4-pipe":
        _lst.append(("analogOutput", 86914))
        _lst.append(("analogOutput", 86915))

    return _lst
