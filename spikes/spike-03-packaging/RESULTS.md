# Spike 03 — Results: PyInstaller Distribution

## Pass criterion (verbatim, PLAN-001 §4.4)

> PyInstaller-bundled PySide6 + libclang on a clean Windows machine with no
> Python. Installs and runs without administrative privileges, and is not
> quarantined by default endpoint security. Record size and cold-start time.

## Environment

- OS: Windows 11 Home Single Language, build 10.0.26200
- Python: 3.13.2 (`C:\Program Files\Python313\python.exe`), used only to create a
  dedicated virtual environment at `spikes/spike-03-packaging/.venv` — nothing
  was installed into the system/global Python.
- Shell used for the build/measure commands: non-elevated `ROCKY\sudul`
  (confirmed via `[Security.Principal.WindowsPrincipal]::IsInRole(Administrator)`
  = `False` — see "Admin-privilege check" below).
- Actual installed package versions (see "Deviations" for why these differ
  from the plan's pins): `PySide6==6.11.2`, `PySide6_Essentials==6.11.2`,
  `PySide6_Addons==6.11.2`, `shiboken6==6.11.2`, `libclang==18.1.1`,
  `pyinstaller==6.10.0`, `pyinstaller-hooks-contrib==2026.7`.

## libclang shared-library collection outcome

**Worked with the naive `binaries=[...]` collection alone — the
`Config.set_library_file(...)` fallback was NOT needed.**

Task 2 Step 1's discovery command found the DLL exactly where the plan
guessed:

```
python -c "import clang, os; print(os.path.dirname(clang.__file__))"
# -> ...\.venv\Lib\site-packages\clang
```

with `native/libclang.dll` present under that directory (≈80.1 MB,
83,988,992 bytes) — no path correction was needed in `packaging.spec`. The
spec's `binaries=[(libclang_dll, ".")]` entry collected it successfully:
after `python -m PyInstaller packaging.spec --noconfirm`, `libclang.dll` was
present in the built bundle (see "Deviations" for exactly where — PyInstaller
6.x's newer onedir layout put it one level deeper than the plan's example
output assumed). Running the frozen exe reproduced the same
"libclang parsed OK, found: ['main']" behavior as the unbundled script (see
"Deviations" for how this was verified), so `app.py`'s
`clang.cindex.Config.set_library_file(...)` fallback described in the plan
was never exercised — `Index.create()` found the bundled DLL on its own.

## Measurements

Ran `powershell -File measure.ps1` three times back-to-back against the same
build for reproducibility. All three agree closely:

| Run | dist_size_mb | process_launch_wall_ms | in_process_cold_start_ms | closed_gracefully |
|-----|-------------:|------------------------:|---------------------------:|:---:|
| 1   | 194.2        | 1524.0                  | 171.9                      | true |
| 2   | 194.2        | 1519.5                  | 161.4                      | true |
| 3   | 194.2        | 1525.3                  | 151.5                      | true |

- **Dist size: 194.2 MB** (`dist/spike03_probe/`, onedir build — 1 exe +
  166 files under `_internal/`, dominated by Qt's Core/Gui/Widgets/Network
  DLLs and libclang's ~80 MB `libclang.dll`). Confirmed independently via
  `Get-ChildItem -Recurse | Measure-Object -Property Length -Sum`.
- **`process_launch_wall_ms` ≈ 1520-1525 ms.** Read this number for what it
  actually measures: `measure.ps1` starts the process, sleeps a fixed
  1500 ms, then stops the clock — so this number is mostly the fixed sleep
  plus a small, consistent ~20-25 ms of `Start-Process`/scheduling overhead,
  **not** a true "time until the window appeared" measurement. It does
  confirm the process starts, is scheduled, and is still alive/well-behaved
  well before the 1500 ms mark — it does not distinguish a 200 ms real
  launch from a 1400 ms one. Treat `in_process_cold_start_ms` as the
  meaningful number.
- **`in_process_cold_start_ms` ≈ 151-172 ms** (mean ≈ 162 ms across 3 runs).
  This is the app's own `time.perf_counter()` delta from `QApplication`
  construction to `window.show()` returning — i.e. genuine Qt/app
  initialization time, measured from inside the frozen process. It is
  essentially identical to the unbundled script's cold start (156-157 ms,
  measured during the Task 1 Step 3 sanity check), which makes sense: this
  metric excludes exe-load/DLL-extraction overhead (that overhead is real,
  it's just not what this particular in-process timer captures).

`measurements.json` itself is gitignored per the plan's file structure and
is not committed; the table above is transcribed directly from three
consecutive `Get-Content measurements.json` printouts, not estimated.

## Admin-privilege check

Confirmed non-elevated throughout:

```
Current user: ROCKY\sudul
Running elevated (Administrator): False
```

(`[Security.Principal.WindowsPrincipal]::IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)`
returned `False` in the same shell used for every build/run/measure step in
this spike — no re-run from a separate non-elevated shell was needed since
this one already wasn't elevated.)

The build itself is evidence for "no admin privileges to install or run":
`python -m PyInstaller packaging.spec` produces only
`dist/spike03_probe/` (one `.exe` + a `_internal/` folder of plain DLL and
data files, 194.2 MB total) inside the ordinary, user-writable project
directory. There is no installer, no registry write, no Windows service, no
driver, and no elevation prompt at any point in the build or in launching
`spike03_probe.exe` directly from that folder as the same non-elevated user.

## Deviations from the plan (what, and why)

1. **`PySide6==6.7.3` → `PySide6==6.11.2`.** PyPI reports `6.7.3` (and every
   `6.x` release through `6.8.0.1`) as `Requires-Python <3.13`; this machine
   runs Python 3.13.2, so `pip install -r requirements.txt` with the plan's
   original pin failed outright with "No matching distribution found."
   Bumped to the latest available release (`6.11.2`, `cp310-abi3` wheels —
   i.e. explicitly built to cover 3.10 through 3.13+). `libclang==18.1.1`
   and `pyinstaller==6.10.0` installed exactly as pinned, no changes needed.
   `requirements.txt` documents this inline.
2. **libclang.dll lands in `dist/spike03_probe/_internal/`, not flat in
   `dist/spike03_probe/`.** The plan's Task 2 Step 3 expected text
   (`ls dist/spike03_probe/ | grep -i libclang`) assumed an older PyInstaller
   onedir layout. PyInstaller 6.0+ collects onedir support files under a
   `_internal/` subdirectory to declutter the top-level dist folder
   (only the launcher `.exe` stays at the top level) — this is a
   PyInstaller-version behavior change, not a spec bug. Verified via
   recursive search: `dist/spike03_probe/_internal/libclang.dll` is present
   and is the correct file (matches the size found in Task 2 Step 1).
3. **`measure.ps1`: force-kill silently lost the frozen exe's stdout —
   fixed with a graceful-close-first approach.** The plan's original script
   unconditionally force-kills (`Stop-Process -Force`, i.e. `TerminateProcess`)
   after a fixed 1500 ms sleep. On this machine that reliably produced
   `in_process_cold_start_ms: null` on every attempt, even though the app
   was working correctly. Root cause, isolated experimentally: CPython
   fully buffers `stdout` when it is not attached to a real console (true
   for any redirected/piped stdout — reproduced identically on the
   *unbundled* `python.exe app.py` under the same `Start-Process
   -RedirectStandardOutput` redirection without `-u`/`PYTHONUNBUFFERED`),
   and `TerminateProcess` kills the process with no opportunity to flush
   that buffer. Confirmed this was a flush-timing issue and not an
   app/libclang failure by observing, while stdout was still empty:
   `MainWindowTitle = 'Spike 03 — Packaging Probe'` (exact match — the
   window was fully constructed, meaning `parse_trivial_c()` had already
   returned successfully) and `Responding = True` (pumping the Qt event
   loop normally, not hung or crashed) for 8+ seconds with zero stderr
   output. **Fix applied in `measure.ps1`:** request a graceful close via
   `$proc.CloseMainWindow()` (sends `WM_CLOSE`, letting the app's own
   `sys.exit()`/interpreter shutdown flush stdio normally) and wait up to
   5 s for exit, falling back to `Stop-Process -Force` only if that doesn't
   work; `PYTHONUNBUFFERED=1` is also set as defense-in-depth for the
   fallback path. All 3 measurement runs closed gracefully
   (`closed_gracefully: true`) and captured `COLD_START_MS` correctly. This
   is a real, reproducible finding about measuring frozen GUI apps this way,
   not a one-off flake — worth carrying into `WP-PKG-01` if this measurement
   approach is reused.
4. **Window content verified via process-level signals, not a visual
   screenshot.** This execution environment's command-running session and
   its interactively-visible desktop session are not the same — a
   screenshot taken immediately after confirming the app's window title via
   `Get-Process` showed an empty desktop with "no windows found"
   system-wide (not specific to this app), indicating a session boundary in
   this environment rather than anything wrong with the build. Process-kill
   by name (`spike03_probe.exe`) did find and terminate the running
   process/PID, confirming it genuinely existed. Verification therefore
   relies on: `MainWindowTitle` exactly matching the string set in
   `MainWindow.__init__`, `Responding = True` (event loop alive), zero
   stderr, and a stdout capture of `COLD_START_MS=...` after graceful
   shutdown — a combination that is only consistent with `parse_trivial_c()`
   (and therefore `Index.create()` + the libclang parse) having succeeded;
   any exception there would have prevented the window from ever being
   constructed/titled and would have produced a traceback on stderr instead.
5. **`.gitignore` additions beyond the plan's list:** `.venv/` (the
   dedicated virtual environment is a harness-level override on top of the
   plan, not part of its original file structure) and `stderr.tmp` (added
   because the `measure.ps1` fix above now redirects stderr too, for
   debuggability, alongside the plan's original `stdout.tmp` — both are
   removed at the end of a successful run regardless).
6. **Per explicit task overrides, not spike-plan deviations:** installed
   into a dedicated `spikes/spike-03-packaging/.venv` rather than the
   system Python (two sibling spikes install different package sets
   concurrently on this machine), and no commits were made / `spikes/README.md`
   was not touched — both left for separate, later steps outside this
   agent run.

## Honest limits of this spike

The pass criterion asks for a **clean Windows machine with no Python**.
This spike ran on the development machine that built it, which has Python,
git, and other developer tooling already installed. That setup can prove:
- the bundle **builds** and the frozen exe **runs without crashing**
- libclang's ctypes-loaded shared library is (or isn't) correctly collected
- size and an in-process cold-start number

It **cannot** prove:
- that the bundle has no missing-DLL dependency that happens to already be
  satisfied by something else installed on this machine (the classic false
  negative for "works on my machine" packaging claims)
- that Windows Defender / SmartScreen does not quarantine the unsigned exe
  on first run on a machine with default endpoint security — AV heuristics
  vary by machine, definitions update, and this machine's Defender history
  is not representative of a clean machine's

**What closes this gap:** copy `dist/spike03_probe/` to an actual clean
Windows VM (no Python installed) or a second, unrelated machine, run the
exe there, and note whether it launches and whether Defender/SmartScreen
raises anything. This is a manual step for whoever owns that VM — it is
not something this spike can complete unattended.

## Verdict

**`PASS (local build)`**

The bundle builds cleanly with `python -m PyInstaller packaging.spec`, the
frozen `spike03_probe.exe` runs standalone from `dist/spike03_probe/` with
libclang's shared library working via the naive `binaries=[...]` collection
(no `set_library_file` fallback needed), size and both cold-start numbers
were recorded from real, repeated measurements (194.2 MB;
process-launch-wall ≈ 1520-1525 ms, dominated by the script's fixed sleep;
in-process cold start ≈ 151-172 ms), and nothing in the build or run path
implicated administrative privileges. This verdict is explicitly a
**local-machine** result — see "Honest limits of this spike" above. It is
**not** a clean-machine PASS and must not be read as one; closing that gap
requires the manual clean-VM step described above, which is outside what
this spike (or any agentic coding session) can complete unattended.
