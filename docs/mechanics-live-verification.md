# Authorized live mechanics composition check

## Scope

User supplied https://cn.warcraftlogs.com/reports/pvQqzXGjykc1Rt8V?fight=2 for validation. Queried Report Revision 3, fight 2, Ula'tek, encounter ID 3492, raid zone 53. Fight duration: 589,712 ms; kill. The official WCL `worldData.zone(id: 53).difficulties` response names difficulty 4 as Heroic. This is distinct from game-data Difficulty ID 15. The journal's DungeonEncounterID matches this particular WCL encounter ID; this is not a universal namespace equivalence.

Report build is unknown. The user-selected 12.1 context was passed to mechanics, which correctly returned degraded / applicability unknown. Localization used the explicitly reviewed 12.1.0.69587 snapshot for display only, not as an assertion of report build.

## Commands and evidence

Commands used existing skill entrypoints, no new workflow or runtime code:

```bash
python3 skills/wcl-data/scripts/wcl_data.py index pvQqzXGjykc1Rt8V
python3 skills/wow-mechanics/scripts/wow_mechanics.py query ulatek --branch retail --difficulty heroic --patch 12.1
python3 skills/wcl-data/scripts/wcl_data.py death-window pvQqzXGjykc1Rt8V --fight-id 2 --actor-id 35 --limit 2000
python3 skills/wcl-data/scripts/wcl_data.py death-window pvQqzXGjykc1Rt8V --fight-id 2 --actor-id 35 --before-ms 600000 --after-ms 5000 --limit 50000
python3 skills/wow-localization/scripts/wow_localization.py spells --input /tmp/wow-mechanics-live-pvQqzXGjykc1Rt8V/spells.json --build 12.1.0.69587 --cache-dir /tmp/wow-mechanics-live-pvQqzXGjykc1Rt8V/name-cache
```

Actor 35 was selected as the first listed participant for interface validation, not because of suspected responsibility. Their only death is at report-relative 7,020,007 ms. The default 15-second window contained 687 participant events and none of the candidate IDs. A deliberately expanded window was necessary to examine earlier signals.

Expanded actual window: [6,446,268, 7,025,007] ms, clipped to fight start. Retrieval paginated through 42 all-actor upstream event pages, then locally filtered to 25,336 participant-source-or-target events; all were displayed. Death search used one page. Both paginations terminated explicitly; Revision remained 3. `query_complete=true`, `whole_attempt_events=false`, `complete_bundle=false`. The window does not include the fight's final 10,973 ms or unrelated participants' events. This expensive expanded window is a validation probe, not a recommended default or new arbitrary raid-query feature.

## Observations

Counts below apply only to the selected participant and window:

| Spell ID | Snapshot zhCN name | Observed event types/counts | First report-relative / fight-relative ms |
| --- | --- | --- | --- |
| 1287265 | 幽魂盘卷 | damage: 10 | 6473770 / 27502 |
| 1300685 | 灵魂绞杀者 | applydebuff: 5; removedebuff: 5 | 6477025 / 30757 |
| 1287036 | 剧毒撕咬 | applydebuff: 2; removedebuff: 2 | 6833376 / 387108 |
| 1303414 | Not queried for names because not observed | No matches in this window | — |

Observed sources: report actor 86, Spectral Coil, NPC ID 267679; actor 87, Blightscale Rawling, NPC ID 261874. This confirms that three candidate IDs are observable with the stated event types in this report. It does not verify all proposed event types (notably cast), prove cause/effect or establish a reusable detection rule. Petrifying Sting remains unverified, not disproved.

Localization exited 0 with all three IDs matched, response build 12.1.0.69587. The name input was derived only from positively observed `abilityGameID` values. Original WCL JSON was not rewritten: SHA-256 before and after extraction/localization was `7ce98a58248d28c520dd560edba9d06026e68a12ee4d1171ce74d41e9fe54c87`.

## Artifacts and limits

Raw evidence and separately derived files are kept locally under `/tmp/wow-mechanics-live-pvQqzXGjykc1Rt8V/` (temporary, not repository fixtures). No credentials or raw report datasets are committed. This check establishes live independent composition and live multi-page retrieval for this one case. It is not complete encounter coverage, a mechanics correctness proof, raid-wide analysis, player grading or responsibility attribution. No runtime code, signal `verified_detection_rule` flags or original evidence were changed.

## Bounded follow-up

A separate, one-off official API research probe queried fight 2 over [6446268, 7035980] ms with `filterExpression: "ability.id = 1303414"`, `dataType: All`, and game ability/report-local actor IDs enabled. One page returned zero events and `nextPageTimestamp: null`. Revision was checked before, within and after the request and remained 3. The query and response are saved locally in `sting-probe.json`. Unlike the participant-window CLI, this was a narrow spell-filtered full-fight API probe; no general query command was added. Zero returned matches do not validate the proposed mapping, rule out alternate spell variants or prove that the mechanic never occurred. A positive control with the same filter form (`ability.id = 1287265`) over [6473000, 6478000] ms returned 42 events, all with `abilityGameID=1287265`, explicit termination and unchanged Revision 3 (`filter-positive-control.json`). This checks the filter form against a known observed ID, without proving the missing signal's identity. Investigation stops here rather than guessing a replacement ID.

The portable mechanics output now describes the scoped observations instead of incorrectly saying no live mapping has been observed. All detection flags remain false. Reviewed interpretation boundaries: Spectral Coils damage or Soul Constrictor application alone does not establish correct soaking, defensive use or fault; Poisonous Bite application/removal does not identify avoidability or a dispel; Petrifying Sting has no confirmed event mapping in this check. None of these observations establishes death causality, full strategy correctness or report-build applicability.

A reduced de-identified fixture records five observed event shapes with synthetic timestamps and remapped actor/fight IDs; its transformations are documented beside it. Command-level tests replay these shapes over two synthetic upstream pages, check exact event preservation and unknown report build, then resolve the three observed IDs via a synthetic name source without rewriting WCL evidence. A separate regression first failed on the stale knowledge-gap statement, then passed after the scoped correction. These are reproducible offline checks, not a replay of all 42 live pages or an additional live validation. All 41 repository tests, Python compilation and diff whitespace checks passed after the follow-up.
