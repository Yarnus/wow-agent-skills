# Ula'tek death-mechanics source research

## Scope and acquisition

The delegated research phase changed no runtime or tests; the parent retained this source brief in the repository. Read the research skill, `docs/mechanics-source-research.md`, and `skills/wow-mechanics/references/ulatek.json`. **The original report build is unknown. Build 12.1.0.69587 is historical source context, not a report-build assertion.** No private report data or secrets were accessed.

Fetched complete response bodies directly with Python urllib. The six Wago CSV responses were HTTP 200, `text/csv`, with build-specific `Content-Disposition` filenames confirming **actual response build 12.1.0.69587**. Journal/difficulty response dates were 17 September 2026, 10:12–10:13 GMT. These are Blizzard-authored game-data extracts hosted by a third party, not a first-party Blizzard API or verified live server hotfix state.

| Source URL | Local raw body under `/tmp/ulatek-death-research/` | Bytes |
| --- | --- | ---: |
| https://wago.tools/db2/JournalEncounter/csv?build=12.1.0.69587 | `JournalEncounter.csv` | 387374 |
| https://wago.tools/db2/JournalEncounterSection/csv?build=12.1.0.69587 | `JournalEncounterSection.csv` | 3159173 |
| https://wago.tools/db2/JournalSectionXDifficulty/csv?build=12.1.0.69587 | `JournalSectionXDifficulty.csv` | 144744 |
| https://wago.tools/db2/Difficulty/csv?build=12.1.0.69587 | `Difficulty.csv` | 2957 |
| https://wago.tools/db2/Spell/csv?build=12.1.0.69587 | `Spell.csv` | 23704001 |
| https://wago.tools/db2/SpellName/csv?build=12.1.0.69587 | `SpellName.csv` | 11291391 |
| https://www.icy-veins.com/wow/ulatek-raid-guide | `guide.html` | 205674 |

Response headers/URLs are saved beside each body: journal/difficulty use `<Table>.metadata.json`; Spell/SpellName use `<Table>.csv.metadata.json`; guide uses `guide.html.metadata.json`. Derived inspection artifacts: `ulatek-sections.json`, `ulatek-difficulties.json`, `Spell-selected.json`, `Spell-related.json`, `SpellName-selected.json`, `SpellName-related.json`, `guide-text.txt`. These are public-source artifacts only. No search summaries were used as evidence.

## Identity and journal structure

`JournalEncounter.ID=2895`: Name `Ula'tek`, JournalInstanceID `1320`, DungeonEncounterID `3492`, OrderIndex `8`, FirstSectionID `35548`. These ID namespaces are not interchangeable. `Difficulty.ID=15`: Name `Heroic`, InstanceType `2`, FallbackDifficultyID `14`.

All sections below have JournalEncounterID `2895`. Arrow means parent → child, not a combat-event causal link.

| Section path / rows | Spell IDs and exact structural support |
| --- | --- |
| `35561 → 35565 → 36739`, sibling `36177` | Stage One: Fury of the Serpent Mother → `1286860` → `1286885`; sibling `1299526` |
| `36171 → 36309 → 36740`, sibling `36741` | Stage Two: Children of the Doomscale → `1286860` → `1286885`; sibling `1299526` |
| `36323 → 36919 → 36920`, sibling `36921` | Stage Three: Ula'tek's Ascension → `1286860` → `1286885`; sibling `1299526` |
| `36171 → 36284` | Stage Two → `1302982`; no children |
| `36323 → 37031 → 37034` | Stage Three → `1295905` → `1306086`; sibling `37033` uses `1318329` |

The Falling Debris and Virulent Spit sections, their listed ancestors, and the corresponding Rage/Heart sections have DifficultyMask `-1` and **no explicit JournalSectionXDifficulty associations**. This is consistent with shared journal structure, but is not an independently verified generic eligibility/inheritance renderer. Their spell sections have empty BodyText_lang and placeholder titles; the actual descriptions must come from Spell, not invented journal prose.

Purge has a stronger explicit Heroic anchor: `JournalSectionXDifficulty.ID=19141`, DifficultyID `15`, JournalEncounterSectionID `37031`. Its FirstChildSectionID is `37033`; that child's NextSiblingSectionID is `37034`. Section `37034` has ParentSectionID `37031`, SpellID `1306086`, empty body, DifficultyMask `-1`, and no direct difficulty association. Report this as a child of an explicitly Heroic-associated parent, not as its own explicit association.

Control rows for fixtures: Normal/LFR parent `37482` (SpellID `1295905`) has associations `19378→14`, `19379→17`, with Purge child `37484`. Mythic parent `36551` has association `19144→16`, Purge child `36593` also has `18994→16`. Section `36593` says: “On Mythic difficulty, [Caustic Waves] erupt from the player when their aura expires.” Embedded Spell ID `1292403`. **Do not import that Mythic-only effect into Heroic.**

Heroic parent `37031` says: “On Heroic difficulty, [Calcified Corpse] radiates damage to all players.” Embedded link `1306119`, while its corpse child `37033` points at `1318329`. Retain that distinction rather than silently rewriting the source IDs.

## Exact spell-text evidence and mappings

Names below come from `SpellName.ID`; descriptions from `Spell.ID` in the fixed build. `$...` expressions are unresolved source tokens, not computed numerical effects.

### Falling Debris: 1286885, nested under Rage of the Shackled

SpellName identifies `1286885` as **Falling Debris**, `1286860` as **Rage of the Shackled**, and `1299526` as **Venomous Heart**. The task's localized “falling rocks” label is not an English source title.

`1286885.Description_lang`:
> Falling debris drops onto several random destinations, inflicting $s1 Nature damage to players within $a1 yards of the impact locations.

`1286860.Description_lang`:
> Ula'tek rages, inflicting $1307367s1 Nature damage every $t1 sec to all players for $d and causing $@spellname1286885 to impact several random destinations.
>
> Flying into this rage exposes Ula'tek's $@spellname1299526.

Supported: destination-based debris impacts are a component of Rage, repeated in three stage branches. Do not treat localized names or three repeated sections as independent mechanics. No exact radius, damage, periodic cadence, or player avoidability verdict is established here.

### Virulent Spit: 1302982

SpellName identifies **Virulent Spit**, not “Toxic Spit.” `1302982.Description_lang`:
> Ula'tek spits venom at several destinations, inflicting $s1 Nature damage to players within $a1 yards of the impact locations.

Supported: destination-impact Nature damage, journal placement under Stage Two. No fetched evidence makes Spit a child of Rage or Purge. Conversely, a source stage heading alone cannot prove the phase of a report event from an unknown build.

### Volatile Purge: a Serpent's Bite consequence with multiple IDs

`1295905` is **Serpent's Bite**; `1306086`, `1305878`, `1316357`, `1312967`, and `1316356` are all named **Volatile Purge**. The latter four are not direct Ula'tek journal SpellID rows; they resolve through spell text under the journal-facing ID `1306086`.

`1295905.Description_lang` describes fangs/venom, then states:
> Players within $1313420a1 yards may leech the venom to remove it but become infected with $@spellname1306086.

`1306086.Description_lang`:
> Players that leech $@spellname1288879 purge their venom after $1312967d. On expiration, the poison erupts from the affected players, inflicting $1305878s1 Nature damage on impact and an additional $1316357s1 Nature damage every $1316356t1 sec for $1316356d to players near the purge. This effect stacks.
>
> In addition, $@spellname1306086 increases damage taken from $@spellname1315732 by $1312967s1%.

`1315732` is named **Deadly Venom**. `1305878`, `1316357`, `1316356` descriptions are `$@spelldesc1306086`; `1312967` has the same reference followed by a newline.

Additional aura text:
- `1312967.AuraDescription_lang`: `You'll $@spellname1306086 on expiration!\nDamage taken from $@spellname1315732 increased by $s1%.`
- `1316356.AuraDescription_lang`: `Inflicts $1316357s1 Nature damage every $t1 sec.\nDamage taken from $@spellname1315732 increased by $s2%.`

Supported source roles: **1305878 impact**, **1316357 periodic damage**, **1312967 pre-expiration aura context**, **1316356 periodic-damage aura context**. These are explicit tooltip cross-references, stronger than matching names, but not independently verified event-trigger rules. A timed pre-purge aura can be an expected consequence of performing the soak; its presence is not proof of failure. A nearby-impact/periodic effect does not establish who overlapped whom, which source actor caused it, or why someone died.

## Attributed strategy, conflicts, and minimal claims

The fetched Icy Veins body advises avoiding Falling Debris while damaging the heart and, in Phase Three, fully soaking Serpent's Bite in assigned groups **then spreading for Volatile Purge**. It also advises spreading and using remaining defensives on the final platform. These are **Icy Veins strategies**, not primary-source mandates or verified report diagnoses. The guide gives a five-second purge delay; the primary text retains `$1312967d`, so do not publish five seconds as a build-verified fact without resolving relevant duration data. No Virulent Spit passage was found in the extracted guide text; do not fabricate guide attribution for it.

No semantic contradiction was found between these bounded guide passages and the primary text. Differences/unknowns: localized “toxic spit” versus English Virulent Spit; placeholder journal titles/empty bodies; direct difficulty associations versus structural inheritance; guide's exact build unknown; original report build unknown; numerical substitutions and hotfix state unverified. The existing reference's three claims cover other abilities and do not substantiate these new death-related claims.

Recommended minimal output is **three bounded investigation entries, not three independent encounter mechanics**:
1. Falling Debris (`1286885`): a Rage of the Shackled child effect; source says random destination impacts. Attribute avoidance advice to Icy Veins.
2. Virulent Spit (`1302982`): source says destination impacts; journal places it in Stage Two. Any dodge advice without another guide is an author recommendation, not a sourced strategy.
3. Serpent's Bite → Volatile Purge (`1306086` journal anchor; `1305878`, `1316357` damage and `1312967`, `1316356` aura candidates): source distinguishes impact, periodic, and pre-expiration roles; guide recommends completing soaks then spreading.

Keep source facts, strategy, and observed/inferred event signals separate. Preserve each original event ID and event type; do not collapse impact, periodic damage, or auras solely by name. Do not infer a verified detection rule, soak failure, avoidability, death cause, or absent encounter mechanic from a limited death window. Parent can independently reconstruct small fixtures by CSV ID joins using the raw bodies and relevant row IDs above; include difficulty controls, empty journal bodies, parent links, and unresolved spell tokens rather than a synthetic all-Heroic flat list. Do not redistribute full guide bodies or tables; licensing remains unestablished.
