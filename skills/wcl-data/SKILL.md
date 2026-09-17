---
name: wcl-data
description: Retrieve Warcraft Logs Retail raid facts. Use to list a Report's Boss Attempts and participants, or inspect a specified participant's events around a death.
---

# WCL Data

Return Report facts with provenance and explicit coverage. This skill works independently; the caller decides whether to combine its results with mechanics or localization.

## Invocation

Requires Python 3.11+ and privately configured `WCL_CLIENT_ID` / `WCL_CLIENT_SECRET` environment variables for an official WCL OAuth client. `WCL_ID` / `WCL_SECRET` are also supported when neither primary variable is set; credential pairs are never mixed. Keep credentials out of prompts, command arguments, output, and artifacts. Missing credentials produce a setup error; ask the user to configure them privately.

Resolve `scripts/wcl_data.py` relative to this skill directory, then use its absolute path from any working directory:

```bash
python3 /absolute/path/to/wcl-data/scripts/wcl_data.py index REPORT
python3 /absolute/path/to/wcl-data/scripts/wcl_data.py death-window REPORT \
  --fight-id 7 --actor-id 10 --death 1 --before-ms 10000 --after-ms 5000 --limit 100
```

`REPORT` is a code or an HTTPS report URL on `warcraftlogs.com`, `www.warcraftlogs.com`, or `cn.warcraftlogs.com`. URL query parameters and fragments do not select the fight or actor; use explicit flags. Inspect `death-window --help` for available flags.

- **Discovery:** use `index` when the Boss Attempt or participant ID is unknown. Select from `attempts[].participants`; names alone may be ambiguous. An explicit request such as “last wipe” can be resolved from the listed times and kill flags; disclose the chosen fight ID.
- **Death window:** use exact Report-local fight and actor IDs. `--death` is the one-based chronological death ordinal. When omitted, one death is selected automatically; multiple deaths return `needs_selection` with candidates. Ask for selection rather than guessing. `no_death` means the complete filtered death search found none, not that the participant took no damage.

Completion means a JSON result was returned and its status and coverage were checked. Exit 0 includes `ok`, `needs_selection`, and `no_death`; exit 1 is a structured retrieval/selection error without partial evidence. CLI syntax errors use exit 2 and stderr. A rate-limit error requires a later retry, not an immediate retry loop.

## Evidence contract

- `identity` retains Report code and Revision; death results add fight and actor IDs. `source` retains the WCL link, endpoint, time basis, and ID namespaces. `attempt` and `participant` identify the selected subject; `actors` resolves event identities where available. Unknown actor identities produce a warning, not an invented NPC mapping.
- Times are milliseconds relative to Report start. `source.report_start_unix_ms` permits conversion to Unix time. Death windows are clipped to the Boss Attempt; compare `requested_window_ms` and `actual_window_ms`.
- Events include the participant as **source or target**. Retrieval fetches all-actor deaths for the attempt, then all actors' events only within the selected short window; participant filtering uses returned Report-local IDs locally. `death_search_scope`, `upstream_window_scope`, and `actor_filter` disclose this distinction. Owned pets, unrelated team events, and surrounding events outside the window are not implicitly included. Returned event fields retain WCL names; `abilityGameID` is a Spell ID, while `sourceID` and `targetID` are Report-local actor IDs.
- `death_pagination` describes the full-attempt participant death search; `event_pagination` describes the selected event window. Each successful paginator requires explicit upstream termination. Revision is checked across retrieval. `query_complete` describes only the filtered event window and is false when no window was queried.
- `display.matched`, `returned`, and `truncated` describe the event array for successful windows, death candidates for selection results, and attempts for the index. `--limit` only limits displayed events; all pages are still checked. Increase it to inspect more events.
- `whole_attempt_events` and `complete_bundle` remain false. Even a window spanning the entire attempt is still participant-filtered. Cite Report, Revision, fight ID, actor ID, and timestamps when explaining facts. Keep responsibility and wipe-causality interpretations separate from observations.

## Current limits

Supports public/unlisted Retail reports whose principal WCL zone is identified as a raid, and completed fights recognized in that zone. Classic, private reports, Mythic+, mixed reports requiring another zone's discovery, and in-progress fights are unsupported or excluded. Build applicability is unknown.

No persistent cache, complete export, statistics, automatic retries, resume, or full-encounter Bundle is implemented. OAuth tokens are process-local. Retrieval is held in memory; large windows cost more requests and memory even with a small display limit. Upstream failures discard partial evidence. Revision equality is an observed consistency check, not a server-side snapshot guarantee.

The executable interface is tested with synthetic HTTP responses and standalone subprocess checks. Authorized live testing passed OAuth, Report Index discovery, and a participant death window, including explicit pagination termination and display truncation. A later authorized Ula'tek participant-window check also passed 42-page retrieval with unchanged Revision, explicit termination, and no display truncation. This verifies one live case, not whole-raid coverage. WCL's special Environment actor ID `-1` is retained without inventing an NPC ID from `gameID=0`. Flexible raid difficulties may have empty size lists.
