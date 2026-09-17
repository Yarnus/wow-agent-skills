# Roadmap

## Goal

Deliver independently usable skills with small interfaces and deep implementations. Agents compose results according to the user's goal instead of following a prescribed coaching workflow.

This document describes the first-release target, not a claim that all listed behavior is implemented. The first release is limited to the three core skills below. Future capabilities are options, not commitments.

## Implemented slice

`skills/wcl-data/` currently owns a standalone Python command for completed raid Boss Attempt/participant discovery and participant death windows. Authentication, upstream queries, pagination, and Revision checks live in its single script; tests exercise the command interface with synthetic HTTP responses. No shared runtime or coaching workflow is required.

The slice distinguishes window completeness from display truncation and whole-attempt coverage. It has no persistent cache, export, statistics, resume, or automatic retry support. Authorized live testing passed OAuth, Report Index discovery (two attempts), and a fight-2 death window (687 participant events, three displayed, explicit pagination termination, unchanged Revision). A later authorized Heroic Ula'tek check passed 42-page retrieval; see [live composition evidence](mechanics-live-verification.md). Regressions cover the special Environment actor `-1`, flexible raid difficulty size lists, regional report URLs, and existing credential variable names. Because actor expressions did not reliably match returned Report-local IDs, retrieval filters deaths by type upstream and actors locally; window retrieval includes all actors only within the requested time range and discloses that coverage. Review follow-up rejects malformed event actor/NPC identities and verifies that the selected death appears in the complete window before publishing evidence; regression tests and the authorized live window check pass after these changes. See [wcl-data instructions](../skills/wcl-data/SKILL.md) for the executable contract and supported source scope.

### Localization slice

`skills/wow-localization/` now provides an independently installable batch zhCN Spell ID command. It retains original names/IDs, identifies actual data builds from Wago response filenames, distinguishes missing/ambiguous names, exposes build mismatches and upstream failures, and caches validated snapshots with explicit refresh/fallback behavior. No WCL imports or credentials are required. This module owns only name resolution; callers retain source evidence separately.

TDD command regressions, independent copied-skill execution, synthetic WCL Spell ID composition, and live Wago default/pinned-build queries and cache reuse pass. A later authorized Ula'tek participant-window check passed live name composition while preserving original evidence; report build remains unknown. Default upstream builds are not asserted to be current Retail releases; snapshot completeness has no authoritative row-count guarantee. See [usage and result semantics](../skills/wow-localization/SKILL.md) and [source/reuse/verification notes](localization-verification.md).

### Mechanics slice

`skills/wow-mechanics/` provides standalone offline snapshot queries for Retail Heroic Ula'tek, with three reviewed claims at build 12.1.0.69587. Facts, secondary/author strategies and inferred signals remain distinct. Patch-only or other-build applicability is unknown. Optional fixed-source rechecks disclose missing content, build mismatch, transport failure and unresolved snapshot changes; they do not automatically update knowledge. No full encounter coverage, generic source framework or mechanic-rule DSL was added.

Command-level TDD regressions, copied-skill execution and synthetic mechanics → WCL death-window → localization composition pass without rewriting evidence. Live Wago row/build verification and the cited Icy Veins strategy passage check pass. A later authorized Ula'tek check passed live three-skill composition and observed three candidate spell IDs; the fourth remains unverified. General full-raid event querying remains unavailable. See [live verification](mechanics-live-verification.md). See [mechanics source notes](mechanics-source-research.md) for terms, exact source coverage and limitations.

## First release

### 1. wcl-data

Scope:

- Discover a Report Index: Boss Attempts, participants, and relevant identities.
- Retrieve scoped events and supported statistics by Boss Attempt, participant, event type, and time range.
- Support complete event export when the task actually needs it, without making export a prerequisite for focused queries.
- Hide official WCL authentication, pagination, caching, rate-limit handling, and Report Revision consistency checks behind the interface.
- Return compact results and file references for large datasets.

Acceptance criteria:

- An agent can list Boss Attempts and inspect a participant's death window without downloading the whole encounter.
- Query-range completeness, display truncation, and whole-Boss-Attempt coverage are distinct and explicit.
- A Complete Bundle is declared only after explicit pagination termination and the applicable range, hash, and Report Revision checks pass.
- Evidence retains WCL Report, Report Revision, Boss Attempt, time basis, and ID namespaces.
- Partial retrieval or upstream failure cannot masquerade as a complete result.
- Credentials never appear in output or artifacts.
- Explicit user selectors such as "last wipe" can be resolved transparently; ambiguous requests can prompt for clarification.

### 2. wow-mechanics

Scope:

- Resolve encounter mechanics for an explicit game branch, patch or build context, and difficulty.
- Return sourced mechanic descriptions, handling strategies, observable event signals, and unsupported or uncertain aspects.
- Keep source-stated mechanics separate from strategies and inferred detection logic.
- Operate without a user's WCL Report.

Acceptance criteria:

- Each substantive mechanic claim has a source and applicability context.
- Unknown patch applicability and source conflicts are visible rather than silently resolved.
- The skill distinguishes mechanic knowledge from verified event-detection rules.
- The result is useful independently and can guide targeted `wcl-data` queries.

Open implementation questions:

- Verify access, terms, update behavior, and patch metadata for candidate sources before selecting adapters.
- Start with a bounded, explicitly documented encounter scope; do not claim universal coverage.

### 3. wow-localization

Scope:

- Start with batch Spell ID lookup, including aura Spell IDs, for zhCN names.
- Use build-aware game data such as Wago Tools `SpellName`; verify source availability before implementation.
- Return ID, original name when supplied, localized name, locale, build, source, and match status.
- Cache reusable mappings internally.

Acceptance criteria:

- The skill works independently, without WCL credentials or a Report Index.
- Known, missing, and ambiguous IDs have explicit results.
- Missing names preserve the supplied original name and ID without blocking other skills.
- WCL-local actor IDs, NPC IDs, and Spell IDs are never treated as interchangeable.
- Machine translations are never represented as official localized names.
- Build mismatches are disclosed.

## Shared engineering work

- Define only the shared result metadata actually needed for composition: identity, source, applicability, coverage, warnings, and file references where relevant.
- Decide packaging so each installed skill contains or can access its required implementation without depending on another skill being invoked first.
- Reuse reliable code from the existing repository only after reviewing dependencies and license obligations.
- Keep authentication, transport, and cache implementation in one maintained location.
- Add regression tests for pagination, Report Revision changes, partial retrieval, malformed upstream data, ID mismatches, and missing localization.
- Document minimal invocation examples once executable interfaces exist; do not publish imaginary commands.
- Keep skill instructions focused on capability, inputs, outputs, limitations, and optional composition examples.

## First-release end-to-end checks

1. Given a WCL Report, list Boss Attempts, select a requested one, and retrieve a participant's death window with honest coverage metadata.
2. Retrieve relevant encounter mechanics with source and difficulty context; use them to inform follow-up event queries without a fixed workflow.
3. Resolve the resulting Spell IDs to Chinese names; preserve original names and IDs for misses.
4. Run localization and mechanic lookup independently of WCL retrieval.
5. Produce a useful conversational answer without rankings, workflow initialization, or mandatory HTML rendering.

Live source checks depend on authorized access and existing privately configured credentials. Fixtures must contain no credentials or unauthorized private report data.

## Not required for the first release

- A coaching workflow state machine or timing ledger.
- Ranking Cohort, Encounter Benchmark, or mandatory Reference Sample counts.
- Structured advice enums as the only allowed answer format.
- Mandatory Profiles, report artifacts, or HTML delivery.
- A generic plugin framework or mechanic-rule DSL.
- WeakAura execution, universal encounter coverage, or unverified support for Classic, Mythic+, and private reports.

## Candidate later iterations

| Capability | Useful result | Trigger for implementation |
| --- | --- | --- |
| `wcl-rankings` | Ranking Candidates filtered by encounter, difficulty, specialization, and ranking context | Users repeatedly need comparison examples; candidates remain distinct from qualified Reference Samples |
| `wow-spec-guide` | Patch-aware, sourced specialization guidance | Reviews need rotation, resources, talents, or cooldown context beyond encounter mechanics |
| `combat-analysis` | Deterministic calculations over existing evidence, such as death chains, aura coverage, or cast intervals | The same calculations recur and merit a tested module |
| `wago-aura-inspect` | Static explanation of a supplied WeakAura's triggers, conditions, and referenced Spell IDs | Users ask what an aura detects; external Lua is parsed, never executed |
| `report-render` | Optional Markdown, HTML, or PDF delivery | Existing general-purpose rendering skills are insufficient |
| Expanded localization | Additional locales and validated encounter, map, and NPC name mappings | Reliable identity associations and build metadata are available |
| Broader content support | Explicit support for more encounters, game modes, or branches | Source coverage and regression tests justify each expansion |
| Cross-attempt comparison | Changes across explicitly selected Boss Attempts | Real reviews need trends without conflating Report Revisions or creating implicit player histories |

## Implementation order

1. Establish the minimal skill/result conventions while implementing `wcl-data` and its tests.
2. Implement independent batch Spell ID localization.
3. Implement a bounded, sourced mechanic lookup.
4. Exercise the three first-release compositions with real user tasks and document limitations.
5. Select later iterations based on observed gaps, not on a prebuilt orchestration architecture.
