# Bounded death-mechanics acceptance

## Scope and evidence

Extended the existing Retail Ula'tek snapshot from three to six bounded entries, not full encounter coverage or six independent mechanics. See [source review](death-mechanics-source-research.md). No runtime interface changes, batch queries, new skills, detection DSL, or old-project changes were required. Original report build remains unknown.

Existing artifacts were available. Report `pvQqzXGjykc1Rt8V`, Revision 3, fight 2 identifies Ula'tek, encounter 3492, WCL difficulty 4 (Heroic; distinct from game-data difficulty 15). The report was a kill. Across the saved participant windows, observed `abilityGameID`/event-type pairs include 1286885 damage, 1302982 damage, 1305878 damage, 1316357 damage, and 1312967/1316356 debuff application/removal. Death metadata and nearby overkill records corroborate direct lethal hits from the first four IDs in different windows; this does not prove upstream positioning or responsibility.

P1 command regressions passed before edits: explicit feigns excluded from default selection, malformed flags rejected, unknown-version mechanics returned degraded JSON rather than exit 2. No new WCL network retrieval was performed this round.

## Representative replay

Selected the existing actor-46 window solely because it contains both Purge aura roles and impact damage. No player names or realm information are retained here. Original requested/actual window: [6915943, 6930943] ms, 494/494 participant-source-or-target events, no clipping or display truncation. Original retrieval explicitly terminated after one death-search page and two window pages with consistent Revision 3. Whole-attempt events and complete bundle remain false.

The current WCL command seam replayed the original death and 494 events using synthetic report metadata/HTTP envelopes. Returned events matched exactly. This is offline replay of captured evidence, not replay of the original upstream pagination transcript or a fresh Revision check. Original file SHA-256 remained `40e84a419f1a46e6f67cbd6f8e66ce85257c9dd78ff86c2fd193ac6123dcc007`.

Observed chain (report-relative milliseconds):

| Timestamp | Observation |
| --- | --- |
| 6920940 | 1312967 applydebuff |
| 6925930 | 1312967 removedebuff |
| 6925941 | 1305878 damage, amount 435989; 1316356 applydebuff |
| 6925942 | 1316356 removedebuff; 1305878 damage, amount 351751, overkill 346616 |
| 6925943 | death, killingAbilityGameID 1305878 |

Before: the evidence established two close impact-damage records and a lethal event, but identical localized names could not explain the separate aura IDs.

After: fixed-build Spell text connects the journal-facing Purge 1306086 to impact 1305878, periodic damage 1316357, pre-expiration context 1312967 and periodic aura 1316356. The journal places Purge under a Heroic-associated Serpent's Bite parent. The observed sequence is consistent with those roles. It does not prove that aura removal was natural expiration, identify whose purge hit whom, prove a failed soak, establish spatial overlap or demonstrate that the reviewed build applies. Periodic 1316357 damage is not asserted to have occurred in this selected chain. A Mythic-only Caustic Waves expiration clause was deliberately excluded from Heroic knowledge.

An appropriate conditional follow-up is to inspect spacing and separate aura/impact histories, not assign fault. Leeching venom can itself be an intended mechanic action. Guide advice to finish assigned soaks and then spread is attributed secondary strategy with unknown exact build, not a report diagnosis.

## Actual executions

- `python3 -m unittest discover -s tests -v`: 48 tests passed. The new command-level coverage test failed before knowledge was added, then passed; existing P1, exact/unknown version, unsupported difficulty, source failure and copied-skill regressions remained green. Added a changed-spell-reference check that leaves retained roles unverified. Tests establish interface/data constraints, not mechanic truth.
- `python3 -m compileall -q skills tests` and `git diff --check`: passed. CSV fixtures preserve significant source-cell whitespace via a scoped Git attribute.
- `query ulatek --branch retail --difficulty heroic --verify-sources`: real network recheck returned exit 1 / degraded / context_unknown, with journal, difficulty, Icy Veins and Spell sources all matched. Requested versions remained null. Four source rechecks do not prove live hotfix/report applicability.
- `wow-localization ... spells --input /tmp/wow-death-spells.json`: exit 0 / ok, cache hit; observed IDs 1305878, 1312967 and 1316356 all mapped to zhCN 易爆清除 at source build 12.1.5.69848, build_status not_requested. This was cached name lookup, not a fresh localization network check or automatic report-build match.
- Public source research fetched actual journal/difficulty/Spell/SpellName and guide bodies, then the parent independently inspected the relevant journal, difficulty and Spell rows. Search summaries were not used as evidence. Only selected attributed source excerpts, fingerprints and original paraphrases are retained in the repository; raw bodies and original report artifacts stay under `/tmp`.

## Remaining gaps

Falling Debris and Virulent Spit lack direct Heroic journal associations; generic descriptions and observed Heroic events support bounded investigation, not a general inheritance renderer. Source numerical substitutions, timers, release channel, hotfix state and report build remain unknown. No signal is promoted to a verified detection rule. The other lethal effects and full encounter remain outside the expanded slice. Source redistribution permission remains unresolved; full tables and guide bodies are not bundled. This round is a historical WCL replay plus fresh public-source recheck, not live WCL revalidation or complete raid analysis.
