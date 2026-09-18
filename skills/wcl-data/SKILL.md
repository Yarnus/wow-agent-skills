---
name: wcl-data
description: Retrieve Warcraft Logs Retail raid facts. Use to list a Report's Boss Attempts and participants, query a bounded attempt event range, discover participant deaths, or inspect a specified participant's events around a death.
---

# WCL Data

Return Report facts with provenance and explicit coverage. This skill works independently; the caller decides whether to combine its results with mechanics or localization.

## Invocation

Requires Python 3.11+ and privately configured `WCL_CLIENT_ID` / `WCL_CLIENT_SECRET` environment variables for an official WCL OAuth client. `WCL_ID` / `WCL_SECRET` are also supported when neither primary variable is set; credential pairs are never mixed. Keep credentials out of prompts, command arguments, output, and artifacts. Missing credentials produce a setup error; ask the user to configure them privately.

Resolve `scripts/wcl_data.py` relative to this skill directory, then use its absolute path from any working directory:

```bash
python3 /absolute/path/to/wcl-data/scripts/wcl_data.py index REPORT
python3 /absolute/path/to/wcl-data/scripts/wcl_data.py events REPORT \
  --fight-id 7 --start-ms 1000 --end-ms 5000 --spell-id 1287265 \
  --event-type damage --actor-id 10 --actor-role either --expected-revision 2
python3 /absolute/path/to/wcl-data/scripts/wcl_data.py deaths REPORT \
  --fight-id 7 --limit 100
python3 /absolute/path/to/wcl-data/scripts/wcl_data.py death-window REPORT \
  --fight-id 7 --actor-id 10 --death 1 --expected-revision 2 \
  --expected-death-timestamp 12000 --before-ms 10000 --after-ms 5000 --limit 100
```

`REPORT` is a code or an HTTPS report URL on `warcraftlogs.com`, `www.warcraftlogs.com`, or `cn.warcraftlogs.com`. URL query parameters and fragments do not select the fight or actor; use explicit flags. Inspect `death-window --help` for available flags.

- **Discovery:** use `index` when the Boss Attempt or participant ID is unknown. Select from `attempts[].participants`; names alone may be ambiguous. An explicit request such as “last wipe” can be resolved from the listed times and kill flags; disclose the chosen fight ID.
- **Event query:** use `events` with a supported Boss Attempt ID and an explicit report-relative `--start-ms` / `--end-ms` range. Optional single-value filters are `--spell-id`, `--event-type`, and participant `--actor-id`; supplied filters are ANDed. Event type is one of `damage`, `cast`, `applydebuff`, or `removedebuff`. Actor role is `source`, `target`, or `either` (the default when an actor is supplied); owned pets are not implicit participants. `--expected-revision` optionally guards a prior Index selection. `--limit` truncates display only. Finite fractional bounds are accepted, clipped to the attempt, and applied locally as a closed interval after an outward-rounded upstream request. A non-overlapping range is an error; zero matches return `status=ok`, an empty `events` array, and complete filtered-query coverage.
- **Death list:** use `deaths` with a supported Boss Attempt ID to retrieve one paginated all-actor death stream. The result retains only attempt participants, excludes explicit `feign=true` events before numbering, preserves repeated deaths and chronological order, and returns each participant's actor-local one-based `death` ordinal. `--limit` limits displayed death records after all pages are checked. `no_death` means the complete filtered search found no eligible participant deaths; it does not mean the attempt had no other events.
- **Death window:** use exact Report-local fight and actor IDs. `--death` is the one-based chronological candidate ordinal after excluding deaths explicitly marked `feign=true`. When omitted, one death is selected automatically; multiple deaths return `needs_selection` with candidates. Ask for selection rather than guessing. `no_death` means the complete filtered death search found no eligible deaths, including when it found only explicit feigns; it does not mean the participant took no damage. To safely select from a prior `deaths` result, pass its `identity.report_revision` as `--expected-revision`, its selected timestamp as `--expected-death-timestamp`, and the explicit `--death` ordinal. Guards are paired, reject stale revision or timestamp before an event window is fetched, and never choose a fallback candidate.
- **Death classification:** `death_classification` covers all attempt participants for `deaths`, or the selected participant for `death-window`, and reports full-attempt `candidate_count`, `excluded_feign_count`, `missing_feign_count` and policy `exclude_explicit_true`. Boolean false and absent `feign` remain eligible; absence is not an independently verified non-feign flag. Present non-boolean values cause a structured retrieval error without partial evidence. Candidate lists, counts, ordinals and automatic/window selection all use the same filtered set. Raw window events remain unchanged and may still contain feigns; use the classification rather than counting every `type=death` event.

Completion means a JSON result was returned and its status and coverage were checked. Exit 0 includes `ok`, `needs_selection`, and `no_death`; exit 1 is a structured retrieval/selection error without partial evidence. CLI syntax errors use exit 2 and stderr. A rate-limit error requires a later retry, not an immediate retry loop.

## Evidence contract

- `identity` retains Report code and Revision; death results add fight ID, and death-window results add actor ID. `source` retains the WCL link, endpoint, time basis, and ID namespaces. `attempt` and `participant` identify the selected subject; `actors` resolves event identities where available. Unknown actor identities produce a warning, not an invented NPC mapping.
- Times are milliseconds relative to Report start. `source.report_start_unix_ms` permits conversion to Unix time. Death windows are clipped to the Boss Attempt; compare `requested_window_ms` and `actual_window_ms`.
- Event-query results preserve original matched event objects. Fixed Spell/type expressions narrow the upstream request; returned event type and `abilityGameID` must agree with those filters. WCL expression actor IDs are not treated as Report-local event actor IDs: participant role filtering always uses returned `sourceID` / `targetID` locally. `query` records requested/actual ranges and filters; `coverage` records the outward-rounded upstream range, expression, local filter, and pagination. `abilityGameID` is a game Spell ID, while `sourceID` and `targetID` are Report-local actor IDs.
- Death-window events include the participant as **source or target**. Retrieval fetches all-actor deaths for the attempt, then all actors' events only within the selected short window; participant filtering uses returned Report-local IDs locally. `death_search_scope`, `upstream_window_scope`, and `actor_filter` disclose this distinction. Owned pets, unrelated team events, and surrounding events outside the window are not implicitly included.
- `death_pagination` describes the full-attempt participant death search; `event_pagination` describes the selected event window. Each successful paginator requires explicit upstream termination. Revision is checked across retrieval. `query_complete` describes the filtered event window for a window result and the filtered death stream for a death-list result; it is false when no window was queried in a death-window selection result.
- `display.matched`, `returned`, and `truncated` describe the event array for successful windows, death candidates for selection results or death-list results, and attempts for the index. `--limit` only limits displayed records; all pages are still checked. Increase it to inspect more records.
- `whole_attempt_events` is true only for an unfiltered event query whose actual range covers the full attempt and whose pagination and Revision checks complete; display may still be truncated. `complete_bundle` remains false because this command creates no export manifest. Death results keep both fields false. Cite Report, Revision, fight ID, filters and timestamps when explaining facts. Keep responsibility and wipe-causality interpretations separate from observations.

## Current limits

Supports public/unlisted Retail reports whose principal WCL zone is identified as a raid, and completed fights recognized in that zone. Classic, private reports, Mythic+, mixed reports requiring another zone's discovery, and in-progress fights are unsupported or excluded. Build applicability is unknown.

No arbitrary expression input, multi-value filter, persistent cache, complete export, statistics, automatic retries, resume, or Complete Bundle is implemented. OAuth tokens are process-local. Retrieval is held in memory; large ranges cost more requests and memory even with a small display limit. Upstream failures discard partial evidence. Revision equality is an observed consistency check, not a server-side snapshot guarantee.

The executable interface is tested with synthetic HTTP responses and standalone copied-skill subprocess checks. One post-implementation authorized bounded live acceptance at Revision 3 completed a one-page known Spell/type query with 42 matches and three displayed events; filtered coverage remained distinct from whole-attempt coverage, and separate localization did not rewrite the event JSON. This is one narrow case, not broad report coverage. A pre-implementation authorized probe found that expressions using returned Report-local actor IDs produced no matches and that a fractional start returned an earlier timestamp, motivating local actor and exact-range filtering. Historical live testing separately passed Index, death windows, and one 42-page participant window. WCL's special Environment actor ID `-1` is retained without inventing an NPC ID from `gameID=0`. Flexible raid difficulties may have empty size lists.
