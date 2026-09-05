"""Programmatic verification of Task 3 Step 2's 5-item manual checklist.

Not part of the original plan's file list. Added because the executing
environment cannot be assumed to support live mouse/keyboard interaction
with the actual app.py window (Bash can launch the process but has no
bound pointer/keyboard for that specific window), even though a real,
non-offscreen Qt platform plugin was independently confirmed to launch
the app without error (see RESULTS.md). This drives the *real* app.py
classes (TestDataModel, FieldDelegate, QTreeView) through pytest-qt's
qtbot, exercising the same code paths a human click/keystroke would,
and asserts the exact outcome each checklist item names. It is offscreen
programmatic verification, not a substitute for a human eyeballing the
running app once (see RESULTS.md).
"""
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QComboBox, QLineEdit, QStyleOptionViewItem, QTreeView

from model import TestDataModel, CONFIG_SCHEMA, FieldKind
from delegates import FieldDelegate


def _child_by_name(model, parent_index, name):
    """Column-0 index of the child named `name` under parent_index."""
    for row in range(model.rowCount(parent_index)):
        idx0 = model.index(row, 0, parent_index)
        if model.spec_for_index(idx0).name == name:
            return idx0
    raise KeyError(f"no child named {name!r} under row={parent_index.row()}")


def _value_col(model, idx0):
    """Given a column-0 index, return the sibling column-1 (value) index."""
    return model.index(idx0.row(), 1, idx0.parent())


def _make_view(model, qtbot):
    view = QTreeView()
    view.setModel(model)
    view.setItemDelegate(FieldDelegate(view))
    view.expandAll()
    view.resize(600, 500)
    # view.edit() needs real geometry/exposure to place an editor; without
    # this, view.edit() silently returns False for cells that are deep
    # enough that expandAll() hasn't yet resolved a visual rect for them.
    with qtbot.waitExposed(view):
        view.show()
    return view


def _actuator0_index(model):
    device = _child_by_name(model, QModelIndex(), "device")
    channel = _child_by_name(model, device, "channel")
    actuators = _child_by_name(model, channel, "actuators")
    return model.index(0, 0, actuators)  # actuators[0]


# ---------------------------------------------------------------------------
# Checklist item 1: expanding device -> channel -> actuators -> [0] -> pixel
# reaches the union at 4 levels of nesting.
# ---------------------------------------------------------------------------
def test_checklist_1_reaches_union_at_four_levels_of_nesting(qtbot):
    model = TestDataModel(CONFIG_SCHEMA)
    view = _make_view(model, qtbot)
    qtbot.addWidget(view)

    device = _child_by_name(model, QModelIndex(), "device")
    channel = _child_by_name(model, device, "channel")
    actuators = _child_by_name(model, channel, "actuators")
    actuator0 = model.index(0, 0, actuators)
    pixel = _child_by_name(model, actuator0, "pixel")

    # NOTE (see RESULTS.md "Deviations"): "4-deep" in struct_def.md counts
    # struct/union TYPE boundaries crossed (Device_t -> Channel_t ->
    # Actuator_t -> Pixel_t = 4). That is a schema-level count -- exactly
    # what Task 1's test_schema_reaches_four_levels_of_struct_nesting
    # checks by walking FieldSpec.children directly, reused here:
    device_spec = next(c for c in CONFIG_SCHEMA.children if c.name == "device")
    channel_spec = next(c for c in device_spec.children if c.name == "channel")
    actuators_spec = next(c for c in channel_spec.children if c.name == "actuators")
    actuator_spec = actuators_spec.children[0]  # the array's element TYPE (one schema node)
    pixel_spec = next(c for c in actuator_spec.children if c.name == "pixel")
    assert pixel_spec.kind == FieldKind.UNION  # confirms the 4-deep TYPE path

    # The QTreeView UI, however, materializes each of the array's 2
    # elements as its own row (so a human can pick *which* actuator
    # before drilling in) -- one row the schema-type count above doesn't
    # have, since the schema stores a single element-type node shared by
    # every instance. Measured via QModelIndex parent-walking, the actual
    # UI row-path to "pixel" is therefore 5 rows deep, not 4. Confirmed
    # here explicitly so "N-deep" isn't read as a literal tree-row count
    # by whoever scopes WP-GUI-11 from this result.
    ui_row_depth = 0
    walk = pixel
    while walk.isValid():
        ui_row_depth += 1
        walk = model.parent(walk)
    assert ui_row_depth == 5, (
        f"expected 5 UI tree rows above (and including) pixel's row "
        f"(device, channel, actuators, actuators[0], pixel), got {ui_row_depth}"
    )
    assert model.spec_for_index(pixel).kind == FieldKind.UNION

    # and the QTreeView itself (after expandAll) reports every ancestor expanded
    assert view.isExpanded(device)
    assert view.isExpanded(channel)
    assert view.isExpanded(actuators)
    assert view.isExpanded(actuator0)
    # pixel row itself is present and selectable in the view
    assert pixel.isValid()


# ---------------------------------------------------------------------------
# Checklist item 2: double-clicking mode's value cell shows a combo box
# listing MODE_IDLE / MODE_ACTIVE / MODE_FAULT by name -- never a bare int.
# ---------------------------------------------------------------------------
def test_checklist_2_mode_editor_is_combo_box_of_names(qtbot):
    model = TestDataModel(CONFIG_SCHEMA)
    view = _make_view(model, qtbot)
    qtbot.addWidget(view)

    actuator0 = _actuator0_index(model)
    mode0 = _child_by_name(model, actuator0, "mode")
    mode_value = _value_col(model, mode0)

    # (a) delegate-level: exactly what the view calls when an edit trigger fires
    delegate = view.itemDelegate(mode_value)
    option = QStyleOptionViewItem()
    editor = delegate.createEditor(view.viewport(), option, mode_value)
    assert isinstance(editor, QComboBox), f"expected QComboBox, got {type(editor)}"
    items = [editor.itemText(i) for i in range(editor.count())]
    assert items == ["MODE_IDLE", "MODE_ACTIVE", "MODE_FAULT"]
    delegate.setEditorData(editor, mode_value)
    assert editor.currentText() in items
    assert editor.currentText() == model.value_for_index(mode_value)  # "MODE_IDLE" default
    editor.deleteLater()

    # never a bare integer in the display role either
    displayed = model.data(mode_value, Qt.DisplayRole)
    assert displayed in ("MODE_IDLE", "MODE_ACTIVE", "MODE_FAULT")
    assert not displayed.lstrip("-").isdigit()

    # (b) end-to-end: actually open the editor through the view, as a real
    # double-click on this cell would (QTreeView's default edit triggers
    # include DoubleClicked), and find the live combo box the view created.
    #
    # NOTE: the public QAbstractItemView.edit(QModelIndex) is a Qt slot
    # declared to return void; PySide6 hands that back as None regardless
    # of whether an editor actually opened, so None here is not a failure
    # signal -- checking for the live child widget below is the real test.
    view.setCurrentIndex(mode_value)
    view.edit(mode_value)
    qtbot.wait(50)
    live_combos = view.viewport().findChildren(QComboBox)
    assert len(live_combos) == 1
    assert [live_combos[0].itemText(i) for i in range(live_combos[0].count())] == [
        "MODE_IDLE", "MODE_ACTIVE", "MODE_FAULT",
    ]
    view.closePersistentEditor(mode_value)


# ---------------------------------------------------------------------------
# Checklist item 3: typing a value outside an int field's declared range
# (999 into pixel.channel.r, which is 0-255) and pressing Enter does NOT
# commit -- the old value remains displayed.
# ---------------------------------------------------------------------------
def test_checklist_3_out_of_range_int_is_not_committed(qtbot):
    model = TestDataModel(CONFIG_SCHEMA)
    view = _make_view(model, qtbot)
    qtbot.addWidget(view)

    actuator0 = _actuator0_index(model)
    pixel = _child_by_name(model, actuator0, "pixel")
    inner_channel = _child_by_name(model, pixel, "channel")  # Pixel_t.channel (r,g,b,a)
    r0 = _child_by_name(model, inner_channel, "r")
    r_value = _value_col(model, r0)
    assert model.spec_for_index(r_value).int_min == 0
    assert model.spec_for_index(r_value).int_max == 255

    # establish a known-good baseline distinct from both 0 and 999
    assert model.setData(r_value, "10", Qt.EditRole) is True
    assert model.data(r_value, Qt.DisplayRole) == "10"

    # (a) model-level defense: setData rejects the out-of-range value outright
    assert model.setData(r_value, "999", Qt.EditRole) is False
    assert model.data(r_value, Qt.DisplayRole) == "10", "old value must remain displayed"

    # (b) end-to-end through the real editor widget: open it, type "999",
    # press Enter, confirm the display is still unchanged afterwards.
    #
    # DEVIATION / finding (see RESULTS.md "Deviations"): the naive
    # assumption was that QIntValidator(0, 255, editor) would refuse the
    # keystrokes outright. Checked directly (QIntValidator(0,255)
    # .validate("999", 3)) it returns Intermediate, not Invalid -- "999"
    # has the same digit count as "255" so Qt treats it as possibly still
    # being edited into range, and QLineEdit only blocks keystrokes that
    # would produce Invalid, not Intermediate. So the editor's own text
    # DOES become "999" while typing. The actual enforcement is entirely
    # the model-level validate()/setData() rejection exercised in (a)
    # above: FieldDelegate.setModelData() calls model.setData() on Enter
    # without checking its return value, but since setData() returns
    # False for "999" it never emits dataChanged, so the view never
    # re-reads a new value and the old one stays displayed. The
    # QIntValidator is a soft, incomplete guard here -- validate() is
    # what actually holds the line, exactly as Task 1's independent unit
    # tests already covered it.
    view.setCurrentIndex(r_value)
    view.edit(r_value)
    qtbot.wait(30)
    editors = view.viewport().findChildren(QLineEdit)
    assert len(editors) == 1, "expected exactly one live QLineEdit editor for an INT field"
    editor = editors[0]
    editor.clear()
    qtbot.keyClicks(editor, "999")
    assert editor.text() == "999", (
        "confirms QIntValidator(0,255) treats '999' as Intermediate, not "
        "Invalid, and so does not block the keystrokes at the widget level "
        "-- see the deviation note above; this is expected, not a failure"
    )
    qtbot.keyClick(editor, Qt.Key_Return)
    qtbot.wait(30)
    assert model.data(r_value, Qt.DisplayRole) == "10", (
        "the old value must remain displayed: setData() rejected \"999\" "
        "and never emitted dataChanged, so the commit did not go through "
        "even though the validator let the text field hold \"999\""
    )


# ---------------------------------------------------------------------------
# Checklist item 4: on_event shows a combo of candidate handler names, not a
# raw function pointer value.
# ---------------------------------------------------------------------------
def test_checklist_4_on_event_editor_is_combo_of_handler_names(qtbot):
    model = TestDataModel(CONFIG_SCHEMA)
    view = _make_view(model, qtbot)
    qtbot.addWidget(view)

    actuator0 = _actuator0_index(model)
    on_event0 = _child_by_name(model, actuator0, "on_event")
    on_event_value = _value_col(model, on_event0)

    delegate = view.itemDelegate(on_event_value)
    option = QStyleOptionViewItem()
    editor = delegate.createEditor(view.viewport(), option, on_event_value)
    assert isinstance(editor, QComboBox), f"expected QComboBox, got {type(editor)}"
    items = [editor.itemText(i) for i in range(editor.count())]
    assert items == ["NULL", "handle_alarm", "handle_reset", "handle_noop"]
    delegate.setEditorData(editor, on_event_value)
    assert editor.currentText() == "NULL"  # default candidate, by name
    editor.deleteLater()

    displayed = model.data(on_event_value, Qt.DisplayRole)
    assert displayed in items
    # not a raw pointer-shaped value (e.g. "0x...", or a bare int/None)
    assert not displayed.startswith("0x")
    assert not displayed.lstrip("-").isdigit()


# ---------------------------------------------------------------------------
# Checklist item 5: samples expands into 4 individually editable integer
# rows.
# ---------------------------------------------------------------------------
def test_checklist_5_samples_array_has_four_editable_int_rows(qtbot):
    model = TestDataModel(CONFIG_SCHEMA)
    view = _make_view(model, qtbot)
    qtbot.addWidget(view)

    actuator0 = _actuator0_index(model)
    samples = _child_by_name(model, actuator0, "samples")
    assert model.rowCount(samples) == 4

    for row in range(4):
        name_idx = model.index(row, 0, samples)
        value_idx = model.index(row, 1, samples)
        spec = model.spec_for_index(value_idx)
        assert spec.kind == FieldKind.INT
        flags = model.flags(value_idx)
        assert flags & Qt.ItemIsEditable, f"samples[{row}] value column is not editable"
        # each row is independently addressable and editable, not aliased
        distinct_value = str(100 + row)
        assert model.setData(value_idx, distinct_value, Qt.EditRole) is True
        assert model.data(value_idx, Qt.DisplayRole) == distinct_value

    # confirm independence: all 4 rows now hold distinct values
    values = [model.data(model.index(r, 1, samples), Qt.DisplayRole) for r in range(4)]
    assert values == ["100", "101", "102", "103"]
