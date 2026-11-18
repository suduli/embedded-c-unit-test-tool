"""Tests for the WP-SEC-03 configuration-is-data boundary.

Verifies: TOOL-SEC-070.
"""

from __future__ import annotations

import pytest

from ectt.sec import ConfigurationIsNotDataError, validate_configuration_is_data


def test_data_only_document_passes_unchanged() -> None:
    """verifies: TOOL-SEC-070"""
    document = {
        "compiler": "gcc",
        "flags": ["-O2", "-Wall"],
        "levels": {"none": 0, "speed": 2},
        "ratio": 1.5,
        "strict": True,
        "absent": None,
    }
    assert validate_configuration_is_data(document) == document


def test_nested_lists_and_mappings_recursed() -> None:
    """verifies: TOOL-SEC-070"""
    document = {"build": {"units": [{"name": "a", "flags": ["-c"]}]}}
    assert validate_configuration_is_data(document) == document


def test_callable_value_is_rejected_with_key_path() -> None:
    """verifies: TOOL-SEC-070"""
    document = {"build": {"hook": lambda: None}}
    with pytest.raises(ConfigurationIsNotDataError) as excinfo:
        validate_configuration_is_data(document)
    assert "build.hook" in str(excinfo.value)
    assert "function" in str(excinfo.value)


def test_arbitrary_object_value_is_rejected() -> None:
    """verifies: TOOL-SEC-070"""
    document = {"build": {"units": [{"name": object()}]}}
    with pytest.raises(ConfigurationIsNotDataError) as excinfo:
        validate_configuration_is_data(document)
    assert "build.units[0].name" in str(excinfo.value)


def test_module_value_is_rejected() -> None:
    """verifies: TOOL-SEC-070"""
    import json

    document = {"helpers": json}
    with pytest.raises(ConfigurationIsNotDataError):
        validate_configuration_is_data(document)


def test_non_string_key_is_rejected() -> None:
    """verifies: TOOL-SEC-070"""
    document = {7: "seven"}
    with pytest.raises(ConfigurationIsNotDataError) as excinfo:
        validate_configuration_is_data(document)
    assert "non-string key" in str(excinfo.value)


def test_error_derives_from_security_base() -> None:
    """verifies: TOOL-SEC-070"""
    from ectt.core.fs import CoreError
    from ectt.sec import SecError

    assert issubclass(ConfigurationIsNotDataError, SecError)
    assert issubclass(SecError, CoreError)


def test_bool_is_data_not_callable_trap() -> None:
    """verifies: TOOL-SEC-070"""
    # bool is a data type; the validator must not confuse it with callables.
    assert validate_configuration_is_data({"flag": False}) == {"flag": False}
