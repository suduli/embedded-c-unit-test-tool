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


from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


class _Node:
    # DEVIATION from plan (see RESULTS.md "Deviations"): added `children_cache`.
    # Without it, `_children_of()` builds a fresh list of `_Node` objects on
    # every call. `createIndex()` stores a raw pointer to whichever `_Node`
    # was current at that moment; nothing else keeps that specific object
    # alive, so Python garbage-collects it as soon as the enclosing call
    # returns, and a later `internalPointer()` on the same QModelIndex reads
    # freed memory (observed as an unrelated bound-method object landing at
    # the reused address, and an AttributeError on `.spec`). Caching each
    # node's children on the node itself keeps the whole tree reachable from
    # `self._root`, which the model holds for its own lifetime.
    __slots__ = ("spec", "parent", "row_in_parent", "key", "children_cache")

    def __init__(self, spec: FieldSpec, parent, row_in_parent: int, key):
        self.spec = spec
        self.parent = parent
        self.row_in_parent = row_in_parent
        self.key = key  # dict key or list index used to read/write the value container
        self.children_cache = None


class TestDataModel(QAbstractItemModel):
    def __init__(self, schema: FieldSpec, value: Any = None, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.value = value if value is not None else default_value_for(schema)
        self._root = _Node(schema, None, 0, None)

    def _children_of(self, node: _Node) -> list[_Node]:
        if node.children_cache is not None:
            return node.children_cache
        spec = node.spec
        if spec.kind in (FieldKind.STRUCT, FieldKind.UNION):
            result = [
                _Node(c, node, i, c.name) for i, c in enumerate(spec.children)
            ]
        elif spec.kind == FieldKind.ARRAY:
            element_spec = spec.children[0] if spec.children else None
            if element_spec is None:
                result = []
            else:
                result = [
                    _Node(element_spec, node, i, i) for i in range(spec.array_len)
                ]
        else:
            result = []
        node.children_cache = result
        return result

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
