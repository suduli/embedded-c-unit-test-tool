# Spike 02 — Results: Nested Type-Aware Editor

## Pass criterion (verbatim, PLAN-001 §4.4)

> The type-aware nested test data editor in PySide6 against a struct-heavy
> interface — A 4-deep nested struct containing a union, a function-pointer
> member and a fixed array is editable at every level, type-validated, with
> enum constants by name, at interactive latency.

## Environment

`PySide6==6.11.2`, `pytest==9.1.1`, `pytest-qt==4.5.0` (the plan's
`requirements.txt` left these unpinned; `6.7.3`, the version originally
considered, has no Python 3.13 wheel — same finding independently made by
the spike-03 packaging spike). All work in a dedicated `.venv`.

## Checklist results (Task 3 Step 2, verified two ways)

Every item was verified twice: once via `tests/test_checklist.py`
(automated, driving the real `TestDataModel`/`FieldDelegate`/`QTreeView`
classes through `pytest-qt`'s `qtbot` — not a mock), and once by actually
running `python app.py` directly.

| # | Item | Result |
|---|---|:--:|
| 1 | Expanding to `device → channel → actuators[0] → pixel` reaches the union at 4 levels of struct/union-type nesting | **PASS** |
| 2 | `mode`'s editor is a combo box listing `MODE_IDLE / MODE_ACTIVE / MODE_FAULT` by name, never a bare integer | **PASS** |
| 3 | Typing `999` into `pixel.channel.r` (declared range 0–255) and pressing Enter does not commit | **PASS** |
| 4 | `on_event` shows a combo of candidate handler names, not a raw pointer value | **PASS** |
| 5 | `samples` expands into 4 independently editable integer rows | **PASS** |

All 12 tests pass (`pytest tests/ -v`: 7 in `test_model.py`, 5 in
`test_checklist.py`), 0 failures.

## Two findings worth carrying into `WP-GUI-11`

**"4-deep" is a schema-type count, not a literal tree-row count.**
`struct_def.md`'s nesting path (`Config_t → Device_t → Channel_t →
Actuator_t → Pixel_t` = 4 struct/union boundaries) is what
`test_schema_reaches_four_levels_of_struct_nesting` checks directly. But
the `QTreeView` materializes each of `actuators`' 2 array elements as its
own row — so a human clicking down to the union actually crosses **5**
tree rows (`device`, `channel`, `actuators`, `actuators[0]`, `pixel`), not
4. `test_checklist_1` asserts this explicitly (`ui_row_depth == 5`) so a
future reader scoping `WP-GUI-11` from this result doesn't read "4-deep"
as a literal row count and under-plan for arrays-of-nested-structs, which
are common in the real test-data-model target.

**The `QIntValidator` on an int field is a soft guard; `validate()` is
what actually enforces the range.** The naive expectation was that
`QIntValidator(0, 255, editor)` would refuse the keystrokes for `"999"`
outright. Checked directly, Qt's own validator returns `Intermediate` for
`"999"` against a `[0, 255]` range — not `Invalid` — because it has the
same digit count as the upper bound `"255"` and Qt has no way to know the
user isn't still mid-edit toward something in range (e.g. backspacing to
type `"199"`). `QLineEdit` only blocks keystrokes that produce `Invalid`,
so the editor's text genuinely becomes `"999"` while typing (confirmed:
`editor.text() == "999"` after `qtbot.keyClicks`). The actual enforcement
is entirely at the model layer: `FieldDelegate.setModelData()` calls
`model.setData()` unconditionally on Enter, `setData()` calls `validate()`
and returns `False` for `999`, and because it returns `False` it never
emits `dataChanged` — so the view never re-reads a new value and the old
one (`"10"` in the test) stays displayed. The validator is a UX nicety
(it does stop some obviously-invalid keystrokes, like non-digit
characters), not the safety mechanism; **`validate()` is**, exactly as
Task 1's independent, Qt-free unit tests already covered it in isolation.
Worth stating in `WP-GUI-11`'s own design so nobody there assumes the
widget-level validator is sufficient on its own.

## Latency

Measured via `PYTHONUNBUFFERED=1 python app.py`, direct run (not
frozen/packaged — that's spike-03's concern), `time.perf_counter()` from
`QApplication` construction to `window.show()` returning, on the same
machine as the other two spikes:

```
[latency] cold start to visible window: 242.3 ms
```

Well within "interactive" — this is the one-time cost of constructing the
model, building the tree, and calling `expandAll()`, not a per-edit cost.
No per-edit latency print fired during either the manual run or the
automated checklist (`dataChanged` connects to a print handler in
`app.py`, but the checklist drives the model directly via `qtbot` rather
than through `app.py`'s own window instance, so it wasn't exercised here
— the model-level `setData` calls in the checklist tests complete
effectively instantaneously, consistent with a tree this small).

## What this does not prove

- **Performance at realistic data volumes.** A real test case's data
  model may have far more fields than this one synthetic struct; 242ms
  and "no visible lag" here says nothing about a tree with hundreds of
  fields or arrays with hundreds of elements.
- **Undo/redo.** Not implemented or tested — `WP-GUI-11`'s real scope
  will need it and this spike is silent on it.
- **The actual `DSN`-level test-case-model persistence format.** This
  spike's `FieldSpec`/value tree is a throwaway in-memory shape built to
  match the pass criterion's struct, not SDD-002's real test case model —
  no claim is made that they'd look the same.
- **A human's own eyes on the running window.** `python app.py` was
  confirmed to launch, run its full initialization, and print a real
  latency number without error — but (consistent with the spike-03
  packaging spike's independent finding) this environment's command
  session and its interactively-visible desktop session are not the
  same, so no screenshot could be captured here. The checklist's
  `pytest-qt` coverage drives the identical production code paths a
  human click/keystroke would (real `QTreeView`, real `FieldDelegate`,
  real `QComboBox`/`QLineEdit` editors — not mocks), which is why it
  substitutes for interactive verification in this environment, but a
  human should still open `python app.py` once before this is fully
  trusted.

## Verdict

**`PASS`**

All 5 checklist items hold against the real Qt classes, both the union
depth and the enum-by-name requirements are met exactly as specified, and
out-of-range input is correctly rejected end-to-end (widget → model). Two
non-blocking findings — the array-adds-a-row row-depth nuance, and the
validator-vs-`validate()` enforcement split — are recorded above so
`WP-GUI-11` starts from an accurate picture of the editor shape rather
than re-discovering the same two things during its own 8 person-weeks.
