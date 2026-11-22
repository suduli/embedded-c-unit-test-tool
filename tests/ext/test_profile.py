# implements: TOOL-TGT-130
"""The versioned host profile and the run-preparation parity gate (A4).

Verifies: TOOL-TGT-130 — a versioned host profile records the target-to-host
derivation and its known ABI differences with unmeasured differences explicitly
unknown; every host-executed result is labelled with its profile; the parity
check gates run preparation with named reasons; host and target result sets
compare through the existing compare_outcomes. Nothing runs on hardware here.
"""

from __future__ import annotations

import json

import pytest

from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.ext import (
    ABI_DIMENSIONS,
    UNKNOWN_ABI,
    ExecutionConfig,
    ExecutionPlan,
    HostProfile,
    LabelledResults,
    ParityError,
    ParityGateError,
    ProfileError,
    ResultLabel,
    abi_difference,
    dump_host_profile,
    label_host_results,
    load_host_profile,
    prepare_host_proxy_run,
    record_host_profile,
)
from ectt.tcm import datacases as dd

PROFILE_ARGS: dict[str, object] = {
    "name": "linux-x86-proxy",
    "target_triple": "arm-none-eabi",
    "host_triple": "x86_64-linux-gnu",
    "flag_changes": ("-mfloat-abi=soft",),
    "define_changes": ("-DHW_SIM=1",),
    "substituted_headers": ("hw_map.h->hw_map_host.h",),
    "unavailable_hardware_behavior": "the access is diagnosed and the test fails",
    "abi": {"width": "int: 32 both", "endianness": "target little, host little"},
}

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")


def _profile(**overrides: object) -> HostProfile:
    return record_host_profile(**{**PROFILE_ARGS, **overrides})  # type: ignore[arg-type]


def _case(case_id: str, expected: str = "1") -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id=case_id,
            unit="src/a.c",
            function="f",
            inputs=dd.TestCaseInputs(),
            expected=dd.TestCaseExpected(return_value=expected),
            stubs=(),
        )
    )


def _result_set(outcomes: dict[str, str]) -> ResultSet:
    results = tuple(finalize_result(t, o, "d" * 64) for t, o in sorted(outcomes.items()))
    return ResultSet(run_id="run-1", execution=EXECUTION, results=results)


def _plans(generated: str = "GEN") -> tuple[ExecutionPlan, ExecutionPlan]:
    cases = (_case("tc.one"), _case("tc.two"))
    host = ExecutionPlan.build(cases, generated, ExecutionConfig("host", "gcc-14.2", "direct", "stdout"))
    target = ExecutionPlan.build(
        cases, generated, ExecutionConfig("target", "arm-none-eabi-gcc", "qemu", "semihosting", target_id="qemu-virt")
    )
    return host, target


# --- the profile record -----------------------------------------------------------------------


def test_the_profile_is_deterministic() -> None:
    """verifies: TOOL-TGT-130 — identical inputs give identical ids and dumps."""
    first, second = _profile(), _profile()
    assert first.profile_id == second.profile_id
    assert first.label == second.label
    assert dump_host_profile(first) == dump_host_profile(second)


def test_the_profile_round_trips_and_refuses_tampering() -> None:
    """verifies: TOOL-TGT-130 — the record is digest-bound like the suite record."""
    profile = _profile()
    loaded = load_host_profile(dump_host_profile(profile))
    assert loaded == profile
    tampered = json.loads(dump_host_profile(profile))
    tampered["abi"]["endianness"] = "tampered"
    with pytest.raises(ProfileError) as excinfo:
        load_host_profile(json.dumps(tampered))
    assert excinfo.value.reason == "digest_mismatch"


def test_unknown_abi_stays_unknown() -> None:
    """verifies: TOOL-TGT-130 — an unmeasured difference is never a guess."""
    profile = _profile()
    assert abi_difference(profile, "endianness") == ("target little, host little", True)
    assert abi_difference(profile, "alignment") == (UNKNOWN_ABI, False)
    assert abi_difference(profile, "signedness") == (UNKNOWN_ABI, False)
    for dimension in ABI_DIMENSIONS:
        _value, measured = abi_difference(profile, dimension)
        assert measured == (dimension in profile.abi)


def test_an_unmeasurable_abi_dimension_is_refused() -> None:
    """verifies: TOOL-TGT-130 — the profile cannot invent dimensions."""
    with pytest.raises(ProfileError) as excinfo:
        _profile(abi={"cache_line": "64"})
    assert excinfo.value.reason == "unknown_abi_dimension"


def test_a_profile_must_record_the_hardware_behavior() -> None:
    """verifies: TOOL-TGT-130 — unavailable hardware behavior is part of the record."""
    with pytest.raises(ProfileError) as excinfo:
        _profile(unavailable_hardware_behavior="  ")
    assert excinfo.value.reason == "missing_hardware_behavior"


def test_the_profile_label_is_a_single_token() -> None:
    """verifies: TOOL-TGT-130 — the label is deterministic and whitespace-free."""
    label = _profile().label
    assert " " not in label
    assert label.startswith("linux-x86-proxy@1#")


# --- labelling host results -------------------------------------------------------------------


def test_every_host_result_carries_its_profile_label() -> None:
    """verifies: TOOL-TGT-130 — labels ride beside every host-executed result."""
    profile = _profile()
    result_set = _result_set({"tc.one": "pass", "tc.two": "error"})
    labelled = label_host_results(profile, result_set)
    assert isinstance(labelled, LabelledResults)
    assert labelled.result_set is result_set
    assert [label.test_id for label in labelled.labels] == ["tc.one", "tc.two"]
    assert all(label.profile_id == profile.profile_id for label in labelled.labels)
    assert all(label.profile_label == profile.label for label in labelled.labels)
    assert all(isinstance(label, ResultLabel) for label in labelled.labels)


def test_a_tampered_profile_cannot_label_results() -> None:
    """verifies: TOOL-TGT-130 — results are only labelled by an intact profile."""
    profile = _profile()
    tampered = HostProfile(
        **{**PROFILE_ARGS, "abi": {"width": "edited"}, "profile_id": profile.profile_id}  # type: ignore[arg-type]
    )
    with pytest.raises(ProfileError) as excinfo:
        label_host_results(tampered, _result_set({"tc.one": "pass"}))
    assert excinfo.value.reason == "digest_mismatch"


# --- the run-preparation gate -----------------------------------------------------------------


def test_a_matched_pair_prepares_with_its_report() -> None:
    """verifies: TOOL-TGT-130 — parity passes into the preparation, config may differ."""
    profile = _profile()
    host, target = _plans()
    prepared = prepare_host_proxy_run(profile, host, target)
    assert prepared.parity.ok is True
    assert prepared.profile is profile
    assert prepared.parity.config_differences != ()  # the toolchains legitimately differ


def test_the_parity_gate_blocks_a_run_with_a_named_reason() -> None:
    """verifies: TOOL-TGT-130 — a diverging case refuses the run by name."""
    profile = _profile()
    host, _ = _plans()
    diverging = ExecutionPlan.build(
        (_case("tc.one"), _case("tc.two", expected="2")),  # tc.two's content differs
        "GEN",
        ExecutionConfig("target", "arm-none-eabi-gcc", "qemu", "semihosting", target_id="qemu-virt"),
    )
    with pytest.raises(ParityGateError) as excinfo:
        prepare_host_proxy_run(profile, host, diverging)
    assert excinfo.value.reasons == ("case_content_differs",)
    assert excinfo.value.reason == "parity_gate_refused"


def test_a_missing_case_refuses_the_run_by_name() -> None:
    """verifies: TOOL-TGT-130 — the gate names a case that would not run on target."""
    profile = _profile()
    host, _ = _plans()
    shorter = ExecutionPlan.build(
        (_case("tc.one"),),
        "GEN",
        ExecutionConfig("target", "arm-none-eabi-gcc", "qemu", "semihosting", target_id="qemu-virt"),
    )
    with pytest.raises(ParityGateError) as excinfo:
        prepare_host_proxy_run(profile, host, shorter)
    assert excinfo.value.reasons == ("case_only_on_host",)


def test_a_tampered_governing_profile_refuses_the_run() -> None:
    """verifies: TOOL-TGT-130 — the gate refuses before parity is even checked."""
    profile = _profile()
    host, target = _plans()
    tampered = HostProfile(
        **{**PROFILE_ARGS, "flag_changes": (), "profile_id": profile.profile_id}  # type: ignore[arg-type]
    )
    with pytest.raises(ProfileError) as excinfo:
        prepare_host_proxy_run(tampered, host, target)
    assert excinfo.value.reason == "digest_mismatch"


def test_the_gate_compares_a_host_plan_with_a_target_plan() -> None:
    """verifies: parity discipline — wrong kinds are refused with the named error."""
    profile = _profile()
    host, _ = _plans()
    with pytest.raises(ParityError) as excinfo:
        prepare_host_proxy_run(profile, host, host)
    assert excinfo.value.reason == "wrong_kind"
