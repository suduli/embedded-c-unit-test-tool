<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Security Policy (for the repository root SECURITY.md)

> **Status: owner-review draft** (WP-SEC-05, TOOL-SEC-080). This page is a
> proposal: the owner copies it to the repository root as `SECURITY.md` after
> reviewing the commitments — they bind the project only once the owner accepts
> them. The reporting channel is GitHub private
> vulnerability reporting (owner's choice, 2026-11-27); no email address is
> published. Switch it on in the repository settings before promoting this page.

## Reporting a vulnerability

Report vulnerabilities **privately** — via GitHub Security Advisories
("Report a vulnerability" on this repository's Security tab). Do **not** open a public issue for an unpatched
vulnerability.

Please include:

- affected version(s) or commit;
- a minimal reproduction (steps, inputs, configuration);
- the observed impact;
- the affected component, if known.

Proof-of-concept code is welcome but not required.

## What we commit to

- **Acknowledgement:** a valid report is acknowledged within **5 business
  days** of receipt.
- **Resolution:** a fix or an explicit mitigation plan is provided within
  **90 days** of acknowledgement, and an advisory publication date is agreed
  with the reporter. Credit is given unless the reporter asks otherwise.

## Supported versions

While the tool is **pre-1.0** (the current state), security fixes are released
only for the **latest release line**. Older pre-release lines receive no
security fixes; users on an older line must upgrade to the latest release to
receive a fix.

From 1.0 onward this rule is replaced by the release policy the owner
publishes at 1.0; until then the pre-1.0 rule above applies and no document
claims more.

## Scope notes specific to ectt

- The tool never sends telemetry and performs no network I/O from product code
  (SDD-002; verified by tests). A report about outbound connections from the
  tool itself would be a high-severity defect by construction.
- Untrusted project data is guarded: source content is never echoed into
  diagnostics, and untrusted projects require an explicit trust decision
  (see `docs/user/options/trust-record.md`).
- Generated C is data produced for *your* build; compiling it runs your
  toolchain. Reports about what a generated harness does under compilation are
  in scope; reports about the C code you write against the tool are yours.

---

Machine-readable carrier: `ectt.sec.policy.disclosure_policy()` (version
`1`, state `owner-review-draft`) — the commitments above are the same data,
and a test keeps the two consistent.
