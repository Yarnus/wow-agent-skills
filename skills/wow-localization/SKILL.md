---
name: wow-localization
description: Resolve WoW Spell IDs to zhCN game-data names. Use for standalone batch name lookup or to annotate game Spell IDs from existing evidence with build-aware names.
---

# WoW Localization

Resolve `scripts/wow_localization.py` relative to this skill directory and invoke its absolute path. Requires Python 3.11+; no credentials, WCL installation, or third-party Python packages are needed. Install the entire skill directory independently.

## Query

```bash
python3 /absolute/path/to/wow-localization/scripts/wow_localization.py spells 17 116 \
  --build 12.1.0.69587
```

For original names, use `--input FILE` instead of positional IDs; `--input -` reads stdin. Input is a nonempty JSON array:

```json
[{"spell_id":17,"original_name":"Power Word: Shield"},{"spell_id":116}]
```

IDs must be positive integers; `original_name`, if present, must be a string. Input order and duplicates are preserved. Only game Spell IDs (including aura Spell IDs) belong here; a positive number alone cannot prove its namespace. For WCL composition, extract positive `events[].abilityGameID` values. Report-local actor IDs and NPC IDs are not Spell IDs. Keep the returned name records separate and join by Spell ID for display; retain original events, identity, Revision, timestamps, and coverage unchanged.

## Interpret results

Check the exit code, top-level `status` / `error`, and every item's `match_status` and `build_status` before describing names as applicable.

Each result contains `spell_id`, `original_name` (null when absent), `localized_name`, `display_name`, `locale`, actual data `build`, `source` URL, `match_status`, and `build_status`.

- `matched`: exactly one nonempty name in the source table. These are zhCN game-data names served by Wago Tools, not machine translations. Some zhCN records themselves contain English or internal/test names; preserve source text.
- `missing`: no nonempty mapping in the fetched snapshot. `ambiguous`: conflicting nonempty names for the same ID. Both return null `localized_name`; `display_name` falls back to the supplied original name, then the ID string. Other results remain usable.
- `upstream_error`: no usable data after a retrieval or validation failure. This is not evidence that an ID is missing. Actual build is null, and `build_status` is `unknown`.
- `build_status` is `matched`, `mismatch`, `not_requested`, or `unknown`. A mismatch retains the actual source build and names but requires an applicability warning. No alternate build is silently fetched. With no requested build, make no claim about current Retail release or Report build applicability.

Exit 0 means `status=ok`, including missing/ambiguous mappings. Exit 1 means `error` (no usable data, or invalid input) or `degraded` (usable names with a failure or build mismatch). Errors distinguish `invalid_input`, `upstream_error`, `invalid_upstream_data`, `build_mismatch`, and `cache_write_failed`. When failures coexist, `error` reports the retrieval/cache failure while each item's `build_status` still exposes any mismatch. CLI syntax errors use exit 2 and stderr. Upstream response bodies are not echoed. On upstream failure, retain fallback names/IDs and continue unrelated analysis rather than inventing translations or looping retries.

## Cache and source scope

`--cache-dir` defaults to `~/.cache/wow-localization`. Each requested build has a separate zhCN snapshot; unspecified build uses a separate default snapshot. A cache hit does not contact Wago or check freshness. Use `--refresh` when updated data is needed. `cache_status` reports `hit`, `stored`, `refreshed`, `miss`, `fallback`, or `write_failed`.

Snapshots use checksum/shape validation and atomic replacement. A refresh failure preserves the last valid snapshot for the same request and returns `degraded`, `cache_status=fallback`, and the failure. A cache-write failure preserves downloaded names in the result. Cache files are internal; copying the skill does not bundle name data.

Source: Wago Tools `SpellName` CSV with `locale=zhCN` and optional `build`. Actual build comes from the response attachment filename, never from the requested build alone. The default endpoint may expose a test/PTR build. This slice does not discover release channels or infer Report builds. CSV schema and rows are checked, but there is no authoritative upstream row-count manifest: a syntactically valid shortened table cannot be proven complete. `missing` is snapshot-relative.

Only zhCN Spell names are supported. NPC names, mechanics, machine translation, WeakAura parsing, Classic applicability, automatic retries, and cache expiration are outside this slice.
