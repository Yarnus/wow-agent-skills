# P1 and death-mechanics acceptance

## Scope

Test-only acceptance of the existing working tree. No runtime, knowledge or test changes were made. Read current skill contracts, verification notes, changed implementations/tests and Issue #1. Local evidence root: `/tmp/wow-acceptance-final/` (abbreviated `A/` below). Original evidence remained under `/tmp/wcl-pvQqzXGjykc1Rt8V-review/`; SHA-256 checks cover every original file. Private raw outputs are not committed.

PASS means the actual execution met its stated contract, not that report-build applicability became known. FAIL means a reproducible behavior error; BLOCKED means external conditions prevented validation; NOT RUN means no execution occurred.

## Results

| Test | Execution | Expected | Actual | Evidence | Verdict |
| --- | --- | --- | --- | --- | --- |
| Full regressions | `python3 -m unittest discover -s tests -v` | All pass | 48 passed this round | A/tests.log | PASS |
| Compilation | `python3 -m compileall -q skills tests` | Exit 0 | Exit 0 | A/compile.log | PASS |
| Whitespace | `git diff --check` | Exit 0 | Exit 0 | A/diff-check.log | PASS |
| Explicit feign exclusion | Command regressions and live actor-25 query | Feign excluded before selection | 1 candidate, 1 excluded feign | A/tests.log; A/live-window.json | PASS |
| Mixed deaths and numbering | Regressions and original-event command replay | Same selected identity/time after filtering | Original second candidate at 6970973 ms becomes ordinal 1 | A/offline-command-replay.json | PASS |
| Unknown version | Actual mechanics CLI without version | Degraded knowledge, null requested versions | Exit 1, context_unknown, six entries | A/mechanics.json | PASS |
| Unsupported vs unknown | Executed command regressions | Unsupported boss/difficulty yields error and empty knowledge | Distinct from usable unknown-version result | A/tests.log | PASS |
| New knowledge integrity | Executed constraint tests, source-row inspection and live source recheck | Correct IDs, references, difficulty caveats, partial coverage | Six bounded entries; four sources matched; detection remains unverified | A/tests.log; A/mechanics-source-check.json | PASS |
| Missing localization | Executed synthetic missing/ambiguous/matched regression | Preserve missing IDs/names; other results usable | Exit 0 with independent item statuses and fallback names | A/tests.log | PASS |
| Original artifact reuse | Identity/window validation and hash checks | No source mutation or identity mixing | Original identity and events retained; all hashes unchanged | A/original-hashes.json; A/offline-window.json | PASS |
| Current Report Index | `wcl_data.py index pvQqzXGjykc1Rt8V` | Confirm fight and participant | Exit 0, Revision 3, fight 2, encounter 3492, difficulty 4, actor 25 present | A/live-index.json | PASS |
| One live death window | `death-window pvQqzXGjykc1Rt8V --fight-id 2 --actor-id 25 --limit 10000` | Complete bounded query, correct selection | Exit 0 / ok; 260/260 events, no truncation or clipping | A/live-window.json | PASS |
| Actual multi-page retrieval | Inspect live pagination JSON | Explicit termination with honest page counts | Death search 1 page, event window 2 pages, both terminated | A/live-window.json | PASS |
| Live/offline identity separation | Compare outputs without merging | Preserve each provenance | Both Revision 3; identity and event arrays equal | A/offline-window.json; A/live-window.json | PASS |
| Display localization | Separate calls using observed positive abilityGameID values | Retain all IDs and applicability caveats | 62/62 matched in each call; cache hit, build_status not_requested | A/offline-names.json; A/live-names.json | PASS |
| Mechanics independence | Absolute CLI path, cwd /tmp, child environment without WCL_* | No WCL credentials needed | Usable degraded knowledge | A/executions.json; A/mechanics.json | PASS |
| Localization independence | Same child isolation, actual spells input | No WCL credentials needed | Exit 0 / ok, usable cached names | A/executions.json; A/live-names.json | PASS |
| Fresh localization network fetch | Not requested; cache was usable | No claim of fresh source retrieval | Cache hit only | A/live-names.json | NOT RUN |
| Full raid/current 42-page validation | Deliberately outside scope | No full-raid completeness claim | One participant, 15-second window only | A/live-window.json | NOT RUN |

No BLOCKED or runtime FAIL occurred. No credentials were printed or supplied on command lines. Child environments removed all WCL_* keys without changing the parent environment. Standalone scripts ran outside the repository cwd, without old-repository imports, workflow initialization, rankings or HTML rendering. Copied-skill independence tests also ran as part of the full suite.

## Representative chain: four evidence categories

Identity: Report pvQqzXGjykc1Rt8V, Revision 3, fight 2, actor 25. Original and live actual/requested window both [6960973, 6975973] report-relative ms. Selected death is 6970973 ms (08:44.705 after pull), not the earlier explicitly marked feign. Original ordinal 2 was not reused as a CLI selector. Build remains null. This attempt was a kill, not a wipe.

**Direct observations:** The original and fresh event arrays both contain damage 1316357 at 6968946 (187518), 6969963 (176267), and 6970972 (136251, overkill 40016). Between them are 1292403 at 6970083 (440924) and 1286835 at 6970272 (39964). Death metadata identifies killingAbilityGameID 1316357. Earlier in this window, 1305878 has amount 0 and 1316356 is applied; mere presence of 1305878 is not evidence that it delivered this lethal hit.

**Source-supported facts:** Fixed-build Spell 1306086 explicitly references 1305878 for Purge impact and 1316357 for periodic damage, with 1312967/1316356 serving distinct aura contexts. Journal section 37034 is a child of Heroic-associated 37031 (association 19141). The reviewed snapshot is build 12.1.0.69587, not the report build. Primary sources: https://wago.tools/db2/Spell/csv?build=12.1.0.69587 ; https://wago.tools/db2/JournalEncounterSection/csv?build=12.1.0.69587 ; https://wago.tools/db2/JournalSectionXDifficulty/csv?build=12.1.0.69587 . All configured row fingerprints matched in this round's network recheck.

**Unproven explanation:** The separate aura and repeated damage records are consistent with the sourced Purge periodic-damage role. This adds a supported distinction to the prior damage-only explanation. It does not establish who caused exposure, whether positioning was avoidable, whether a soak failed, or whether aura removal means natural expiration. Observed Caustic Waves damage is not evidence for the Mythic-only Purge-expiration clause in this Heroic encounter.

**Unknown factors:** Report build/hotfix applicability, exact spatial relationships, upstream assignments, other players' complete actions and complete encounter coverage. Localization returned actual data build 12.1.5.69848 with no requested build; names are annotations only. Source matching is not proof of report applicability or verified detection rules.

## Before/after interpretation

The prior lethal-event finding for 1316357 remains supported. Added knowledge explains why the impact and periodic damage IDs must not be collapsed merely because they share the zhCN name 易爆清除. Any generic claim that an earlier same-name impact was this death's direct cause must be withdrawn; any spatial, soak-failure or responsibility claim remains unproven. No such stronger claim is needed for useful three-skill composition. P1's earlier feign correction remains necessary: a type=death record alone is not sufficient to count a real death.

Offline replay used original death/events with constructed HTTP envelopes and minimal synthetic metadata while preserving report/revision/fight/actor selectors. It is not a recording of original HTTP pagination. Fresh Index/window calls are separately saved and supply this round's actual two-page evidence. Historical 42-page tests and previous source research are not counted as newly executed.

## Findings and next action

No reproducible implementation defect was found in the exercised scope; no runtime repair is requested. The concrete maintenance discrepancy was Issue #1's top mechanics checkbox still describing three claims and unverified live composition while later comments documented six entries and validation. Minimal reproduction: `gh issue view 1 --json body,comments`; compare the top mechanics item with the latest progress comments. Root cause is summary drift, not a skill failure; synchronize that item as part of this authorized Issue update.

Known report-build, difficulty-inheritance, localization freshness and full-raid limitations remain disclosed limits, not automatically new feature tasks. No relaxation of assertions, new feature, raw private dataset or unnecessary player identity was introduced for acceptance.
