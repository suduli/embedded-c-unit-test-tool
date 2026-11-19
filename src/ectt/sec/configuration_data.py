"""Configuration-is-data enforcement (WP-SEC-03).

Configuration is data, not script: every configuration document that reaches
the tool must contain only data values. This module is the boundary check —
it recurses through mappings and lists and refuses anything that is not a
data type, reporting the offending key path, so code embedded in a
configuration cannot reach execution.

Satisfies: TOOL-SEC-070.
"""

from __future__ import annotations

from typing import Any

from ectt.sec.errors import SecError

__all__ = [
    "ConfigurationIsNotDataError",
    "validate_configuration_is_data",
]

_DATA_TYPES = (str, int, float, bool, type(None))


class ConfigurationIsNotDataError(SecError):
    """Raised when a configuration document embeds non-data (executable) content."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "configuration_is_not_data",
        path: str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


def _check(value: Any, key_path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ConfigurationIsNotDataError(
                    f"configuration key {key_path!r} has a non-string key "
                    f"({type(key).__name__}); configuration keys must be strings",
                )
            _check(item, f"{key_path}.{key}" if key_path else key)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check(item, f"{key_path}[{index}]")
        return
    if not isinstance(value, _DATA_TYPES):
        raise ConfigurationIsNotDataError(
            f"configuration value at '{key_path}' has non-data type "
            f"{type(value).__name__}; configuration is data, not script"
        )


def validate_configuration_is_data(document: Any) -> Any:
    """Validate that the document contains only data values; return it unchanged.

    A configuration holding a callable, module, or arbitrary object is refused
    with :class:`ConfigurationIsNotDataError` naming the offending key path,
    before the configuration can be used.
    """
    _check(document, "")
    return document
