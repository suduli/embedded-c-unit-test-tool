# Verification Analysis Note — WP-SEC-05 (Security Disclosure Process and Supported-Version Policy)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-SEC-05. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-SEC-080 (M, P2, I) — *The project shall document a security disclosure
process and a supported-version policy* — verification method I (inspection).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-SEC-080): the project documents a security disclosure
  process consisting of: a private reporting channel, the content expected in a
  report, an explicit acknowledgement commitment, and an explicit resolution
  commitment. The process text is present in this note (§The policy) and as
  structured, inspectable data in `ectt.sec.policy`.
- AC-2 (falsifiable): the project documents a supported-version policy stating
  which release lines receive security fixes. The policy is expressed as a rule
  tied to the release state (pre-1.0: the latest release line only) rather than a
  list that goes stale, and states when the rule changes (at 1.0).
- AC-3 (falsifiable): the policy data is frozen, timestamp-free and deterministic —
  importing the module twice yields identical data — and its required fields are
  present and non-empty, verified by tests (inspection evidence).

**Owner action required (morning merge):** promote the policy text below to a
top-level `SECURITY.md` and link it from the README. `SECURITY.md` at the repo root
is outside this run's allowed paths; the structured data in `ectt.sec.policy` is the
in-scope carrier. The commitments below are first-authored tonight and are marked for
owner review; they bind the project only once the owner accepts them.

## The policy

### Disclosure process (owner-review draft)

1. **Reporting channel.** Report vulnerabilities privately via GitHub Security
   Advisories ("Report a vulnerability" on this repository) (owner's choice, 2026-11-27). Do not open a public issue
   for an unpatched vulnerability.
2. **Report content.** Include: affected version(s) or commit, a minimal reproduction
   (steps, inputs, configuration), the observed impact, and — if known — the
   affected component. Proof-of-concept code is welcome but not required.
3. **Acknowledgement.** Maintainers acknowledge a valid report within 5 business
   days of receipt.
4. **Resolution.** Maintainers provide either a fix or an explicit mitigation plan
   within 90 days of acknowledgement, and agree an advisory publication date with
   the reporter. Credit is given unless the reporter asks otherwise.

### Supported-version policy (owner-review draft)

- **While the tool is pre-1.0 (current state):** security fixes are released only
  for the latest release line. No older pre-release line receives security fixes;
  users on an older line must upgrade to the latest release to receive a fix.
- **From 1.0 onward:** this policy is replaced by the release policy the owner
  publishes at 1.0; until that policy exists, the pre-1.0 rule above applies and no
  document claims more.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-SEC-080** | The project shall document a security disclosure process and a supported-version policy. | `src/ectt/sec/policy.py` (`disclosure_policy`, `DisclosurePolicy`, channel/commitment/rule constants), re-exported by `src/ectt/sec/__init__.py`; the authoritative prose is §The policy of this note | **Guarantee (inspection):** the disclosure process is documented with all four required elements — a private reporting channel (GitHub Security Advisories, "no public issue for an unpatched vulnerability"), expected report content (four items), an acknowledgement commitment (5 business days) and a resolution commitment (90 days to a fix or a mitigation plan, agreed advisory date, reporter credit). The supported-version policy is documented as a rule tied to the release state (pre-1.0: latest release line only) with an explicit hand-over condition at 1.0 — a rule, not a list that goes stale.<br><br>**Machine-readable carrier:** `ectt.sec.policy` exposes the same policy as a frozen dataclass with deterministic `to_dict()`; the tests verify every required element is present, non-empty, frozen and identical across calls, and that the data carries an explicit `owner-review-draft` state marker.<br><br>**Honest limits:** the commitments are first-authored in this unattended run and are marked owner-review drafts; they bind the project only once the owner accepts them, and the note says so. A top-level `SECURITY.md` is outside this run's allowed paths — promoting the text there is a recorded shared-file change for the morning merge. No document claims more than the pre-1.0 rule.<br><br>**Test evidence:** `tests/sec/test_policy.py` — `test_policy_exposes_a_private_reporting_channel`, `test_policy_states_expected_report_content`, `test_policy_states_acknowledgement_and_resolution_commitments`, `test_policy_states_a_supported_version_rule`, `test_policy_data_is_frozen`, `test_policy_data_is_deterministic`, `test_policy_carries_an_explicit_state_marker`, `test_policy_type_is_frozen_dataclass` (8 tests, green in the WP-SEC-05 gate run: 498 passed, 4 skipped). |
