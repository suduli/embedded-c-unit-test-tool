<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Installation

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

ectt is a Python package (requires Python >= 3.11). From a checkout of the
repository:

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"     # Windows path
#   or:  .venv/bin/python -m pip install -e ".[dev]"    # POSIX path
```

The `[dev]` extra installs the development/test tooling (pytest, ruff, mypy,
jsonschema). The package itself needs the `clang` Python binding, which loads
a native libclang shared library at runtime - the C front-end is the only
native dependency (SDD-001 S4.2). Coverage reading uses the documented GCC
`gcov --json-format` output; producing it needs a GCC toolchain with
`--coverage`, which ectt does not install for you.

Verify the installation:

```
ectt --help
ectt --list-commands
```

The command-line surface today is deliberately small: `ectt --list-commands`
lists the engine operations wired into the CLI catalogue (currently
`operation.cancel`). The full workflows are available as the Python API
described in the workflow pages. A complete command per workflow is
**not yet available**.

