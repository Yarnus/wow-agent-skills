# Bounded participant death discovery verification

Baseline commit: `2c8fe6c` preserves the previously validated P1 and mechanics work. The maintained interface is documented in [the skill instructions](../skills/wcl-data/SKILL.md). This slice does not complete the whole first-release roadmap.

## Delivered interface

`deaths REPORT --fight-id N [--limit N]` retrieves one paginated death stream, filters to attempt participants and uses the shared explicit-feign classification. Chronological records preserve repeated deaths and contain `actor_id`, actor-local `death` ordinal and `timestamp`. Join identities through `attempt.participants`; report/revision/fight come from top-level `identity`. Classification totals for this command cover all attempt participants (not just one participant).

Pass the selected record into existing `death-window` with explicit actor/death and paired `--expected-revision` / `--expected-death-timestamp`. Revision or timestamp mismatch rejects selection rather than choosing a fallback. Existing unguarded usage remains available. Guards are opt-in and report revision equality is not a server snapshot guarantee.

## Recovery and automated evidence

The plan-executor timed out after preserving implementation/tests/docs, so its task was not accepted as successful. Parent inspected the actual diff and transcript. Transcript evidence shows new commands/flags initially failing with argparse exit 2, then passing; a missing guarded candidate initially returned success and was corrected after a failing test. Parent reran the complete suite: **58 tests passed**, plus `python3 -m compileall -q skills tests` and `git diff --check`.

Regressions cover participant filtering, multiple deaths, mixed feigns, no eligible deaths, multi-page discovery, truncation, invalid fields, stale revision/time and missing guarded candidates. The paginated fixture checks exactly two death requests for two pages rather than per-participant repetition. Additional parent command-seam probes verified an untruncated repeated-death list passed directly into guarded window selection, plus a genuinely empty death stream. These supplemental probes are saved locally, not new shipped tests.

## Authorized live acceptance

Used existing private environment credentials. Executed exactly one discovery for report `pvQqzXGjykc1Rt8V`, fight 2, then one guarded actor-25 window. No all-participant window expansion occurred. A temporary wrapper called the actual command entrypoint and counted urllib request categories without logging credentials, request bodies or headers.

| Operation | Result | Actual requests / pages |
| --- | --- | --- |
| Discovery | exit 0 / ok; Revision 3; 7 eligible deaths, 1 excluded feign, 7 absent feign fields; 7/7 records, no truncation | 1 OAuth + 4 GraphQL calls; death stream 1 page, explicitly terminated |
| Guarded window | exit 0 / ok; actor 25, ordinal 1, death 6970973 ms, Revision 3; 260/260 events | 1 OAuth + 7 GraphQL calls; death search 1 page, event window 2 pages, explicitly terminated |

Selected death and identity match the earlier actor-25 evidence at Revision 3. Requested and actual window are [6960973, 6975973] report-relative ms. No clipping or display truncation occurred. Discovery query completeness describes participant deaths only; window completeness describes participant-source-or-target events only. Both `whole_attempt_events` and `complete_bundle` remain false.

The new discovery's real death pagination was single-page; multi-page discovery was tested synthetically, not claimed live. The window really used two event pages. No numerical performance improvement is inferred from request counts, and independent window selection still rechecks death candidates.

Private outputs and counts: `/tmp/wow-death-discovery-acceptance/{discovery,window}.json`, `{discovery,window}-requests.json`, `supplemental.log`. Full test log: `/tmp/wow-discovery-recovery-tests.log`. No raw event datasets or player names are added to the repository.

## Limits

No automatic all-window retrieval, complete export, responsibility scoring, persistent player history or generic batch framework. Mechanics/localization scope is unchanged. Default discovery limit can truncate presentation but never pagination; inspect display metadata. Missing feign fields remain eligible under the documented P1 policy.
