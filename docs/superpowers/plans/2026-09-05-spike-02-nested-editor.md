# WP-SPIKE-02 — Nested Type-Aware Editor Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Adaptation note:** P0 validation spike, not production feature work. Pure-Python validation/model logic is unit-tested per the skill's TDD pattern; the Qt wiring itself is verified by running the app and (if a screenshot tool is available in the executing environment) capturing one screenshot for the record, since GUI interaction is impractical to fully unit-test.

**Goal:** Prove that a 4-deep nested C struct — containing a union, a function-pointer member, and a fixed array — can be presented and edited at every level in a PySide6 tree editor, with type validation and enum constants shown by name, at interactive latency. This is ADR-001 §6 (R-02) and SDD-001 §9's named schedule driver (`WP-GUI-11` is the single largest work package in PLAN-001 at 8 person-weeks) — the point of prototyping it now, before `WP-GUI-10` commits to an editor model, is to surface any structural problem while it is still cheap to change.

**Architecture:** A small, C-struct-shaped Python type-descriptor system (`FieldSpec` tree) drives a `QAbstractItemModel` exposing the nested structure as rows; per-kind `QStyledItemDelegate` subclasses provide type-appropriate editors (combo box for enums, validated line edits for numerics, a view-selector for the union, a candidate-list combo for the function pointer). Validation logic is plain Python, independently unit-tested; the Qt layer is a thin binding over it.

**Tech Stack:** Python 3.13, PySide6, pytest, pytest-qt (for driving the model/delegates without manual interaction where practical).

**Spec:** [`PLAN-001-specification-analysis-and-work-breakdown.md`](../../../PLAN-001-specification-analysis-and-work-breakdown.md) §4.4 (`WP-SPIKE-02` pass criterion), [`design/SDD-002-interfaces.md`](../../SDD-002-interfaces.md) (test case model, if it defines a nested value representation — check before Task 1 and align field naming if so)

## Global Constraints

- Pass criterion (PLAN-001 §4.4, verbatim): "The type-aware nested test data editor in PySide6 against a struct-heavy interface — A 4-deep nested struct containing a union, a function-pointer member and a fixed array is editable at every level, type-validated, with enum constants by name, at interactive latency."
- ADR-001's assumed GUI position is PySide6 (Qt) — use it, do not substitute another toolkit; part of what this spike tests is whether PySide6 itself is adequate for this editor shape.
- This is UI-adjacent work: per the user's standing convention, prefer a screenshot for visual verification over heavyweight browser/UI automation where one is available; do not spend excessive effort building a full automation harness for a throwaway spike.

---

## File Structure

```
spikes/spike-02-nested-editor/
  README.md                 # what this spike tests, how to reproduce, links back to PLAN-001 §4.4
  requirements.txt          # PySide6, pytest, pytest-qt
  struct_def.md             # the C struct this spike models, with the nesting-depth count spelled out
  model.py                  # FieldSpec schema + TestDataModel(QAbstractItemModel)
  delegates.py              # per-kind QStyledItemDelegate subclasses
  app.py                    # QMainWindow wiring it together, runnable directly
  tests/
    test_model.py           # pure-Python: schema construction, value get/set, validation
  RESULTS.md                # filled in after running — outcome record, incl. a screenshot if captured
```

---

### Task 1: The struct definition and its Python schema

**Files:**
- Create: `spikes/spike-02-nested-editor/struct_def.md`
- Create: `spikes/spike-02-nested-editor/model.py`
- Test: `spikes/spike-02-nested-editor/tests/test_model.py`

**Interfaces:**
- Produces (for Task 2 and Task 3 to consume):
  - `FieldKind` — a `str` Enum: `INT`, `FLOAT`, `ENUM`, `ARRAY`, `STRUCT`, `UNION`, `FUNCPTR`, `CHAR_ARRAY`.
  - `FieldSpec(name: str, kind: FieldKind, children: list["FieldSpec"] = [], enum_values: list[str] | None = None, array_len: int | None = None, int_min: int | None = None, int_max: int | None = None, funcptr_candidates: list[str] | None = None)` — a `@dataclass`, immutable schema (no runtime values).
  - `CONFIG_SCHEMA: FieldSpec` — the module-level constant: the root `FieldSpec` for the spike's struct (see struct_def.md below), consumed directly by `model.py`'s `TestDataModel` and by `tests/test_model.py`.
  - `default_value_for(spec: FieldSpec) -> Any` — builds a nested dict/list default value tree matching `spec`.
  - `validate(spec: FieldSpec, raw_text: str) -> tuple[bool, Any | str]` — returns `(True, parsed_value)` on success or `(False, error_message)` on failure. Used by delegates in Task 2; independently testable without Qt.

- [ ] **Step 1: Write `struct_def.md`** documenting the exact C struct being modeled, with the nesting path spelled out so the "4-deep" claim in RESULTS.md is checkable, not asserted:

```markdown
# The struct under test

    typedef enum { MODE_IDLE, MODE_ACTIVE, MODE_FAULT } Mode_t;

    typedef union {
        uint32_t raw;
        struct { uint8_t r, g, b, a; } channel;
    } Pixel_t;

    typedef struct {                   /* depth 3 */
        Mode_t       mode;             /* enum, by name */
        Pixel_t      pixel;            /* union */
        void       (*on_event)(int);   /* function pointer */
        int32_t      samples[4];       /* fixed array */
    } Actuator_t;

    typedef struct {                   /* depth 2 */
        Actuator_t actuators[2];
        char       label[16];
    } Channel_t;

    typedef struct {                   /* depth 1 */
        Channel_t channel;
        uint16_t  id;
    } Device_t;

    typedef struct {                   /* depth 0 (root) */
        Device_t device;
        float     scale;
    } Config_t;

Nesting path exercised: `Config_t` (0) → `.device` `Device_t` (1) →
`.channel` `Channel_t` (2) → `.actuators[i]` `Actuator_t` (3) →
`.pixel` `Pixel_t`, a **union** (4). That is the 4-deep path the pass
criterion names. `Actuator_t` alone also carries the function-pointer
member and the fixed array the criterion requires alongside the union —
all three land at the same tree level so the editor has to handle all of
them without one masking a bug in another.
```

- [ ] **Step 2: Write the schema tests first**

```python
# tests/test_model.py
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
        c for c in CONFIG_SCHEMA.children[0].children[0].children[0].children
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
```

Run: `pytest tests/test_model.py -v`
Expected: FAIL — `model.py` does not exist yet.

- [ ] **Step 3: Implement `model.py`'s schema and pure functions** (the `TestDataModel(QAbstractItemModel)` class is Task 2 — this step is Qt-free by design so it can be tested without a `QApplication`)

```python
# model.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class FieldKind(str, Enum):
    INT = "int"
    FLOAT = "float"
    ENUM = "enum"
    ARRAY = "array"
    STRUCT = "struct"
    UNION = "union"
    FUNCPTR = "funcptr"
    CHAR_ARRAY = "char_array"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: FieldKind
    children: list["FieldSpec"] = field(default_factory=list)
    enum_values: Optional[list[str]] = None
    array_len: Optional[int] = None
    int_min: Optional[int] = None
    int_max: Optional[int] = None
    funcptr_candidates: Optional[list[str]] = None


def _actuator_spec() -> FieldSpec:
    return FieldSpec(
        name="actuator", kind=FieldKind.STRUCT,
        children=[
            FieldSpec("mode", FieldKind.ENUM, enum_values=["MODE_IDLE", "MODE_ACTIVE", "MODE_FAULT"]),
            FieldSpec("pixel", FieldKind.UNION, children=[
                FieldSpec("raw", FieldKind.INT, int_min=0, int_max=0xFFFFFFFF),
                FieldSpec("channel", FieldKind.STRUCT, children=[
                    FieldSpec("r", FieldKind.INT, int_min=0, int_max=255),
                    FieldSpec("g", FieldKind.INT, int_min=0, int_max=255),
                    FieldSpec("b", FieldKind.INT, int_min=0, int_max=255),
                    FieldSpec("a", FieldKind.INT, int_min=0, int_max=255),
                ]),
            ]),
            FieldSpec("on_event", FieldKind.FUNCPTR,
                      funcptr_candidates=["NULL", "handle_alarm", "handle_reset", "handle_noop"]),
            FieldSpec("samples", FieldKind.ARRAY, array_len=4,
                      children=[FieldSpec("[i]", FieldKind.INT, int_min=-2147483648, int_max=2147483647)]),
        ],
    )


def _channel_spec() -> FieldSpec:
    return FieldSpec(
        name="channel", kind=FieldKind.STRUCT,
        children=[
            FieldSpec("actuators", FieldKind.ARRAY, array_len=2, children=[_actuator_spec()]),
            FieldSpec("label", FieldKind.CHAR_ARRAY, array_len=16),
        ],
    )


def _device_spec() -> FieldSpec:
    return FieldSpec(
        name="device", kind=FieldKind.STRUCT,
        children=[
            _channel_spec(),
            FieldSpec("id", FieldKind.INT, int_min=0, int_max=65535),
        ],
    )


CONFIG_SCHEMA = FieldSpec(
    name="config", kind=FieldKind.STRUCT,
    children=[
        _device_spec(),
        FieldSpec("scale", FieldKind.FLOAT),
    ],
)


def default_value_for(spec: FieldSpec) -> Any:
    if spec.kind == FieldKind.STRUCT:
        return {c.name: default_value_for(c) for c in spec.children}
    if spec.kind == FieldKind.UNION:
        return {c.name: default_value_for(c) for c in spec.children}
    if spec.kind == FieldKind.ARRAY:
        element_spec = spec.children[0] if spec.children else None
        return [default_value_for(element_spec) if element_spec else 0 for _ in range(spec.array_len)]
    if spec.kind == FieldKind.CHAR_ARRAY:
        return ""
    if spec.kind == FieldKind.ENUM:
        return spec.enum_values[0]
    if spec.kind == FieldKind.FUNCPTR:
        return spec.funcptr_candidates[0] if spec.funcptr_candidates else "NULL"
    if spec.kind == FieldKind.FLOAT:
        return 0.0
    return 0  # INT


def validate(spec: FieldSpec, raw_text: str) -> tuple[bool, Any]:
    if spec.kind == FieldKind.ENUM:
        if raw_text in (spec.enum_values or []):
            return True, raw_text
        return False, f"{raw_text!r} is not one of {spec.enum_values}"
    if spec.kind == FieldKind.FUNCPTR:
        if raw_text in (spec.funcptr_candidates or []):
            return True, raw_text
        return False, f"{raw_text!r} is not a known handler"
    if spec.kind == FieldKind.INT:
        try:
            value = int(raw_text, 0)
        except ValueError:
            return False, f"{raw_text!r} is not a valid integer"
        if spec.int_min is not None and value < spec.int_min:
            return False, f"{value} is below the minimum {spec.int_min}"
        if spec.int_max is not None and value > spec.int_max:
            return False, f"{value} exceeds the maximum {spec.int_max}"
        return True, value
    if spec.kind == FieldKind.FLOAT:
        try:
            return True, float(raw_text)
        except ValueError:
            return False, f"{raw_text!r} is not a valid float"
    if spec.kind == FieldKind.CHAR_ARRAY:
        max_len = (spec.array_len or 1) - 1  # room for the NUL terminator
        if len(raw_text) > max_len:
            return False, f"exceeds the {max_len}-character limit for a {spec.array_len}-byte buffer"
        return True, raw_text
    return False, f"unsupported field kind for direct text entry: {spec.kind}"
```

- [ ] **Step 4: Run the tests, verify they pass**

Run: `pytest tests/test_model.py -v`
Expected: PASS on all cases.

- [ ] **Step 5: Commit**

```bash
git add spikes/spike-02-nested-editor/struct_def.md spikes/spike-02-nested-editor/model.py spikes/spike-02-nested-editor/tests/test_model.py
git commit -m "spike-02: struct schema, defaults, and validation logic"
```

---

### Task 2: `QAbstractItemModel` binding

**Files:**
- Modify: `spikes/spike-02-nested-editor/model.py` (append the Qt-facing class — same file, since the model and its schema are one cohesive unit per the file-structure plan)

**Interfaces:**
- Consumes: `FieldSpec`, `CONFIG_SCHEMA`, `default_value_for` from Task 1.
- Produces (for Task 3's delegates and Task 4's app to consume): `TestDataModel(QAbstractItemModel)` with:
  - `__init__(self, schema: FieldSpec, value: Any = None)`
  - `spec_for_index(self, index: QModelIndex) -> FieldSpec` — used by delegates to pick the right editor.
  - `value_for_index(self, index: QModelIndex) -> Any`
  - Standard overrides: `index`, `parent`, `rowCount`, `columnCount`, `data`, `setData`, `flags`, `headerData`.

- [ ] **Step 1: Implement `TestDataModel`**

```python
# model.py (appended)
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


class _Node:
    __slots__ = ("spec", "parent", "row_in_parent", "key")

    def __init__(self, spec: FieldSpec, parent, row_in_parent: int, key):
        self.spec = spec
        self.parent = parent
        self.row_in_parent = row_in_parent
        self.key = key  # dict key or list index used to read/write the value container


class TestDataModel(QAbstractItemModel):
    def __init__(self, schema: FieldSpec, value: Any = None, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.value = value if value is not None else default_value_for(schema)
        self._root = _Node(schema, None, 0, None)

    def _children_of(self, node: _Node) -> list[_Node]:
        spec = node.spec
        if spec.kind in (FieldKind.STRUCT, FieldKind.UNION):
            return [
                _Node(c, node, i, c.name) for i, c in enumerate(spec.children)
            ]
        if spec.kind == FieldKind.ARRAY:
            element_spec = spec.children[0] if spec.children else None
            if element_spec is None:
                return []
            return [
                _Node(element_spec, node, i, i) for i in range(spec.array_len)
            ]
        return []

    def _value_at(self, node: _Node) -> Any:
        if node.parent is None:
            return self.value
        parent_value = self._value_at(node.parent)
        return parent_value[node.key]

    def _set_value_at(self, node: _Node, new_value: Any) -> None:
        parent_value = self._value_at(node.parent)
        parent_value[node.key] = new_value

    def index(self, row, column, parent=QModelIndex()):
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        children = self._children_of(parent_node)
        if row < 0 or row >= len(children):
            return QModelIndex()
        return self.createIndex(row, column, children[row])

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node: _Node = index.internalPointer()
        if node.parent is None or node.parent is self._root:
            return QModelIndex()
        return self.createIndex(node.parent.row_in_parent, 0, node.parent)

    def rowCount(self, parent=QModelIndex()):
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        return len(self._children_of(parent_node))

    def columnCount(self, parent=QModelIndex()):
        return 2  # name, value

    def spec_for_index(self, index: QModelIndex) -> FieldSpec:
        return index.internalPointer().spec

    def value_for_index(self, index: QModelIndex) -> Any:
        return self._value_at(index.internalPointer())

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        node: _Node = index.internalPointer()
        if index.column() == 0:
            return str(node.key) if isinstance(node.key, int) else node.spec.name
        value = self._value_at(node)
        if node.spec.kind in (FieldKind.STRUCT, FieldKind.UNION, FieldKind.ARRAY):
            return f"<{node.spec.kind.value}>"
        return str(value)

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or index.column() != 1:
            return False
        node: _Node = index.internalPointer()
        ok, parsed = validate(node.spec, str(value))
        if not ok:
            return False
        self._set_value_at(node, parsed)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not index.isValid():
            return base
        node: _Node = index.internalPointer()
        editable_kinds = (FieldKind.INT, FieldKind.FLOAT, FieldKind.ENUM, FieldKind.FUNCPTR, FieldKind.CHAR_ARRAY)
        if index.column() == 1 and node.spec.kind in editable_kinds:
            return base | Qt.ItemIsEditable
        return base

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ["Field", "Value"][section]
        return None
```

- [ ] **Step 2: Write a pytest-qt test that exercises the model without opening a visible window**

```python
# tests/test_model.py (append)
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
```

Run: `pip install pytest-qt && pytest tests/test_model.py -v`
Expected: PASS. (`qtbot` fixture comes from `pytest-qt`; it also handles constructing a headless `QApplication` for the test process.)

- [ ] **Step 3: Commit**

```bash
git add spikes/spike-02-nested-editor/model.py spikes/spike-02-nested-editor/tests/test_model.py spikes/spike-02-nested-editor/requirements.txt
git commit -m "spike-02: QAbstractItemModel binding over the struct schema"
```

---

### Task 3: Type-aware delegates

**Files:**
- Create: `spikes/spike-02-nested-editor/delegates.py`

**Interfaces:**
- Consumes: `TestDataModel.spec_for_index`, `FieldKind`, `validate` from Task 1/2.
- Produces: `FieldDelegate(QStyledItemDelegate)` — one delegate class that dispatches by `FieldKind`, used directly by Task 4's `app.py`.

- [ ] **Step 1: Implement the delegate**

```python
# delegates.py
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QLineEdit
from PySide6.QtGui import QIntValidator, QDoubleValidator
from model import FieldKind


class FieldDelegate(QStyledItemDelegate):
    """Dispatches to a type-appropriate editor per FieldKind.
    Enum and function-pointer fields always show names, never raw values —
    that is the specific claim the pass criterion makes and the reason
    this is a dedicated delegate rather than a bare QLineEdit everywhere.
    """

    def createEditor(self, parent, option, index):
        model = index.model()
        spec = model.spec_for_index(index)
        if spec.kind == FieldKind.ENUM:
            box = QComboBox(parent)
            box.addItems(spec.enum_values)
            return box
        if spec.kind == FieldKind.FUNCPTR:
            box = QComboBox(parent)
            box.addItems(spec.funcptr_candidates)
            return box
        if spec.kind == FieldKind.UNION:
            box = QComboBox(parent)
            box.addItems([c.name for c in spec.children])
            return box  # selects which member is the "active view"; editing that member is a child row
        editor = QLineEdit(parent)
        if spec.kind == FieldKind.INT:
            lo = spec.int_min if spec.int_min is not None else -2147483648
            hi = spec.int_max if spec.int_max is not None else 2147483647
            editor.setValidator(QIntValidator(lo, hi, editor))
        elif spec.kind == FieldKind.FLOAT:
            editor.setValidator(QDoubleValidator(editor))
        return editor

    def setEditorData(self, editor, index):
        value = index.model().value_for_index(index)
        if isinstance(editor, QComboBox):
            i = editor.findText(str(value))
            editor.setCurrentIndex(max(i, 0))
        else:
            editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.currentText() if isinstance(editor, QComboBox) else editor.text()
        model.setData(index, text)
```

- [ ] **Step 2: Manual verification checklist** (no automated test — this is exactly the interaction pytest-qt is weakest at covering meaningfully; run it and check by hand)

Run: `python app.py` (once Task 4 exists)
Confirm by direct interaction:
  1. Expanding `device → channel → actuators → [0] → pixel` reaches the union at 4 levels of nesting.
  2. Double-clicking `mode`'s value cell shows a combo box listing `MODE_IDLE / MODE_ACTIVE / MODE_FAULT` by name — never a bare integer.
  3. Typing a value outside an int field's declared range (e.g. `999` into `channel.r`, which is 0–255) and pressing Enter does **not** commit — the old value remains displayed.
  4. `on_event` shows a combo of candidate handler names, not a raw function pointer value.
  5. `samples` expands into 4 individually editable integer rows.

- [ ] **Step 3: Commit**

```bash
git add spikes/spike-02-nested-editor/delegates.py
git commit -m "spike-02: type-aware delegates (enum/funcptr/union by name, validated numerics)"
```

---

### Task 4: Runnable app, latency measurement, and RESULTS.md

**Files:**
- Create: `spikes/spike-02-nested-editor/app.py`
- Create: `spikes/spike-02-nested-editor/RESULTS.md`
- Modify: `spikes/README.md`

- [ ] **Step 1: Implement `app.py`**

```python
# app.py
import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView
from model import TestDataModel, CONFIG_SCHEMA
from delegates import FieldDelegate


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spike 02 — Nested Type-Aware Editor")
        self.model = TestDataModel(CONFIG_SCHEMA)
        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(FieldDelegate(self.view))
        self.view.expandAll()
        self.setCentralWidget(self.view)
        self.resize(480, 400)

        self._edit_start = None
        self.model.dataChanged.connect(self._on_data_changed)

    def _on_data_changed(self, *_):
        if self._edit_start is not None:
            elapsed_ms = (time.perf_counter() - self._edit_start) * 1000
            print(f"[latency] commit round-trip: {elapsed_ms:.1f} ms")
            self._edit_start = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launch_start = time.perf_counter()
    window = MainWindow()
    window.show()
    print(f"[latency] cold start to visible window: {(time.perf_counter() - launch_start) * 1000:.1f} ms")
    sys.exit(app.exec())
```

- [ ] **Step 2: Run it and work through Task 3 Step 2's manual checklist**

Run: `python app.py`
Expected: window opens, cold-start latency prints (should be well under 1000 ms for a tree this small — record the actual number), all 5 checklist items in Task 3 Step 2 pass. If a screenshot tool is available in the executing environment, capture one showing the tree expanded to the union level for the record.

- [ ] **Step 3: Write `RESULTS.md`** — must include, from the actual run:
  - The cold-start latency number printed by the app.
  - Pass/fail for each of the 5 manual checklist items in Task 3 Step 2, stated individually (not just "looks good").
  - The pytest-qt round-trip result from Task 2 Step 2.
  - Verdict: `PASS` if all 5 checklist items hold and no interaction felt laggy; otherwise name exactly which item failed and why, since `WP-GUI-11` (8 person-weeks, the largest single work package in PLAN-001) depends on knowing that *before* it starts, not after.
  - One paragraph on what this spike does **not** prove: it doesn't test performance at realistic data volumes (a real test case data set may have many more fields than this one struct), doesn't test undo/redo, and doesn't test the actual `DSN`-level test-case-model persistence format — it is purely an editor-shape feasibility check.

- [ ] **Step 4: Update `spikes/README.md`'s row for spike-02.**

- [ ] **Step 5: Commit**

```bash
git add spikes/spike-02-nested-editor/app.py spikes/spike-02-nested-editor/RESULTS.md spikes/README.md
git commit -m "spike-02: runnable app, latency measurement, and verdict"
```

---

## Self-Review

**Spec coverage:** Pass criterion clauses — "4-deep nested struct": Task 1's schema + `struct_def.md`'s explicit path. "containing a union, a function-pointer member and a fixed array": all three sit as siblings inside `Actuator_t` (Task 1 Step 3) — tested together deliberately per the Global Constraints note that they must not mask each other. "editable at every level": Task 2's `setData` plus Task 3's checklist item 1 (reaching the union at depth 4) and item 5 (array elements). "type-validated": Task 1's `validate()`, unit-tested, plus checklist item 3. "enum constants by name": checklist item 2, explicitly asserted never-a-bare-integer. "interactive latency": Task 4's timing instrumentation. All covered.

**Placeholder scan:** No TBD/TODO. Task 3 Step 2 and Task 4 Step 2's manual-checklist steps are deliberately manual (GUI interaction), not placeholders — each names the exact action and exact expected result.

**Type consistency:** `FieldSpec`, `FieldKind`, `validate`, `default_value_for` (Task 1) are consumed unchanged by `TestDataModel` (Task 2) and `FieldDelegate` (Task 3) — field and method names (`spec_for_index`, `value_for_index`, `.kind`, `.enum_values`, `.funcptr_candidates`, `.int_min`/`.int_max`) match at every use site.
