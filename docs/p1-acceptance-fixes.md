# P1 fixes from real composition acceptance

## Reproduction and root causes

The original local artifacts under `/tmp/wcl-pvQqzXGjykc1Rt8V-review/` were available and read. A participant's first death candidate had `feign: true`; the second lethal event omitted the field. Candidate generation filtered only by actor before numbering. Window consistency also accepted a same-time feign in place of the selected death.

Mechanics CLI reproduction without either version flag exited 2. Its argument group required a version, and downstream validation assumed a non-null version string. This prevented an honest unknown-version query despite an available scoped historical snapshot.

Before implementation changes, two command-seam regressions failed: the mixed death/feign result returned `needs_selection` instead of `ok`; unknown-version mechanics exited 2 instead of returning degraded knowledge. Additional malformed-flag and window-consistency tests failed before their fixes.

## Interface changes

- WCL classifies deaths before candidate numbering and selection. Only explicit boolean true is excluded. `death_classification` reports eligible candidates, excluded feigns and missing flags over the participant's full-attempt death search. Raw window events are preserved. An absent flag remains eligible under existing behavior, not a claim that absence independently proves a true death. Present non-boolean flags fail validation without partial evidence. A same-time feign cannot satisfy selected-death window consistency.
- Mechanics accepts omitted build/patch with explicit boss, branch and difficulty. It returns exit 1, `degraded`, `context_unknown`, unknown applicability and null requested versions, retaining the snapshot and actual source build. Known-version behavior, unsupported-content errors and CLI syntax errors remain distinct. Source-check failures can take precedence in `error`; applicability still discloses unknown requested context.

The live artifacts establish only true and absent flag shapes. Attempts to consult the official WCL help page failed; no authoritative semantics for non-boolean encodings were obtained. Rejecting those values is a local validation policy, not an invented upstream meaning.

## Verification

- `python3 -m unittest discover -s tests -v`: all 46 tests passed, including mixed deaths/feigns, only feigns, multiple eligible deaths, boolean false, absent flags, malformed values in both search and window, and selection consistency.
- `python3 -m compileall -q skills tests` and `git diff --check`: passed.
- Unknown-version CLI: exit 1, three mechanics, source build `12.1.0.69587`, null requested build/patch and unknown applicability. Exact-build, patch-only, other-build, unsupported-context, malformed-version and source-recheck regressions passed.
- Offline replay through the WCL command seam used both original death records and the original 260-event lethal window, with synthetic report metadata. It selected ordinal 1 after excluding one feign, and preserved the original window events exactly. This replays the captured selected evidence, not the original upstream HTTP pagination transcript.
- One authorized live WCL invocation queried only fight 2 / actor 25 in the original report, using existing private environment credentials. Revision 3 remained consistent. It returned `ok`, one eligible candidate at report-relative 6970973 ms, one excluded feign, and one missing flag. The 15-second window [6960973, 6975973] ms returned 260/260 events with no truncation or clipping. Death pagination: one page; event pagination: two pages; both explicitly terminated. Whole-attempt events and complete bundle remain false.

Only two de-identified event shapes and transformation notes are added as fixtures. Full player analysis, raw report datasets and credentials remain outside the repository. Live output is local at `/tmp/wow-p1-live.json`; unknown-version output is `/tmp/wow-p1-mechanics.json`.

## Remaining limits

No mechanics were added, no detection rules promoted, and no batch interface, new skill or workflow introduced. Missing feign flags retain the existing upstream death-event interpretation. Unknown report versions cannot establish snapshot or hotfix applicability. This live check validates one participant window, not all participants or an entire encounter. No source recheck was performed against live mechanics sources in this fix round; source-recheck tests used synthetic HTTP responses.
