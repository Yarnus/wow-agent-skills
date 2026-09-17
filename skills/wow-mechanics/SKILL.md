---
name: wow-mechanics
description: Query sourced Heroic Ula'tek mechanics independently, or identify candidate event signals for a Warcraft Logs follow-up. Exposes build applicability, strategy attribution, and knowledge gaps.
---

# WoW Mechanics

Resolve `scripts/wow_mechanics.py` relative to this directory and invoke its absolute path. Install the entire skill directory. Requires Python 3.11+, with no third-party packages, WCL credentials or report. Default queries read a bundled, manually reviewed knowledge snapshot without network access.

## Query

```bash
python3 /absolute/path/to/wow-mechanics/scripts/wow_mechanics.py query ulatek \
  --branch retail --difficulty heroic
```

Omit both version flags when the report's build and patch are unknown. Supply `--patch 12.1` or `--build 12.1.0.69587` only when that is the actual requested context; the flags are mutually exclusive. Accepted boss names are `ulatek`, `Ula'tek` and `乌拉特克`; a bare ordinal is ambiguous. Only Retail Heroic is supported. Ask for missing boss, branch or difficulty rather than silently choosing it; an unknown version is accepted without guessing.

Completion means checking the exit code, `status`, `applicability`, each source's verification and `knowledge_gaps`. Exit 0 means the requested build matches the reviewed snapshot. Exit 1 means an error or degraded result; CLI syntax errors use exit 2. Unknown-version queries return `degraded`, error `context_unknown`, applicability `unknown`, and null requested build/patch. Patch-only queries and other builds retain their existing `patch_applicability_unknown` result. All retain explicitly scoped historical knowledge, actual source build and provenance. Unsupported identity/branch/difficulty returns `error` with no mechanics; malformed version strings return `invalid_context`; missing flag values or mutually exclusive flags are CLI syntax errors (exit 2). A matching snapshot does not establish live hotfix state or report applicability.

## Interpret knowledge

- `mechanics[].fact`: an original concise paraphrase of a source statement, with source IDs, journal section, spell-text and available difficulty-association row locators. Inspect `scope.difficulty_basis`: a Heroic-associated parent differs from a direct association; observed Heroic events do not validate generic journal inheritance. The enclosing `scope` applies to the claim. Game data is Blizzard-authored but third-party hosted by Wago Tools.
- `strategies`: distinguish `secondary_guide` advice from `author_recommendation`. The Icy Veins strategy has unknown exact build applicability.
- `signals`: candidate WoW Spell IDs and possible event types inferred from the mechanism. `verified_detection_rule=false` remains false even after source verification. A spell link is not proof of its actual combat-log event mapping.
- `sources`: provenance, review dates and validation details. `reviewed_snapshot` is offline historical review, not a current availability claim.
- `conflicts`: unresolved differences from the reviewed snapshot, not automatically reconciled facts. An empty list is not exhaustive multi-source agreement.

Coverage is limited to six bounded entries: Spectral Coils/Soul Constrictor, Poisonous Bite, Petrifying Sting, Falling Debris under Rage of the Shackled, Virulent Spit, and Serpent's Bite / Volatile Purge. These include child effects, not six independent mechanics. Purge signals distinguish impact, periodic damage, pre-expiration aura and periodic aura by ID rather than localized name. Falling Debris and Virulent Spit have observed Heroic signals but unverified journal difficulty inheritance; their generic spell facts are not Heroic-exclusive claims. Mythic-only Purge effects are excluded. It is not a complete Ula'tek guide. Numerical effects, full phase mechanics, encounter timers and responsibility judgments are outside this slice.

## Optional source recheck

Add `--verify-sources` to retrieve three fixed Wago tables (journal sections, difficulty associations and spell text) and the Icy Veins guide. This makes four sequential requests with a 120-second timeout each; no retries, cache or automatic knowledge updates. It compares selected build-identified rows with reviewed hashes (normalizing line endings), and checks the cited strategy passages. Full downloaded source bodies are neither saved nor included in the output.

Source states include `matched`, `missing`, `conflict`, `build_mismatch`, `fetch_failed` and `invalid_content`. When missing and changed rows coexist, the source state is `missing` and `conflicts` separately lists changed row IDs; inspect both. Failure degrades the result while retaining the historical snapshot. Claim-level `unverified` requires disclosure; do not describe retained claims as freshly confirmed. `source_matched` only establishes support for the reviewed content, not completeness, current tuning or event-detection validity. Guide passage checks are narrow, not a full-page integrity guarantee.

## Optional agent composition

Choose follow-up calls according to the user's question, not a mandatory workflow:

1. If a report is supplied, use `wcl-data index` to select the actual encounter, difficulty, attempt and participant. Keep Journal Encounter ID, Dungeon Encounter ID, WCL encounter ID and report-local IDs distinct. The stored Dungeon Encounter ID matched one authorized Ula'tek report's encounter ID; this is not a universal namespace equivalence. WCL Heroic ID 4 and game-data Heroic ID 15 are distinct.
2. For a participant death review, call the existing `wcl-data death-window` and inspect `abilityGameID` for candidate signal IDs. WCL currently has no arbitrary full-raid event command. Missing events in a participant window cannot establish that a mechanic did not occur elsewhere.
3. If names are needed, pass positive observed game Spell IDs to `wow-localization spells`. Keep its names as a separate annotation; preserve the original WCL JSON, Revision, timestamps and coverage. WCL report build remains unknown unless independently supplied.

Explain observed evidence separately from source knowledge and hypotheses. Damage or aura application alone does not prove correct soaking, defensive use or avoidability; aura removal alone does not identify a dispel. A death or mechanic anomaly does not establish fault. Synthetic composition tests and one authorized live participant-window composition pass. Three candidate IDs were observed (1287265 damage; 1300685 and 1287036 debuff application/removal); 1303414 remains unverified. These observations do not promote signals to verified detection rules.
