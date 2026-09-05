# Spike 03 — PyInstaller Distribution Spike

## Pass criterion (verbatim, PLAN-001 §4.4)

> PyInstaller-bundled PySide6 + libclang on a clean Windows machine with no
> Python. Installs and runs without administrative privileges, and is not
> quarantined by default endpoint security. Record size and cold-start time.

## What this spike tests

`app.py` is a minimal PySide6 window that also performs one real `libclang`
parse (`clang.cindex.Index.create()` + `.parse(...)`), so the resulting
PyInstaller bundle is a genuine test of "PySide6 + libclang together" — not
just PySide6 alone. `libclang`'s shared library is loaded via `ctypes` at
runtime, which is invisible to PyInstaller's static import analysis, so
`packaging.spec` explicitly collects it via `binaries=[...]`.

## How to reproduce

```powershell
# From spikes/spike-03-packaging/
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Sanity check the unbundled script first:
python app.py

# Build the bundle:
python -m PyInstaller packaging.spec --noconfirm

# Measure size and cold start:
powershell -File measure.ps1
```

Results (including exact package versions actually installed, in case they
differ from `requirements.txt` due to Python-version wheel availability) are
recorded in [`RESULTS.md`](RESULTS.md).

## Honest limits — read before trusting the verdict

This spike was built and measured on a developer machine (Python, git, and
other tooling already installed), **not** a clean Windows machine with no
Python. That is exactly what the pass criterion above asks for, and this
spike cannot fully provide it from inside an agentic coding session. See the
**"Honest limits of this spike"** section in [`RESULTS.md`](RESULTS.md) for
what this local run can and cannot prove, and what would close the gap
(running the built bundle on an actual clean VM). Do not read the verdict in
`RESULTS.md` as a clean-machine PASS — it is explicitly scoped as
`PASS (local build)` or `FAIL` for that reason.
