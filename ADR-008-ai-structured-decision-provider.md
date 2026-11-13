# ADR-008 — AI Provider for Structured Test-Decision Validation

**Document ID:** ADR-008
**Status:** **Accepted, 2026-09-19** — default provider and modular contract recorded; provider behavior not yet independently exercised (see §7)
**Relates to:** SRS-001 §18 AIF (`TOOL-AIF-220` through `TOOL-AIF-260`), §25 PLG (`TOOL-PLG-100`), A-08, K-04

**Correction note, 2026-10-17:** DR-30–32 correct configurable evidence exclusion, mandatory boundary validation, optional confidence and adapter substitution cost. AI-provider extensibility is TOOL-PLG-100; TOOL-PLG-080 retains load-failure handling. The 2026-09-19 acceptance is historical; no integration/evaluation result or new approval is asserted.

---

<!-- nav:start -->
**Related documents** — [SRS-001](SRS-001-requirements.md) · [ADR-001](ADR-001-architecture-decisions.md) · [ADR-006](ADR-006-fork-or-build-fresh.md) · **ADR-008** *(you are here)* · [SDD-001](design/SDD-001-architecture.md) · [SDD-002](design/SDD-002-interfaces.md) · [SDD-003](design/SDD-003-data-model.md) · [SDD-004](design/SDD-004-traceability-architecture.md) · [SDD-005](design/SDD-005-external-integration.md) · [Register](design/trace/design-elements.yaml) · [Design index](design/README.md)

Architecture diagrams: [specifications](design/diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 1. Context

SRS-001 §18 (AI-Assisted Features) already carried a local-first, opt-in-remote
posture before this decision existed: AI is disabled by default (`TOOL-AIF-010`),
a locally-executed model must be supported (`TOOL-AIF-020`), nothing leaves the
machine without explicit per-session enablement (`TOOL-AIF-030`), and every
provider sits behind one abstraction (`TOOL-AIF-050`). A-08 states plainly that
users may be air-gapped; K-04 makes non-AI operation network-independent by
constraint, not by courtesy.

Two requests extended that section:

1. **`TOOL-AIF-220`** — a test-case *validation* capability: discrete typed
   decisions (pass/fail triage on ambiguous results, flaky-test flagging,
   review-priority triage of AI-generated artifacts already queued by
   `TOOL-AIF-090`) rather than the free-text *generation* the section already
   covered (`TOOL-AIF-060`/`110`/`120`). The two are different shapes of
   problem. Generation produces an artifact a human reviews. Validation
   produces typed advice usable for review routing only after adapter validation.
   The raw deterministic test result remains authoritative; AI advice cannot
   silently replace pass/fail, coverage measurements or evidence acceptance.
2. **A named default for that role** — TypeSafe AI's **Jev** model — and an
   explicit instruction that the door stay open for "supplementary local or
   enterprise-level models" later. A follow-up request generalized that
   instruction: the AI subsystem as a whole should be modular enough to accept
   **any type of AI model**, not only alternative structured-decision
   providers.

This ADR records both: which provider is the out-of-box default for the new
role, and the contract that keeps that default from becoming load-bearing
architecture.

### 1.1 What was checked before writing this

The [TypeSafe introduction](https://docs.typesafe.ai/introduction) was initially read on 2026-09-19 and rechecked on 2026-10-17. It documents Choice and Score results with probability/confidence fields, and Noul as a value in [0,1]; the Noul value is not itself a separate confidence estimate. It describes parallel, isolated evaluation of questions. These are vendor documentation claims, not measured behavior, calibration or task accuracy in this project. Typed output is a reason to evaluate the fit, not a substitute for the boundary validation in §3.1.

---

## 2. Decision

1. **A structured-decision provider role is separate from the generation
   provider role.** `TOOL-AIF-230` already requires this; this ADR adopts it as
   the shape of the AI subsystem going forward, not just a requirement text.
2. **TypeSafe AI (Jev) is the default provider profile for the
   structured-decision role**, used only when a user has explicitly enabled a
   remote provider per `TOOL-AIF-030`. This satisfies `TOOL-AIF-240`.
3. **The default is a configuration value, not a code dependency.** It is
   reached through the AI-provider extension point defined in `TOOL-PLG-100`,
   the same mechanism every AI-assisted capability uses — present ones
   (`TOOL-AIF-060`/`110`/`120`/`220`) and any added after this specification is
   baselined (`TOOL-AIF-260`). No feature code calls TypeSafe's or any other
   vendor's SDK directly.
4. **Extensibility covers differing model types through adapters and role capabilities.** An adapter maps native outputs into a supported typed feature contract and advertises compatible schema versions and capabilities. A generation-only or embedding provider does not automatically implement structured decisions. An unknown provider/model type requires adapter implementation, capability mapping, authorization review and evaluation before use. Selecting an installed, compatible, evaluated adapter can be a configuration change; adding support for a new type is engineering work.

---

## 3. Why Jev fits the validation role specifically

| Property needed by TOOL-AIF-220 | General-purpose model with structured output | TypeSafe Jev (vendor claims) |
|---|---|---|
| Typed output | Available through an adapter/schema; transport and schema validation remain required | Typed primitives reduce text extraction work; adapter validation remains required |
| Several independent questions | Cost/interference depends on provider and request design; evaluate on project fixtures | Vendor describes isolated parallel evaluation; project latency/accuracy not measured |
| Probability/confidence | Optional capability, with provider-specific semantics | Choice/Score expose these fields; Noul is a [0,1] value, not separate calibrated confidence |
| Auditability (AIF-160) | Record request, model, parameters and validated result | Same requirement; vendor typing creates no exemption |

This motivates a default profile, not exclusive support or demonstrated suitability. §7 retains the outstanding terms, local-candidate and behavioral evaluation gates.

### 3.1 Mandatory validation and advisory boundary

Every adapter, including a typed vendor SDK adapter, must validate the negotiated schema/version, role capability, required fields, expected choice membership, numeric range/finite values and declared probability/confidence semantics. Validate transport status and response correlation before producing a normalized result; do not branch on raw vendor values. A schema-valid response can still be wrong: project evaluation and human review remain required.

The normalized outcome is either `ok` with a validated typed value and provenance, `abstain` with a reason (including unsupported capability or a required confidence signal being absent), or an explicit `error` such as malformed output, unsupported schema, transport failure or timeout. Cancellation follows SDD-002 and never creates a fabricated decision. An absent optional confidence value remains absent, never zero or a guessed score. Feature policies state whether confidence is required and how any threshold was established.

Record provider/adapter/model versions, request and input identity, relevant parameters, authorization context, raw-response reference/hash and validation outcome under the central provenance contract. A valid result may route review priority or present advice; it must not overwrite the original deterministic test verdict, instrumentation data or coverage independence evidence. Invalid, abstaining, failed or cancelled results leave that evidence intact and available for human review.

Acceptance remains pending: independently exercise malformed/missing/out-of-range responses, unknown choices/versions, missing capabilities, absent confidence, transport failure, timeout/cancellation and two different adapters before claiming interchangeability or validation coverage.

---|---|---|
| Output the caller can branch on without a parse/validate step | No — text is generated, then parsed, then validated against a schema; malformed output is a real failure mode at this boundary | Yes, by the vendor's own description — typed values returned directly |
| Cost of asking several independent questions per decision | Grows with prompt size and is subject to context interference between questions | Documented as evaluated "in parallel and in isolation," with each addition described as not creating "context-rot" |
| A confidence/probability signal the tool can threshold on | Not native; would require a second call or a heuristic over token probabilities | Native to all three primitives |
| Auditability (`TOOL-AIF-160`) — record prompt, model, parameters | Same as any LLM call | Same requirement applies; TypeSafe does not exempt this project from logging what was asked and what was returned |

None of this is treated as a reason to make TypeSafe AI *mandatory*. It is the
reason it is the **default** — the profile a user gets without having to
research providers first — subject to §5's local-substitution requirement.

---

## 4. Alternatives rejected

**A. Reuse the existing generation provider (`TOOL-AIF-050`) for validation
too, prompting it for JSON output.**
Rejected as the *default*, not removed as an *option* — a general-purpose LLM
remains reachable through the same `TOOL-PLG-100` contract and satisfies
`TOOL-AIF-250` like any other provider. Its text-to-schema adaptation cost is a reason to evaluate the typed provider first, not proof that it is less accurate or reliable. Provider-specific structured-output support may reduce that cost. Neither alternative has been behaviorally compared here, and both require §3.1 validation.

**B. Classical ML or hand-written rule-based heuristics; no AI vendor at all.**
Rejected as the *only* path, kept as a first-class **local** provider under
`TOOL-AIF-020`/`TOOL-AIF-250`. It trivially satisfies air-gapped operation
(A-08), but it does not need to carry that case alone — a locally-hosted
structured-decision model behind the same contract does, and `TOOL-AIF-220` is
filed at *(S, P3)*, not a hard requirement that must degrade gracefully to
rules if AI is unavailable. `TOOL-AIF-010` already guarantees the tool's core
function needs neither.

**C. Defer `TOOL-AIF-220` past v1.0 rather than pick a default now.**
Rejected: the capability was already scoped at *(S, P3)* in SRS-001; deferring
the *requirement* is a product-scope decision this ADR does not have standing
to make. Building the modular contract (`TOOL-PLG-100`) now costs the same
whether it initially serves one AI role or several — deferring the default
does not defer that cost, it just leaves the role's provider unspecified.

**D. Hard-code TypeSafe AI as the only supported structured-decision
provider.**
Rejected outright. This is the one alternative genuinely incompatible with the
request, not merely a weaker option: it would violate `TOOL-AIF-020`'s
mandatory local-execution support, fail every A-08 air-gapped user
unconditionally, and reintroduce exactly the vendor lock-in the modularity
instruction was written to prevent.

---

## 5. Consequences

**Accepted.**

- `TOOL-AIF-220`–`260` and `TOOL-PLG-100` are designed to be served by one adapter
  contract shared with the tool's other extension points (`TOOL-PLG-010`
  already lists compiler configurations, test-framework back-ends, target
  execution, and report formats as siblings), rather than a second, divergent
  extensibility mechanism built just for AI.
- TypeSafe AI is the configured remote default profile for the validation role, activated only after opt-in and subject to the pre-shipping gates in §7. Typed values still require §3.1 validation.
- Selecting an already installed compatible adapter is configuration-only. A new local, self-hosted or enterprise provider needs an implemented adapter, capability/schema checks and evaluation; none is inferred from the phrase “any type.”
- AI-assisted capabilities use the shared extension mechanism with explicit role/version/capability discovery. Discoverability is a design obligation, not implemented proof.

### 5.1 Configurable certification-evidence mode

AIF-100 supplies a **configurable exclusion mode**, not a universal ban on all AI-associated outputs. In normal mode, labelled AI advice/artifacts may be retained with provenance. Enabling certification-evidence mode excludes AI-generated and AI-adjudicated artifacts, including evidence derived from either, from the certification-evidence selection/export path. The export records the selected mode and exclusions; if origin is unknown, that mode excludes the item until provenance is resolved.

Persist distinct origins for deterministic observations, AI-generated artifacts, AI adjudications and human-authored/reviewed records, with references to their inputs. Human review records author/outcome separately and does not erase AI origin. Preserve deterministic results separately from AI advice. An AI-adjudicated result remains AI-origin even when the underlying execution was deterministic; the original execution record remains available and is assessed independently.

The exclusion is enforced by evidence selection/export, not merely a UI label. Certification-evidence export selects the exclusion mode by default; other normal-mode exports explicitly record their mode and must not imply qualification. This policy requires the corresponding AIF-100 wording, data provenance and export validation. It does not certify any retained result or assert the implementation already enforces these rules.

**Rejected — what is given up.**

- No commitment to TypeSafe AI beyond a swappable default. Leaving for an installed compatible adapter can require only configuration; supporting an unknown replacement requires implementation and evaluation.
- No qualification or certification claim attaches to TypeSafe AI output. AIF-100 exclusion applies when its mode is enabled, with generated/adjudicated provenance and human review handled as in §5.1.

- A small amount of near-term design cost: the structured-decision role
  (`TOOL-AIF-230`) is a second AI-provider surface alongside generation
  (`TOOL-AIF-050`), each needing its own adapter contract even though both
  route through the same extension point.

---

## 6. What would reverse this

1. **If TypeSafe AI's documented behavior does not hold up under actual
   integration** — for example, if a "local" or low-latency claim turns out to
   require network access this project did not expect, or the parallel/
   isolated-evaluation claim does not hold at the question counts
   `TOOL-AIF-220`'s use cases need. This reopens the *default* only; §2's
   contract is unaffected because no feature code depends on Jev directly.
2. **If `TOOL-AIF-220` is deprioritized below P3/S before construction begins.**
   The validation role is dropped; `TOOL-PLG-100` remains in place for the
   generation role and for whatever AI-assisted capability is proposed next.
3. **If a locally-runnable structured-decision model reaches comparable fit**
   for a user base where A-08 (air-gapped operation) is the common case rather
   than the exception. The default named in `TOOL-AIF-240` moves to it; nothing
   else in this ADR changes.

---

## 7. Confidence, and what is not settled

**Confidence: Medium.** Lower than ADR-006's "High," and for a specific,
stated reason: the case for Jev's fit (§3) rests on the vendor's own
documentation, read once, on one date. No API call was made against it, no
evaluation harness was run, and no failure mode of the service itself —
latency under load, availability, drift in returned confidence calibration —
has been observed by this project. That is a materially weaker evidence base
than ADR-006's, which cross-checked claims against a public repository, its
commit history, and the GitHub API. Following the practice ADR-006 §9.2 set:

| Claim | Quality |
|---|---|
| Jev primitives, optional confidence fields and parallel/isolated positioning | **Verified only as vendor documentation claims** — [introduction](https://docs.typesafe.ai/introduction), read 2026-09-19 and rechecked 2026-10-17; no project behavioral evaluation |
| Fit for `TOOL-AIF-220`'s specific use cases (flaky-test flagging, review triage) | **Judgement**, drawn from the primitives' stated shape, not from a trial against this tool's actual test-result data |
| Pricing, rate limits, data-retention terms, and whether "state" submitted to Jev is retained | **Not checked.** Material to `TOOL-AIF-030`'s transmission-disclosure requirement and to `TOOL-AIF-040`; must be established before this default ships, not assumed from the introduction page |
| Availability of a locally-executable structured-decision model meeting `TOOL-AIF-020`/`250` today | **Not surveyed.** This ADR requires the *capability* to substitute one; it does not yet name a specific local candidate |

None of these gaps affect §2's decision to build a modular contract — that
holds regardless of which provider ends up behind it. They bound how much
weight the *specific default* (TypeSafe AI) should carry until the pricing/
retention/local-candidate gaps above are closed, which should happen before
`WP`-level implementation of `TOOL-AIF-220` begins.

---

## 8. Summary

| | |
|---|---|
| **Decision** | Structured-decision AI role, separate from generation; default provider TypeSafe AI (Jev), opt-in remote only; both roles — and any future AI role — integrate through one documented extension point (`TOOL-PLG-100`) |
| **Confidence** | **Medium** — architecture (modular contract) is high-confidence; the named default is a documentation-only claim, not yet independently verified |
| **Strongest evidence for** | Jev's typed, parallel, isolated-evaluation primitives motivate evaluating its fit for `TOOL-AIF-220`; all adapters still validate output and project accuracy remains unmeasured |
| **Strongest evidence against** | Vendor terms, data-retention behavior, and production reliability are unverified; local-provider parity for air-gapped users (A-08) is not yet demonstrated with a named candidate |
| **Discharges** | The open question of what backs `TOOL-AIF-220`, and how "any type of AI model" is architecturally honored rather than left as a slogan |
| **Feeds** | SDD-002 (interface contract for the AI-provider extension point), SDD-005 (if a specific local structured-decision model is later adopted as an OSS/vendored dependency) |
| **Requires** | Verification of TypeSafe AI's pricing, rate limits, and data-retention terms against `TOOL-AIF-030`/`040` before the default ships; a named local-provider candidate before `TOOL-AIF-020` can be demonstrated for this role, not just specified |
