from model import CONFIG_SCHEMA, FieldKind, default_value_for, validate


def test_schema_reaches_four_levels_of_struct_nesting():
    # Config_t -> device -> channel -> actuators[i] -> pixel (union)
    device = next(c for c in CONFIG_SCHEMA.children if c.name == "device")
    channel = next(c for c in device.children if c.name == "channel")
    actuators = next(c for c in channel.children if c.name == "actuators")
    actuator = actuators.children[0]
    pixel = next(c for c in actuator.children if c.name == "pixel")
    assert pixel.kind == FieldKind.UNION


def test_schema_has_union_funcptr_and_array_at_same_level():
    device = next(c for c in CONFIG_SCHEMA.children if c.name == "device")
    channel = next(c for c in device.children if c.name == "channel")
    actuators = next(c for c in channel.children if c.name == "actuators")
    actuator = actuators.children[0]
    kinds = {c.name: c.kind for c in actuator.children}
    assert kinds["pixel"] == FieldKind.UNION
    assert kinds["on_event"] == FieldKind.FUNCPTR
    assert kinds["samples"] == FieldKind.ARRAY


def test_default_value_builds_full_nested_tree():
    value = default_value_for(CONFIG_SCHEMA)
    assert value["device"]["channel"]["actuators"][1]["pixel"]["raw"] == 0
    assert len(value["device"]["channel"]["actuators"]) == 2
    assert len(value["device"]["channel"]["actuators"][0]["samples"]) == 4


def test_validate_enum_accepts_known_name_by_name_not_number():
    mode_spec = next(
        c for c in CONFIG_SCHEMA.children[0].children[0].children[0].children[0].children
        if c.name == "mode"
    )
    ok, value = validate(mode_spec, "MODE_ACTIVE")
    assert ok is True
    assert value == "MODE_ACTIVE"
    ok, _ = validate(mode_spec, "1")
    assert ok is False  # by name, not by number — a bare "1" is not a valid enum entry


def test_validate_int_rejects_non_numeric():
    ok, err = validate(FieldSpec_int(), "not-a-number")
    assert ok is False
    assert "not-a-number" in err or "invalid" in err.lower()


def test_validate_int_enforces_declared_range():
    from model import FieldSpec, FieldKind
    spec = FieldSpec(name="x", kind=FieldKind.INT, int_min=0, int_max=255)
    ok, err = validate(spec, "999")
    assert ok is False


def FieldSpec_int():
    from model import FieldSpec, FieldKind
    return FieldSpec(name="x", kind=FieldKind.INT)


def test_model_setdata_round_trip_via_index(qtbot):
    from PySide6.QtCore import Qt
    from model import TestDataModel, CONFIG_SCHEMA

    m = TestDataModel(CONFIG_SCHEMA)
    device_idx = m.index(0, 0)
    channel_idx = m.index(0, 0, device_idx)
    id_idx = m.index(1, 1, device_idx)  # Device_t.id, value column
    assert m.setData(id_idx, "42", Qt.EditRole) is True
    assert m.data(id_idx, Qt.DisplayRole) == "42"

    # invalid value is rejected and does not corrupt the stored value
    assert m.setData(id_idx, "not-a-number", Qt.EditRole) is False
    assert m.data(id_idx, Qt.DisplayRole) == "42"
