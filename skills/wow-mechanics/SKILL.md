---
name: wow-mechanics
description: Query sourced Heroic Ula'tek mechanics independently, or identify candidate event signals for a Warcraft Logs follow-up. Exposes build applicability, strategy attribution, and knowledge gaps.
---

# WoW Mechanics

Resolve `scripts/wow_mechanics.py` relative to this directory and invoke its absolute path. Install the entire skill directory. Requires Python 3.11+, with no third-party packages, WCL credentials or report. Default queries read a bundled, manually reviewed knowledge snapshot without network access.

## Query

```bash
python3 /absolute/path/to/wow-mechanics/scripts/wow_mechanics.py query ulatek \
  --branch retail --difficulty heroic --patch 12.1
```

Use `--build 12.1.0.69587` instead of `--patch` only when that is the actual requested context. Accepted boss names are `ulatek`, `Ula'tek` and `乌拉特克`; a bare ordinal is ambiguous. Only Retail Heroic is supported. Ask for missing identity/context rather than silently choosing it.

Completion means checking the exit code, `status`, `applicability`, each source's verification and `knowledge_gaps`. Exit 0 means the requested build matches the reviewed snapshot. Exit 1 means an error or degraded result; CLI syntax errors use exit 2. Patch-only queries and other builds return `degraded`, applicability `unknown`, and retain explicitly scoped historical knowledge. A matching snapshot does not establish live hotfix state or report applicability.

## Interpret knowledge

- `mechanics[].fact`: an original concise paraphrase of a source statement, with source IDs, journal section and difficulty-association row locators. The enclosing `scope` applies to the claim. Game data is Blizzard-authored but third-party hosted by Wago Tools.
- `strategies`: distinguish `secondary_guide` advice from `author_recommendation`. The Icy Veins strategy has unknown exact build applicability.
- `signals`: candidate WoW Spell IDs and possible event types inferred from the mechanism. `verified_detection_rule=false` remains false even after source verification. A spell link is not proof of its actual combat-log event mapping.
- `sources`: provenance, review dates and validation details. `reviewed_snapshot` is offline historical review, not a current availability claim.
- `conflicts`: unresolved differences from the reviewed snapshot, not automatically reconciled facts. An empty list is not exhaustive multi-source agreement.

Coverage is limited to three Heroic claims: Spectral Coils/Soul Constrictor, Poisonous Bite and Petrifying Sting. It is not a complete Ula'tek guide. Numerical effects, full phase mechanics, encounter timers and responsibility judgments are outside this slice.

## Optional source recheck

Add `--verify-sources` to retrieve the two fixed Wago tables and Icy Veins guide. This makes three sequential requests with a 120-second timeout each; no retries, cache or automatic knowledge updates. It compares selected build-identified rows with reviewed hashes (normalizing line endings), and checks the cited strategy passages. Full downloaded source bodies are neither saved nor included in the output.

Source states include `matched`, `missing`, `conflict`, `build_mismatch`, `fetch_failed` and `invalid_content`. When missing and changed rows coexist, the source state is `missing` and `conflicts` separately lists changed row IDs; inspect both. Failure degrades the result while retaining the historical snapshot. Claim-level `unverified` requires disclosure; do not describe retained claims as freshly confirmed. `source_matched` only establishes support for the reviewed content, not completeness, current tuning or event-detection validity. Guide passage checks are narrow, not a full-page integrity guarantee.

## Optional agent composition

Choose follow-up calls according to the user's question, not a mandatory workflow:

1. If a report is supplied, use `wcl-data index` to select the actual encounter, difficulty, attempt and participant. Keep Journal Encounter ID, Dungeon Encounter ID, WCL encounter ID and report-local IDs distinct. The stored Dungeon Encounter ID has not been validated against live WCL.
2. For a participant death review, call the existing `wcl-data death-window` and inspect `abilityGameID` for candidate signal IDs. WCL currently has no arbitrary full-raid event command. Missing events in a participant window cannot establish that a mechanic did not occur elsewhere.
3. If names are needed, pass positive observed game Spell IDs to `wow-localization spells`. Keep its names as a separate annotation; preserve the original WCL JSON, Revision, timestamps and coverage. WCL report build remains unknown unless independently supplied.

Explain observed evidence separately from source knowledge and hypotheses. A death or mechanic anomaly does not establish fault. Live three-skill report composition remains unverified; synthetic composition tests pass.
