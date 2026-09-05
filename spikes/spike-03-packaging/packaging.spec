# packaging.spec
# Built for: python -m PyInstaller packaging.spec
import os
import clang

block_cipher = None

clang_pkg_dir = os.path.dirname(clang.__file__)
# Confirmed by Task 2 Step 1 on this machine: the libclang PyPI wheel ships
# the shared library at native/libclang.dll — matches the plan's guess.
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
