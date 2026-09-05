# WP-SPIKE-03 — PyInstaller Distribution Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Adaptation note:** P0 validation spike. This one is fundamentally a measurement exercise (build, run, record numbers), not a TDD candidate — steps are structured as build/measure/record rather than test/implement cycles. **Read the "Honest limits of this spike" note under Task 3 before treating any result as a final verdict** — the executing environment is a developer machine, not a clean one, and that caps what "no admin, not quarantined" can actually mean here.

**Goal:** Prove that a PyInstaller-bundled PySide6 + libclang application builds successfully, has a defensible size and cold-start time, and does not obviously require administrative privileges to run — surfacing this now because `WP-PKG-01` (P2) and the whole distribution story in ADR-001 §2/§3 depend on it, and because ctypes-loaded native libraries like libclang are a known PyInstaller trouble spot that is much cheaper to find out about now than after `WP-GUI-01` exists.

**Architecture:** Reuse spike-02's PySide6 app, add a trivial libclang parse call so the bundle demonstrably includes both dependencies, write a PyInstaller spec that explicitly collects libclang's shared library (ctypes-loaded native libraries are invisible to PyInstaller's default import analysis), build with `--onedir`, and measure.

**Tech Stack:** Python 3.13, PySide6, `libclang` (PyPI), PyInstaller.

**Spec:** [`PLAN-001-specification-analysis-and-work-breakdown.md`](../../../PLAN-001-specification-analysis-and-work-breakdown.md) §4.4 (`WP-SPIKE-03` pass criterion), [`design/SDD-005-external-integration.md`](../../SDD-005-external-integration.md) §5.3, §9.1 (K-04/K-05 constraints), `TOOL-INS-030` (installation must not require a language runtime, package manager, or extra compiler)

## Global Constraints

- Pass criterion (PLAN-001 §4.4, verbatim): "PyInstaller-bundled PySide6 + libclang on a clean Windows machine with no Python. Installs and runs without administrative privileges, and is not quarantined by default endpoint security. Record size and cold-start time."
- K-05 (SDD-005 §2): no administrative privileges for install or run.
- K-04 (SDD-005 §2): must work air-gapped — the built bundle must not need network access to start.
- Do not commit build output (`dist/`, `build/`, `*.spec`'s generated warn/xref files) to the repository — these are large binaries and belong in `.gitignore`.

---

## File Structure

```
spikes/spike-03-packaging/
  README.md                     # what this spike tests, how to reproduce, honest limits
  requirements.txt              # PySide6, libclang, pyinstaller
  .gitignore                    # dist/, build/, *.spec's auto xref, __pycache__/
  app.py                        # thin wrapper: spike-02's window + one real libclang parse call
  packaging.spec                # the PyInstaller spec, with libclang's .dll explicitly collected
  measure.ps1                   # builds, measures size + cold start, writes measurements.json
  RESULTS.md                    # filled in after running — outcome record
```

---

### Task 1: App with a real libclang call, and scaffolding

**Files:**
- Create: `spikes/spike-03-packaging/app.py`
- Create: `spikes/spike-03-packaging/requirements.txt`
- Create: `spikes/spike-03-packaging/.gitignore`
- Create: `spikes/spike-03-packaging/README.md`

**Interfaces:**
- Produces: a runnable `app.py` that imports both `PySide6` and `clang.cindex`, and performs one real parse — this is what makes the eventual bundle a genuine test of "PySide6 + libclang together," not just PySide6 alone.

- [ ] **Step 1: Write `app.py`**

```python
# app.py
import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from clang.cindex import Index


def parse_trivial_c() -> str:
    """One real libclang parse, so the bundle demonstrably needs libclang
    at runtime — not just at import time."""
    index = Index.create()
    tu = index.parse("probe.c", args=["-std=c11"], unsaved_files=[("probe.c", "int main(void) { return 0; }")])
    functions = [c.spelling for c in tu.cursor.get_children() if c.spelling == "main"]
    return f"libclang parsed OK, found: {functions}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spike 03 — Packaging Probe")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("PySide6 + libclang, bundled by PyInstaller."))
        layout.addWidget(QLabel(parse_trivial_c()))
        self.setCentralWidget(central)
        self.resize(420, 120)


if __name__ == "__main__":
    t0 = time.perf_counter()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Print, don't just show — measure.ps1 greps stdout for this line to
    # get an in-process cold-start number independent of process-launch overhead.
    print(f"COLD_START_MS={(time.perf_counter() - t0) * 1000:.1f}")
    sys.exit(app.exec())
```

- [ ] **Step 2: `requirements.txt`, `.gitignore`, `README.md`**

```
# requirements.txt
PySide6==6.7.3
libclang==18.1.1
pyinstaller==6.10.0
```

```
# .gitignore
dist/
build/
*.spec.bak
__pycache__/
measurements.json
```

README.md: restate the pass criterion verbatim, note reproduction steps (`pip install -r requirements.txt`, then `pwsh measure.ps1`), and prominently link to the "Honest limits of this spike" section that Task 3 writes into RESULTS.md — don't let a reader mistake a local-machine PASS for a clean-machine PASS.

- [ ] **Step 3: Run it directly (unbundled) as a sanity check before involving PyInstaller at all**

Run: `pip install -r requirements.txt && python app.py`
Expected: window opens showing "libclang parsed OK, found: ['main']"; `COLD_START_MS=...` printed to stdout. If this fails, fix it before Task 2 — PyInstaller can only ever make a working script's failure mode worse, never better.

- [ ] **Step 4: Commit**

```bash
git add spikes/spike-03-packaging/app.py spikes/spike-03-packaging/requirements.txt spikes/spike-03-packaging/.gitignore spikes/spike-03-packaging/README.md
git commit -m "spike-03: probe app exercising PySide6 and libclang together"
```

---

### Task 2: PyInstaller spec with explicit libclang collection

**Files:**
- Create: `spikes/spike-03-packaging/packaging.spec`

**Interfaces:**
- Consumes: `app.py` from Task 1.
- Produces: `dist/spike03_probe/` (onedir build) for Task 3 to measure.

- [ ] **Step 1: Locate libclang's shared library file** (needed because ctypes-loaded native libraries are invisible to PyInstaller's static import analysis and must be listed explicitly — this is the single most likely failure point in this whole spike, and finding out about it now is the point of the exercise)

Run:
```bash
python -c "import clang, os; print(os.path.dirname(clang.__file__))"
```
Expected: a path. List its contents (`ls` that directory, and its `native/` subdirectory if present) — the `libclang` PyPI wheel typically ships the shared library as `native/libclang.dll` on Windows. Record the exact relative path found; the spec below assumes `native/libclang.dll` but **must be corrected to match what is actually found** before proceeding.

- [ ] **Step 2: Write `packaging.spec`**

```python
# packaging.spec
# Built for: python -m PyInstaller packaging.spec
import os
import clang

block_cipher = None

clang_pkg_dir = os.path.dirname(clang.__file__)
# NOTE: confirm this matches what Task 2 Step 1 actually found before running.
libclang_dll = os.path.join(clang_pkg_dir, "native", "libclang.dll")

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[(libclang_dll, ".")] if os.path.exists(libclang_dll) else [],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="spike03_probe",
    debug=False,
    strip=False,
    upx=False,  # UPX-compressed executables are more likely to trip AV heuristics — leave off for this spike
    console=True,  # keep the console so COLD_START_MS is visible; drop for the real GUI app later
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name="spike03_probe",
)
```

- [ ] **Step 3: Build and confirm the libclang DLL actually landed in the bundle**

Run:
```bash
python -m PyInstaller packaging.spec --noconfirm
ls dist/spike03_probe/ | grep -i libclang
```
Expected: `libclang.dll` (or whatever the exact filename found in Step 1 was) present in `dist/spike03_probe/`. If it's missing, the `binaries=[...]` entry in the spec did not match the real file location — fix the path from Step 1's actual output, not by guessing.

- [ ] **Step 4: Run the bundled exe directly and confirm it behaves like the unbundled script**

Run: `./dist/spike03_probe/spike03_probe.exe`
Expected: same window, same "libclang parsed OK" message, same `COLD_START_MS=...` line (in the console, since `console=True`). This is the load-bearing check: if libclang's `Config` can't find its shared library when frozen, `Index.create()` raises `LibclangError` here — a real, likely-first-try failure worth expecting rather than being surprised by. If it fails: set `clang.cindex.Config.set_library_file(...)` explicitly in `app.py` before creating the `Index`, resolving the path via `sys._MEIPASS` when frozen (`getattr(sys, "_MEIPASS", clang_pkg_dir)`), and rebuild.

- [ ] **Step 5: Commit**

```bash
git add spikes/spike-03-packaging/packaging.spec
git commit -m "spike-03: PyInstaller spec with explicit libclang collection"
```

---

### Task 3: Measurement and verdict

**Files:**
- Create: `spikes/spike-03-packaging/measure.ps1`
- Create: `spikes/spike-03-packaging/RESULTS.md`
- Modify: `spikes/README.md`

**Interfaces:**
- Consumes: `dist/spike03_probe/` from Task 2.
- Produces: `measurements.json` (gitignored) feeding `RESULTS.md`.

- [ ] **Step 1: Write `measure.ps1`**

```powershell
# measure.ps1 — size and cold-start measurement for the bundled probe.
$ErrorActionPreference = "Stop"
$distDir = "dist/spike03_probe"
$exe = Join-Path $distDir "spike03_probe.exe"

if (-not (Test-Path $exe)) {
    throw "Build first: python -m PyInstaller packaging.spec --noconfirm"
}

$sizeBytes = (Get-ChildItem -Recurse $distDir | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($sizeBytes / 1MB, 1)

$launchStart = Get-Date
$proc = Start-Process -FilePath $exe -PassThru -RedirectStandardOutput "stdout.tmp"
Start-Sleep -Milliseconds 1500
$proc | Stop-Process -Force
$launchWallMs = ((Get-Date) - $launchStart).TotalMilliseconds

$stdout = Get-Content "stdout.tmp" -Raw -ErrorAction SilentlyContinue
$inProcessMs = $null
if ($stdout -match "COLD_START_MS=([\d.]+)") {
    $inProcessMs = [double]$Matches[1]
}
Remove-Item "stdout.tmp" -ErrorAction SilentlyContinue

$result = @{
    dist_size_mb = $sizeMB
    process_launch_wall_ms = [math]::Round($launchWallMs, 1)
    in_process_cold_start_ms = $inProcessMs
    measured_at_utc = (Get-Date).ToUniversalTime().ToString("o")
}
$result | ConvertTo-Json | Out-File -Encoding utf8 "measurements.json"
Get-Content "measurements.json"
```

- [ ] **Step 2: Run it**

Run: `pwsh -File measure.ps1` (or `powershell -File measure.ps1`)
Expected: prints JSON with `dist_size_mb`, `process_launch_wall_ms`, `in_process_cold_start_ms`. Record the actual numbers — do not estimate them.

- [ ] **Step 3: Check for an admin-privilege requirement**

Confirm, and record in RESULTS.md: the build produces only files under `dist/spike03_probe/` (a plain user-writable directory) with no installer, no registry write, and no driver — running `spike03_probe.exe` directly from that folder as the current (non-elevated) user is itself the evidence for "does not require administrative privileges." If the current shell happens to be elevated, re-run from a non-elevated shell to confirm; note which was used in RESULTS.md.

- [ ] **Step 4: Honest limits of this spike — write this into RESULTS.md verbatim, do not soften it**

```markdown
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
```

- [ ] **Step 5: Write the rest of `RESULTS.md`** — dist size, both timing numbers, the libclang-collection outcome (did Task 2 Step 4 need the `set_library_file` fallback, or did it work with `binaries=[...]` alone?), the admin-privilege check outcome, then the verdict:
  - `PASS (local build)` if the exe runs standalone with libclang working and no admin rights implicated — paired explicitly with the "Honest limits" section so nobody reads this as a clean-machine PASS.
  - `FAIL` only if the bundle cannot be made to run at all even on this machine (e.g. libclang never loads regardless of the `set_library_file` fallback) — that would be a real, load-bearing finding for `ADR-001 §2/§3` and `WP-PKG-01`.

- [ ] **Step 6: Update `spikes/README.md`'s row for spike-03.**

- [ ] **Step 7: Commit**

```bash
git add spikes/spike-03-packaging/measure.ps1 spikes/spike-03-packaging/RESULTS.md spikes/README.md
git commit -m "spike-03: measurements and packaging verdict"
```

---

## Self-Review

**Spec coverage:** "PyInstaller-bundled PySide6 + libclang": Task 1 (the app genuinely uses both) + Task 2 (the spec explicitly collects libclang's native library, the one part PyInstaller doesn't do automatically). "clean Windows machine with no Python" / "not quarantined": Task 3 Step 4 addresses this directly and honestly rather than papering over the gap — this is the one clause of the three spikes' pass criteria that cannot be fully closed inside an agentic coding session, and the plan says so instead of asserting a false PASS. "Installs and runs without administrative privileges": Task 3 Step 3. "Record size and cold-start time": Task 3 Steps 1-2.

**Placeholder scan:** No TBD/TODO. Task 2 Step 1's "must be corrected to match what is actually found" is a genuine data-dependent step (the exact wheel-internal path can vary by `libclang` release), not a placeholder — it says exactly how to find the real value and what to do with it.

**Type consistency:** `app.py` (Task 1) is consumed unmodified by `packaging.spec` (Task 2) — the `COLD_START_MS=` stdout contract Task 1 establishes is exactly what `measure.ps1` (Task 3) parses via regex. No mismatch.
