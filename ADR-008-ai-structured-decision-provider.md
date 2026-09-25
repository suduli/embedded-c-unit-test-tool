# ADR-008 — AI Provider for Structured Test-Decision Validation

**Document ID:** ADR-008
**Status:** **Accepted, 2026-09-19** — default provider and modular contract recorded; provider behavior not yet independently exercised (see §7)
**Relates to:** SRS-001 §18 AIF (`TOOL-AIF-220` through `TOOL-AIF-260`), §25 PLG (`TOOL-PLG-080`), A-08, K-04

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
   produces a value the tool's own control flow branches on — which means the
   free-text path's usual shape (prompt an LLM, parse its text back into
   something code can use) is exactly the mismatch this role should avoid, not
   repeat.
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

TypeSafe AI's own introduction page (`docs.typesafe.ai/introduction`, retrieved
2026-09-19) was read before treating the request as more than a name. It
describes **Jev**, "TypeSafe's flagship model and the first System One model,"
built to evaluate typed questions against a state and return typed answers —
three primitives (**Choice**, **Score**, **Noul**, the last a 0–1 truth value),
each returning a value plus a probability/confidence, evaluated in parallel and
in isolation so that "adding questions barely changes the response time" and
"does not create context-rot." The vendor's own framing — "fast, structured
decisions" a program can "branch on, sort by, and route with," as opposed to
text generation coerced into structure — matches the shape of `TOOL-AIF-220`
closely enough that it is worth treating as a genuine architectural fit, not
just a name a stakeholder supplied. That match is a documentation claim,
however, not a result this project has reproduced; §7 states that limit
directly.

---

## 2. Decision

1. **A structured-decision provider role is separate from the generation
   provider role.** `TOOL-AIF-230` already requires this; this ADR adopts it as
   the shape of the AI subsystem going forward, not just a requirement text.
2. **TypeSafe AI (Jev) is the default provider profile for the
   structured-decision role**, used only when a user has explicitly enabled a
   remote provider per `TOOL-AIF-030`. This satisfies `TOOL-AIF-240`.
3. **The default is a configuration value, not a code dependency.** It is
   reached through the AI-provider extension point defined in `TOOL-PLG-080`,
   the same mechanism every AI-assisted capability uses — present ones
   (`TOOL-AIF-060`/`110`/`120`/`220`) and any added after this specification is
   baselined (`TOOL-AIF-260`). No feature code calls TypeSafe's or any other
   vendor's SDK directly.
4. **"Any type of AI model" is read literally, not just as "any vendor of the
   same kind."** The extension point does not assume every future provider
   returns a `(choice, probability, confidence)` triple the way Jev does; a
   provider adapter is responsible for mapping its own native output shape
   — free-text, embedding, classification label, ranked list, or something this
   project has no name for yet — onto the typed contract a calling feature
   expects. This is what makes the contract survive a model *type* it was not
   written against, which is the specific thing requested, not merely a second
   vendor of today's type.

---

## 3. Why Jev fits the validation role specifically

| Property needed by `TOOL-AIF-220` | Free-text LLM prompted for JSON | TypeSafe Jev (per vendor docs) |
|---|---|---|
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
remains reachable through the same `TOOL-PLG-080` contract and satisfies
`TOOL-AIF-250` like any other provider. Rejected as the default because it
reproduces the exact mismatch `TOOL-AIF-220` exists to avoid: text generated,
then parsed back into something code depends on. Reliability of that parse
degrades as more independent judgments are folded into one call, which is the
opposite of Jev's documented per-question isolation.

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
to make. Building the modular contract (`TOOL-PLG-080`) now costs the same
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

- `TOOL-AIF-220`–`260` and `TOOL-PLG-080` are satisfied by one adapter
  contract shared with the tool's other extension points (`TOOL-PLG-010`
  already lists compiler configurations, test-framework back-ends, target
  execution, and report formats as siblings), rather than a second, divergent
  extensibility mechanism built just for AI.
- TypeSafe AI ships as the out-of-box remote default for the validation role,
  giving typed answers without a parsing layer, for users who opt in.
- Local, self-hosted, or enterprise-operated substitution is a configuration
  change (`TOOL-AIF-250`), including for a provider or model type this project
  does not know about yet — that is the point of §2.4's literal reading of
  "any type."
- Every AI-assisted capability, current and future, becomes discoverable and
  addable the same way a new report format already is.

**Rejected — what is given up.**

- No commitment to TypeSafe AI beyond a swappable default. If its terms,
  availability, or behavior change unfavorably, the cost of leaving is the cost
  of changing one configuration value — that is the contract working as
  designed, not a gap in it.
- No qualification or certification claims attach to TypeSafe AI's output.
  `TOOL-AIF-100` continues to exclude every AI-generated or AI-adjudicated
  result from certification evidence, regardless of which provider produced
  it.
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
   The validation role is dropped; `TOOL-PLG-080` remains in place for the
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
| Jev's three primitives, parallel/isolated evaluation, and "no text generation, no parsing" positioning | **Verified as a documentation claim** — `docs.typesafe.ai/introduction`, read 2026-09-19 — not independently exercised |
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
| **Decision** | Structured-decision AI role, separate from generation; default provider TypeSafe AI (Jev), opt-in remote only; both roles — and any future AI role — integrate through one documented extension point (`TOOL-PLG-080`) |
| **Confidence** | **Medium** — architecture (modular contract) is high-confidence; the named default is a documentation-only claim, not yet independently verified |
| **Strongest evidence for** | Jev's typed, parallel, isolated-evaluation primitives match `TOOL-AIF-220`'s shape more directly than prompting a free-text model for JSON and parsing the result |
| **Strongest evidence against** | Vendor terms, data-retention behavior, and production reliability are unverified; local-provider parity for air-gapped users (A-08) is not yet demonstrated with a named candidate |
| **Discharges** | The open question of what backs `TOOL-AIF-220`, and how "any type of AI model" is architecturally honored rather than left as a slogan |
| **Feeds** | SDD-002 (interface contract for the AI-provider extension point), SDD-005 (if a specific local structured-decision model is later adopted as an OSS/vendored dependency) |
| **Requires** | Verification of TypeSafe AI's pricing, rate limits, and data-retention terms against `TOOL-AIF-030`/`040` before the default ships; a named local-provider candidate before `TOOL-AIF-020` can be demonstrated for this role, not just specified |
