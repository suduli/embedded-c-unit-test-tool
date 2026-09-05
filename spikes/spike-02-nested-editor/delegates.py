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
