"""Regenerate docs/reference/interchange-format.md from ectt.mig.

The published reference is generated, never hand-edited: run this script and
commit the result. tests/mig/test_reference_doc.py fails when the shipped
document drifts from :func:`ectt.mig.formats.render_format_reference`.
"""

from __future__ import annotations

from pathlib import Path

from ectt.mig.formats import render_format_reference


def main() -> None:
    target = Path(__file__).with_name("interchange-format.md")
    target.write_text(render_format_reference(), encoding="utf-8", newline="\n")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
