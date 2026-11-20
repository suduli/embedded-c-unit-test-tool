# implements: TOOL-PLG-050, TOOL-REP-090
"""Report format extension point (WP-REP-11).

The provider side of the ``report_formats`` extension point (``ectt.plg``,
contract ``report_format``, interface version 1): a report format is a pure
function from the documented intermediate report model
(``ectt.rep.model.ReportModel``) to rendered text.

Adding a format consumes the model only — the model already exists and is
persisted, so no test is re-executed (TOOL-PLG-050). The registry is a plain
named mapping with deterministic ordering; the built-in ``text`` and ``json``
formats delegate to the WP-REP-01 renderers.

Satisfies: TOOL-PLG-050, TOOL-REP-090.
"""

from __future__ import annotations

from collections.abc import Callable

from ectt.plg.points import CONTRACT_REPORT_FORMAT
from ectt.rep.errors import ReportModelError
from ectt.rep.model import ReportModel
from ectt.rep.render import render_json, render_text

__all__ = [
    "REPORT_FORMAT_CONTRACT",
    "REPORT_FORMATS_POINT_ID",
    "ReportFormatRegistry",
    "default_format_registry",
]

#: The plg contract this registry implements providers for.
REPORT_FORMAT_CONTRACT = CONTRACT_REPORT_FORMAT

#: The ``ectt.plg`` extension point id the descriptors use.
REPORT_FORMATS_POINT_ID = "report_formats"

FormatRenderer = Callable[[ReportModel], str]


class ReportFormatRegistry:
    """Named registry of report formats over the intermediate model."""

    def __init__(self) -> None:
        self._formats: dict[str, FormatRenderer] = {}

    def register(self, name: str, renderer: FormatRenderer) -> None:
        """Validate and register a format; reject a reused name."""
        if not isinstance(name, str) or not name or any(char.isspace() for char in name):
            raise ReportModelError(
                f"report format name must be a non-empty string without whitespace, got {name!r}",
                reason="invalid_format_name",
            )
        if not callable(renderer):
            raise ReportModelError(
                f"report format '{name}' must be a callable taking the report model",
                reason="invalid_provider",
            )
        if name in self._formats:
            raise ReportModelError(f"report format '{name}' is already registered", reason="duplicate_format")
        self._formats[name] = renderer

    def names(self) -> tuple[str, ...]:
        """All registered format names, ordered deterministically."""
        return tuple(sorted(self._formats))

    def render(self, model: ReportModel, name: str) -> str:
        """Render the model with the named format."""
        renderer = self._formats.get(name)
        if renderer is None:
            raise ReportModelError(
                f"no report format is registered under '{name}' (available: {', '.join(self.names())})",
                reason="unknown_format",
            )
        return renderer(model)


def default_format_registry() -> ReportFormatRegistry:
    """A fresh registry with the built-in ``json`` and ``text`` formats.

    A new instance is returned on every call so callers cannot mutate shared
    module state.
    """
    registry = ReportFormatRegistry()
    registry.register("json", render_json)
    registry.register("text", render_text)
    return registry
