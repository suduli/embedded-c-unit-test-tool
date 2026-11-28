# implements: DSN-ANA-070
"""Decision and condition inventory for CMP-ANA (TOOL-PAR-150, schema 1.6).

A *decision* is the controlling expression of ``if`` / ``while`` / ``do`` /
``for`` / ``?:``, or any other outermost ``&&`` / ``||`` expression. Its
*conditions* are the leaves left after ``&&``, ``||``, ``!``, parentheses and
implicit casts are removed, in source order. This follows what GCC 14
``-fcondition-coverage`` was observed to record (see
docs/verification/WP-ANA-08-decisions-analysis.md): ``switch`` and plain
comparisons stored in a variable are not decisions, unevaluated ``sizeof``
operands are skipped, and constant conditions are kept here but marked
``constant`` because the compiler drops them.

``line`` is the line GCC was observed to attach the record to; ``start_line``
and ``end_line`` bound the whole decision so a consumer can still match a
record the prediction misses.

libclang's Python binding does not expose operator kinds, so the C API is
called directly.
"""

from __future__ import annotations

import ctypes
from dataclasses import replace
from pathlib import Path
from typing import Any

from clang import cindex  # type: ignore[import-untyped]

from ectt.ana.model import ConditionModel, DecisionModel

__all__ = ["extract_function_decisions"]

_TRANSPARENT = ("PAREN_EXPR", "UNEXPOSED_EXPR")
_LOGICAL = ("&&", "||")
_CONSTANT_KINDS = ("INTEGER_LITERAL", "CHARACTER_LITERAL", "FLOATING_LITERAL", "CXX_BOOL_LITERAL_EXPR")
_UNEVALUATED = ("CXX_UNARY_EXPR",)  # sizeof / alignof


def _api(name: str, argtypes: list[Any], restype: Any) -> Any:
    function = getattr(cindex.conf.lib, name)
    function.argtypes = argtypes
    function.restype = restype
    return function


def _spelled(value: Any) -> str:
    """The text of a CXString result, whichever form the binding hands back."""
    if isinstance(value, str):
        return value
    return str(cindex.conf.lib.clang_getCString(value))


def _operator(node: Any, family: str) -> str:
    kind = _api(f"clang_getCursor{family}OperatorKind", [cindex.Cursor], ctypes.c_int)(node)
    return _spelled(_api(f"clang_get{family}OperatorKindSpelling", [ctypes.c_int], cindex._CXString)(kind))


def _spelling_position(location: Any) -> tuple[int, int]:
    line, column, offset = ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint()
    handle = ctypes.c_void_p()
    _api("clang_getSpellingLocation", [cindex.SourceLocation] + [ctypes.c_void_p] * 4, None)(
        location, ctypes.byref(handle), ctypes.byref(line), ctypes.byref(column), ctypes.byref(offset)
    )
    return line.value, column.value


class _Walker:
    def __init__(self, function: str, source: bytes) -> None:
        self.function = function
        self.source = source
        self.decisions: list[DecisionModel] = []
        self.complete = True

    # -- expression helpers -------------------------------------------------

    def _strip(self, node: Any) -> Any:
        """Drop parentheses and implicit casts around an expression."""
        while node.kind.name in _TRANSPARENT:
            children = list(node.get_children())
            if len(children) != 1:
                return node
            node = children[0]
        return node

    def _logical_operands(self, node: Any) -> list[Any] | None:
        """The operands of a ``&&`` / ``||`` / ``!`` node, else None."""
        if node.kind.name == "BINARY_OPERATOR" and _operator(node, "Binary") in _LOGICAL:
            return list(node.get_children())
        if node.kind.name == "UNARY_OPERATOR" and _operator(node, "Unary") == "!":
            return list(node.get_children())
        return None

    def _leaves(self, node: Any, negated: bool = False) -> list[tuple[Any, bool]]:
        """The conditions in order, each with whether it sits under an odd number of ``!``."""
        node = self._strip(node)
        operands = self._logical_operands(node)
        if operands is None:
            return [(node, negated)]
        if node.kind.name == "UNARY_OPERATOR":
            negated = not negated
        return [leaf for operand in operands for leaf in self._leaves(operand, negated)]

    def _is_logical_tree(self, node: Any) -> bool:
        """True when a ``&&`` / ``||`` sits at the top, possibly under ``!``."""
        node = self._strip(node)
        if node.kind.name == "BINARY_OPERATOR":
            return _operator(node, "Binary") in _LOGICAL
        if node.kind.name == "UNARY_OPERATOR" and _operator(node, "Unary") == "!":
            return any(self._is_logical_tree(child) for child in node.get_children())
        return False

    def _top_operator(self, node: Any) -> Any:
        node = self._strip(node)
        while node.kind.name == "UNARY_OPERATOR":
            node = self._strip(next(iter(node.get_children())))
        return node

    def _text(self, node: Any) -> str:
        start, end = node.extent.start.offset, node.extent.end.offset
        return " ".join(self.source[start:end].decode("utf-8", "replace").split())

    def _is_constant(self, node: Any) -> bool:
        if node.kind.name in _CONSTANT_KINDS or node.kind.name in _UNEVALUATED:
            return True
        if node.kind.name == "DECL_REF_EXPR":
            referenced = node.referenced
            return referenced is not None and referenced.kind.name == "ENUM_CONSTANT_DECL"
        if node.kind.name in ("UNARY_OPERATOR", "BINARY_OPERATOR"):
            children = list(node.get_children())
            return bool(children) and all(self._is_constant(self._strip(c)) for c in children)
        return False

    def _from_macro(self, node: Any) -> bool:
        """True when any part of the expression is spelled somewhere else."""
        expansion = (node.extent.start.line, node.extent.start.column)
        if _spelling_position(node.extent.start) != expansion:
            return True
        children = list(node.get_children())
        extents = {(c.extent.start.offset, c.extent.end.offset) for c in children}
        if len(children) > 1 and len(extents) == 1:
            return True
        return any(self._from_macro(child) for child in children)

    def _condition(self, leaf: Any, negated: bool) -> ConditionModel:
        macro = self._from_macro(leaf)
        text = leaf.spelling if macro and leaf.spelling else self._text(leaf)
        line, column = leaf.extent.start.line, leaf.extent.start.column
        return ConditionModel(
            line=line, column=column, expression=text, constant=self._is_constant(leaf), negated=negated
        )

    def _conditions(self, leaves: list[tuple[Any, bool]]) -> tuple[ConditionModel, ...]:
        found = [self._condition(leaf, negated) for leaf, negated in leaves]
        # Conditions from one macro use all read as the macro call: number them.
        texts = [c.expression for c in found]
        for i, condition in enumerate(found):
            if texts.count(condition.expression) > 1 and self._from_macro(leaves[i][0]):
                part = texts[: i + 1].count(condition.expression)
                found[i] = replace(condition, expression=f"{condition.expression} (part {part})")
        return tuple(found)

    def _record(self, kind: str, expression: Any, line: int, start_line: int) -> None:
        leaves = self._leaves(expression)
        self.decisions.append(
            DecisionModel(
                function=self.function,
                kind=kind,
                line=line,
                column=expression.extent.start.column,
                start_line=min(start_line, expression.extent.start.line),
                end_line=expression.extent.end.line,
                expression=self._text(expression),
                conditions=self._conditions(leaves),
                macro=self._from_macro(expression),
            )
        )
        for leaf, _ in leaves:
            self.visit(leaf)

    def _operator_line(self, left: Any, right: Any, symbol: str, fallback: int) -> int:
        """The source line of the operator between two operands.

        libclang reports the expression start, GCC the operator. When the
        operands cannot be told apart (a macro), the fallback stands.
        """
        start, end = left.extent.end.offset, right.extent.start.offset
        found = self.source.find(symbol.encode(), start, end) if start < end else -1
        return fallback if found < 0 else self.source.count(bytes([10]), 0, found) + 1

    # -- statement walk -----------------------------------------------------

    def _controlling(self, kind: str, expression: Any, line: int, start_line: int) -> None:
        self._record(kind, expression, line, start_line)

    def _for_condition(self, node: Any) -> tuple[Any | None, list[Any]]:
        """Split a ``for`` statement into its condition and the other children."""
        children = list(node.get_children())
        depth = 0
        semicolons: list[int] = []
        for token in node.get_tokens():
            if token.spelling == "(":
                depth += 1
            elif token.spelling == ")":
                depth -= 1
                if depth == 0:
                    break
            elif token.spelling == ";" and depth == 1:
                semicolons.append(token.extent.start.offset)
        if len(semicolons) != 2:
            # A header built by a macro cannot be split: say so, never guess.
            self.complete = False
            return None, children
        first, second = semicolons
        condition = next((c for c in children if first < c.extent.start.offset < second), None)
        return condition, [c for c in children if condition is None or c != condition]

    def visit(self, node: Any) -> None:
        kind = node.kind.name
        if kind in _UNEVALUATED:
            return
        children = list(node.get_children())
        line = node.location.line
        if kind in ("IF_STMT", "WHILE_STMT") and len(children) >= 2:
            condition = children[0]
            # GCC attaches an `if` record to the keyword and a loop record to the condition.
            predicted = line if kind == "IF_STMT" else condition.extent.start.line
            self._controlling("if" if kind == "IF_STMT" else "while", condition, predicted, line)
            children = children[1:]
        elif kind == "DO_STMT" and len(children) == 2:
            condition = children[1]
            self.visit(children[0])
            self._controlling("do", condition, condition.extent.start.line, condition.extent.start.line)
            return
        elif kind == "FOR_STMT":
            condition, children = self._for_condition(node)
            if condition is not None:
                self._controlling("for", condition, condition.extent.start.line, condition.extent.start.line)
        elif kind == "CONDITIONAL_OPERATOR" and len(children) == 3:
            condition = children[0]
            # GCC attaches a ternary record to the line of the `?`.
            marker = self._operator_line(condition, children[1], "?", line)
            self._controlling("ternary", condition, marker, condition.extent.start.line)
            children = children[1:]
        elif kind in ("BINARY_OPERATOR", "UNARY_OPERATOR") and self._is_logical_tree(node):
            top = self._top_operator(node)
            operands = list(top.get_children())
            marker = self._operator_line(operands[0], operands[1], _operator(top, "Binary"), top.location.line)
            self._record("expression", node, marker, node.extent.start.line)
            return
        elif kind == "UNEXPOSED_EXPR" and len(children) > 1:
            # A construct the binding does not name (GNU `a ?: b`): GCC records
            # a decision for it, so the inventory must not claim completeness.
            self.complete = False
        for child in children:
            self.visit(child)


def extract_function_decisions(
    function_cursor: Any, working_directory: str | Path | None = None
) -> tuple[tuple[DecisionModel, ...], bool]:
    """Return one function's decisions and whether the walk was complete.

    Order is the statement walk order, which is source order except that a
    ``do`` condition follows its body.
    """
    path = function_cursor.extent.start.file
    try:
        source = b""
        if path is not None:
            located = Path(path.name)
            if not located.is_absolute() and working_directory is not None:
                located = Path(working_directory) / located
            source = located.read_bytes()
    except OSError:
        source = b""
    walker = _Walker(function_cursor.spelling, source)
    for child in function_cursor.get_children():
        if child.kind.name == "COMPOUND_STMT":
            walker.visit(child)
    complete = walker.complete and bool(source)
    return tuple(walker.decisions), complete
