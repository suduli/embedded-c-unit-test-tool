# implements: DSN-CORE-010, DSN-CORE-060
"""Integration test for byte-identical reproducibility across differing environments.

Verifies: TOOL-NFR-060, TOOL-NFR-070, TOOL-NFR-080, TOOL-PRJ-050, TOOL-PRJ-080.
Exit criterion: PLAN-001 §5.4 row for WP-CORE-01.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


def _build_fixture_c_tree(source_dir: Path) -> dict[str, tuple[int, str]]:
    """Populate a fixture C source tree and return a snapshot of (mtime_ns, sha256)."""
    source_dir.mkdir(parents=True, exist_ok=True)

    header_content = (
        "#ifndef ADC_H\n"
        "#define ADC_H\n"
        "\n"
        "#include <stdint.h>\n"
        "#include \"config.h\"\n"
        "\n"
        "uint16_t adc_read_channel(uint8_t channel);\n"
        "void adc_calibrate(float reference_voltage);\n"
        "int adc_self_test(void);\n"
        "\n"
        "#endif /* ADC_H */\n"
    )
    (source_dir / "adc.h").write_text(header_content, encoding="utf-8")

    source_content = (
        "#include \"adc.h\"\n"
        "\n"
        "uint16_t adc_read_channel(uint8_t channel) {\n"
        "    return (uint16_t)(channel * 100);\n"
        "}\n"
        "\n"
        "void adc_calibrate(float reference_voltage) {\n"
        "    /* calibration routine */\n"
        "}\n"
        "\n"
        "int adc_self_test(void) {\n"
        "    return 0;\n"
        "}\n"
    )
    (source_dir / "adc.c").write_text(source_content, encoding="utf-8")

    config_content = (
        "#ifndef CONFIG_H\n"
        "#define CONFIG_H\n"
        "\n"
        "#define ADC_MAX_CHANNELS 8\n"
        "\n"
        "#endif\n"
    )
    (source_dir / "config.h").write_text(config_content, encoding="utf-8")

    snapshot: dict[str, tuple[int, str]] = {}
    for path in sorted(source_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(source_dir).as_posix()
            mtime = path.stat().st_mtime_ns
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[rel] = (mtime, digest)
    return snapshot


def _manifest(directory: Path) -> dict[str, str]:
    """Calculate relative path to SHA-256 manifest of a directory."""
    manifest_map: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rel = path.relative_to(directory).as_posix()
            manifest_map[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest_map


def test_byte_identical_across_differing_subprocesses(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-060, TOOL-NFR-070, TOOL-NFR-080, TOOL-PRJ-050, TOOL-PRJ-080, DSN-CORE-010, DSN-CORE-060

    Runs the fixture pipeline twice in separate subprocesses that differ in:
    - PYTHONHASHSEED (0 vs 47291)
    - cwd (two different working directories)
    - absolute output-root path (two different output trees)
    - TZ (UTC vs America/New_York)
    - locale env vars (C vs en_US.UTF-8)

    Asserts:
    1. Both output trees are 100% byte-identical across all generated artifacts.
    2. No user source file's mtime_ns or sha256 changes across the run.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src_pythonpath = str(repo_root / "src")

    fixture_src = tmp_path / "source_tree"
    source_snapshot_before = _build_fixture_c_tree(fixture_src)

    pipeline_script = str(repo_root / "tests" / "core" / "fixture_pipeline.py")
    python_path_env = f"{src_pythonpath}{os.pathsep}{repo_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"

    # Machine 1 setup
    cwd1 = tmp_path / "cwd_machine_1"
    cwd1.mkdir()
    out1 = tmp_path / "machine_1_out" / "build" / "ectt"

    env1 = os.environ.copy()
    env1["PYTHONHASHSEED"] = "0"
    env1["TZ"] = "UTC"
    env1["LC_ALL"] = "C"
    env1["LANG"] = "C"
    env1["PYTHONPATH"] = python_path_env

    cmd1 = [
        sys.executable,
        pipeline_script,
        "--source-dir",
        str(fixture_src),
        "--output-dir",
        str(out1),
    ]

    res1 = subprocess.run(
        cmd1,
        cwd=str(cwd1),
        env=env1,
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 0, f"Machine 1 failed: {res1.stderr}"

    # Machine 2 setup: deliberately different seeds, paths, cwd, TZ, locales
    cwd2 = tmp_path / "cwd_machine_2"
    cwd2.mkdir()
    out2 = tmp_path / "deeply" / "different" / "output_root" / "ectt"

    env2 = os.environ.copy()
    env2["PYTHONHASHSEED"] = "47291"
    env2["TZ"] = "America/New_York"
    env2["LC_ALL"] = "en_US.UTF-8"
    env2["LANG"] = "en_US.UTF-8"
    env2["PYTHONPATH"] = python_path_env

    cmd2 = [
        sys.executable,
        pipeline_script,
        "--source-dir",
        str(fixture_src),
        "--output-dir",
        str(out2),
    ]

    res2 = subprocess.run(
        cmd2,
        cwd=str(cwd2),
        env=env2,
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0, f"Machine 2 failed: {res2.stderr}"

    # 1. Assert both output trees are byte-identical
    manifest1 = _manifest(out1)
    manifest2 = _manifest(out2)

    assert len(manifest1) > 0, "No files generated in output tree 1"
    assert manifest1 == manifest2, f"Manifest mismatch:\nOut1: {manifest1}\nOut2: {manifest2}"

    # Byte-by-byte direct verification
    for rel_path, digest1 in manifest1.items():
        f1 = out1 / rel_path
        f2 = out2 / rel_path
        bytes1 = f1.read_bytes()
        bytes2 = f2.read_bytes()
        assert bytes1 == bytes2, f"Byte divergence in artifact: {rel_path}"

    # 2. Source immutability verification: assert every file in source tree is untouched
    for rel_path, (before_mtime, before_digest) in source_snapshot_before.items():
        curr_file = fixture_src / rel_path
        after_mtime = curr_file.stat().st_mtime_ns
        after_digest = hashlib.sha256(curr_file.read_bytes()).hexdigest()

        assert before_digest == after_digest, f"Source file content was modified: {rel_path}"
        assert before_mtime == after_mtime, f"Source file mtime was touched: {rel_path}"
