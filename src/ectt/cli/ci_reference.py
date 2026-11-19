"""Reference CI pipeline configurations and artifact-cache contract (WP-CLI-04).

TOOL-CIC-050: reference pipeline configurations for GitHub Actions and
GitLab CI. TOOL-CIC-070: caching of ingestion and analysis artifacts across
CI runs. Both templates call the documented non-interactive CLI entry and
react to the stable exit codes of :mod:`ectt.cli.exit_codes`
(TOOL-CIC-030); both cache exactly :func:`cacheable_artifacts`.

The live-pipeline demonstration (method D) is release-time CI work; the
container image is WP-PKG-05 (INS-090).

Satisfies: TOOL-CIC-050, TOOL-CIC-070.
"""

from __future__ import annotations

__all__ = [
    "CACHE_KEY_SOURCE",
    "GITHUB_ACTIONS_PIPELINE",
    "GITLAB_CI_PIPELINE",
    "cacheable_artifacts",
]

#: The file whose digest keys the artifact cache: the compilation database
#: describes the inputs whose derived artifacts are cached (TOOL-CIC-070).
CACHE_KEY_SOURCE = "compile_commands.json"

#: Ingestion and analysis artifacts carried across CI runs, as path
#: patterns inside the project directory (TOOL-CIC-070). These are the
#: outputs of WP-ING-01 ingestion (normalised database + staleness data)
#: and WP-ANA-04 analysis models; they live inside the tool's output root,
#: never in user source.
def cacheable_artifacts() -> tuple[str, ...]:
    """Return the cacheable ingestion/analysis artifact path patterns."""
    return (
        ".ectt/output/ingestion/",
        ".ectt/output/analysis/",
    )


_GITHUB_STEPS = """\
name: ectt
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: pip install .
      - name: Cache ingestion and analysis artifacts
        uses: actions/cache@v4
        with:
          path: |
            .ectt/output/ingestion/
            .ectt/output/analysis/
          key: ectt-${{ runner.os }}-${{ hashFiles('compile_commands.json') }}
      - name: List catalogue operations
        run: python -m ectt.cli --list-commands
      - name: Verify
        # The verify operation is the release-time entry; the catalogue
        # publishes operations as their packages land (operation.cancel
        # exists today). --list-commands above is the current-build check.
        run: python -m ectt.cli verify --project .
        # exit codes (TOOL-CIC-030): 0 success, 10 test failure,
        # 11 coverage threshold failure, 1 tool error, 2 usage error
"""

_GITLAB_STEPS = """\
stages:
  - verify

ectt-verify:
  stage: verify
  image: python:3.11
  script:
    - pip install .
    - python -m ectt.cli --list-commands
    - python -m ectt.cli verify --project .
  cache:
    key:
      files:
        - compile_commands.json
    paths:
      - .ectt/output/ingestion/
      - .ectt/output/analysis/
  # exit codes (TOOL-CIC-030): 0 success, 10 test failure,
  # 11 coverage threshold failure, 1 tool error (fails the job), 2 usage error
"""

GITHUB_ACTIONS_PIPELINE = _GITHUB_STEPS
GITLAB_CI_PIPELINE = _GITLAB_STEPS
