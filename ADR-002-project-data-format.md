# ADR-002 — Project Data Storage Format

**Document ID:** ADR-002
**Status:** **Accepted, 2026-09-26** — restricted YAML format and single-adapter architecture decided
**Relates to:** SRS-001 §26 PRJ (`TOOL-PRJ-010`, `TOOL-PRJ-020`, `TOOL-PRJ-050`, `TOOL-PRJ-070`), §17 UIX (`TOOL-UIX-320`), §16 CIC (`TOOL-CIC-080`), §22 SEC (`TOOL-SEC-070`), SDD-001 §396, SDD-003 §2.1, §4, §5, §10, `DSN-PRJ-010`, `DSN-PRJ-030`, `DSN-PRJ-040`, `DSN-SEC-060`

---

<!-- nav:start -->
**Related documents** — [SRS-001](SRS-001-requirements.md) · [ADR-001](ADR-001-architecture-decisions.md) · **ADR-002** *(you are here)* · [ADR-006](ADR-006-fork-or-build-fresh.md) · [ADR-008](ADR-008-ai-structured-decision-provider.md) · [SDD-001](design/SDD-001-architecture.md) · [SDD-002](design/SDD-002-interfaces.md) · [SDD-003](design/SDD-003-data-model.md) · [SDD-004](design/SDD-004-traceability-architecture.md) · [SDD-005](design/SDD-005-external-integration.md) · [Register](design/trace/design-elements.yaml) · [Design index](design/README.md)

Architecture diagrams: [specifications](design/diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 1. Context

Test projects for safety-related embedded software have lifetimes measured in decades (SRS-001 §26). Verification suites authored today must remain readable, diffable, and executable long after the tool versions that authored them are retired. Furthermore, verification is a collaborative team discipline: concurrent edits by multiple engineers must produce localized, reviewable Git diffs and resolvable merge conflicts (TOOL-PRJ-050, TOOL-PRJ-060).

Open question 6 in SRS-001 §27 required choosing a concrete plain-text serialisation syntax. Standard serialization formats introduce severe hazards when applied to safety-critical embedded test data:

1. **Implicit typing hazards (SDD-003 §10):** General-purpose YAML parsers execute heuristic type coercion. In embedded C testing, where string identifiers, register masks, floating-point literals, and hardware pins are ubiquitous, implicit typing corrupts test data without warning.
2. **Untrusted project files as attack vectors (DSN-SEC-060, TOOL-SEC-070):** Projects retrieved from external repositories, branches, or shared drives are untrusted inputs. Formats supporting code execution, expressions, include directives, or deserialization tags create an arbitrary-code-execution surface before compilation even begins. Configuration must be data, not code.
3. **Diff instability and phantom churn:** Non-deterministic key ordering, unstable floating-point representations, platform-dependent line endings, and whitespace fluctuations generate massive phantom diffs that train human reviewers to skim changes.

### 1.1 Hazard Matrix

| Literal in C / Test Data | Standard YAML (Implicit Typing) | Restricted YAML (ADR-002) | Impact on Safety Evidence |
|---|---|---|---|
| `NO` (e.g. sensor state) | Boolean `false` | String `"NO"` | State corruption in test assertions |
| `1.10` (e.g. version tag) | Float `1.1` | String `"1.10"` | Silent numerical mutation / version mismatch |
| `010` (e.g. octal or pin) | Integer `8` | String `"010"` | Hardware pin or register mismatch |
| `0x1F` (register mask) | Integer `31` | String `"0x1F"` | Hex notation lost in diffs |
| `~` (e.g. bitwise flag) | `None` / `null` | String `"~"` | Assertion converted to null check |

---

## 2. Decision

1. **Adopt Restricted YAML as the project storage syntax.**
   - All scalar values are parsed strictly as strings with implicit type resolution disabled. Type conversion occurs solely at the schema/model layer.
   - On write, every scalar value is double-quoted (`"..."`). This structurally eliminates implicit typing hazards (`NO` -> false, `1.10` -> float, version strings -> numbers).
2. **Isolate syntax behind a single serialisation adapter (DSN-PRJ-010, SDD-001 §396).**
   - The core data model is completely format-agnostic. Surface syntax is confined to one adapter (`RestrictedYamlAdapter`).
   - A secondary adapter (e.g. JSON or binary) can be introduced in the future without modifying domain models or workflow engines.
3. **Deterministic emission rules (DSN-PRJ-030, SDD-003 §4).**
   - Keys are emitted in a defined canonical order with `schema_version` always first (TOOL-PRJ-020).
   - Default values are omitted on write, keeping files minimal and clean.
   - Output uses LF line endings (`\n`), no trailing whitespace, a single trailing newline, and UTF-8 encoding without BOM.
   - Floating-point numbers are formatted via `canonical_float_repr` and emitted as quoted strings.
   - Indentation is fixed at 2 spaces per nesting level. Semantically null load->save cycles are strictly byte-identical.

---

## 3. Security and Compliance Implications

Project files are treated as untrusted inputs (DSN-SEC-060). Configuration is data, not code (TOOL-SEC-070):
1. **No executable constructs:** The loader explicitly rejects expressions, includes, or hooks.
2. **Strict parser rejection:** The loader rejects the following constructs with a named error specifying the exact file and line number:
   - Anchors and aliases (`&anchor`, `*alias`) to prevent alias-expansion denial of service (Billion Laughs).
   - Merge keys (`<<`) which obscure data provenance and introduce parser ambiguities.
   - Explicit tags (`!!python/...`, `!custom`, `!!int`, `!!str`, etc.), eliminating arbitrary deserialization gadgets.
   - Duplicate mapping keys (which standard PyYAML silently overwrites).
   - Multi-document streams (files must contain exactly one document).
   - Non-string mapping keys (compound structures as keys are forbidden).

---

## 4. Alternatives Rejected

- **JSON:**
  *Rejected.* Standard JSON lacks native comments for human-authored documentation, creates heavy quote noise, causes merge conflicts over trailing commas on list additions, and poorly represents multiline strings (such as embedded C stub snippets).
- **TOML:**
  *Rejected.* TOML's table and array-of-tables syntax becomes unwieldy and unreadable when expressing deeply nested hierarchical test case trees, structured parameter mappings, and heterogeneous test vectors (TOOL-UIX-160).
- **Purpose-built custom DSL:**
  *Rejected.* A bespoke grammar requires building and maintaining dedicated parsers, language server protocol (LSP) servers, and editor syntax highlighters over decades, creating a long-term maintenance liability with zero ecosystem support.
- **Unrestricted YAML / ruamel round-trip:**
  *Rejected.* Unrestricted YAML suffers from severe typing hazards (the "Norway problem", float truncations, octal conversions) and critical security vulnerabilities via object tags. Relying on `ruamel.yaml` comment-preserving round-trips was rejected because comment preservation heuristics across complex edits are fragile, non-deterministic across versions, and fail to guarantee byte-level diff stability.

---

## 5. Consequences

**Accepted:**
- `TOOL-PRJ-010`, `TOOL-PRJ-020`, `TOOL-PRJ-050`, `TOOL-UIX-320`, and `TOOL-CIC-080` are fully satisfied.
- Test data is immune to silent scalar type corruption across all platforms and tool versions.
- Git diffs are minimal, stable, and readable.
- Arbitrary code execution via project files is structurally prevented.
- **Comment-loss rule:** Rationale and user documentation belong in explicit string fields (e.g. `description`), which reliably survive tool rewrites. While comments are tolerated on read, tool rewrites cannot preserve free-floating comments; overwriting an existing file that contains YAML comments will raise `CommentPreservationError` unless the caller explicitly passes `discard_comments=True`. No silent data loss occurs.

**Rejected — what is given up:**
- Free-form inline comments authored in external text editors are not preserved during automated tool updates unless explicitly discarded.
- Direct YAML shorthand features (anchors, references, custom tags) are completely disabled.

---

## 6. What Would Reverse This

1. If an international standard for safety-critical unit testing (e.g. ISO/IEC) mandates an alternate open schema format (such as an XML or JSON-LD dialect) as a condition of compliance.
2. If PyYAML tokenization introduces an unresolvable performance bottleneck on multi-gigabyte project trees that cannot be mitigated by caching or file sharding.
3. If an industry-standard, fully deterministic round-trip parser emerges that reliably preserves arbitrary comments across AST mutations with mathematical proofs of byte-stability.

---

## 7. Summary

ADR-002 establishes **Restricted YAML** as the storage format for all `ectt` project artifacts. Every scalar is double-quoted on write and loaded as a string without implicit typing. Surface syntax is encapsulated in a single adapter, protecting domain logic from format dependencies while enforcing strict security guards against code execution and diff churn.
