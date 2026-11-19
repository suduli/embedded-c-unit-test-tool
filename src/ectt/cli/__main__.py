"""``python -m ectt.cli`` entry point (WP-CLI-01).

Kept outside ``pyproject.toml`` (shared file) so the night run needs no
packaging change: the module executes the catalogue-generated CLI and exits
with its code.
"""

from __future__ import annotations

import sys

from ectt.cli.dispatch import run

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
