# Mechanics source investigation and verification

Subsequent [authorized live verification](mechanics-live-verification.md) passed three-skill composition and 42-page retrieval, observed three candidate IDs and confirmed the encounter ID for one report. The implementation-time limitations below are historical; report build and the fourth signal remain unverified.

## Approved scope and interface proposal

Retail 12.1, Heroic Ula'tek (乌拉特克), eighth boss of The Venomous Abyss. Gnarlroot was an exploratory candidate rejected by the user. The implementation is a deliberately partial three-claim snapshot, not a complete encounter guide.

Approved external seam: one standalone Python `query` command accepting an explicit boss, branch, difficulty and patch/build context, returning JSON with separately classified source statements, strategies, inferred event signals, applicability, sources and gaps. No WCL dependency or workflow is required. Proposed tests exercise the command seam and copied-skill execution, replacing only external transport/source files for failure cases. The user approved the command seam before TDD.

## Acquisition checks

Observed HTTP response dates: 17 September 2026. Earlier full-body probes were refused by the fetch tool because DNS returned fake-IP addresses. After the user fixed Clash Verge Rev configuration, full-body retrieval succeeded. Search snippets were not treated as evidence. The delegated researcher failed because its web extensions were unavailable; the parent performed the checks below.

- Official Chinese update notes: https://wow.blizzard.cn/news/24293281/ — readable body acquired. The raid section identifies eight encounters and Ula'tek as the final encounter. This is first-party encounter context, not a full mechanics definition. The extracted body does not explicitly establish the string `12.1` or an exact build. It links to https://wow.blizzard.cn/news/24294062/ for raid details (not yet checked).
- https://www.icy-veins.com/wow/ulatek-raid-guide — readable body acquired (9,397 characters). It explicitly covers Normal/Heroic; changelog says Normal/Heroic strategy added 4 September 2026, guide created 13 August 2026. Some extracted phase sections are empty: extraction is not established as complete. Intermission advice explicitly assigns alternating Heroic Spectral Coils soak groups. This is secondary strategy, not Blizzard-authored mechanics. It is a mutable page with a human changelog, not a build-pinned source.
- https://www.wowhead.com/guide/midnight/raids/venomous-abyss-ulatek-boss-strategy-abilities — extraction reported incomplete content; excluded from claim evidence.

Direct Python HTTPS probes with an identifying `wow-mechanics-research/1.0` User-Agent acquired the following Wago CSV bodies, all HTTP 200 and `text/csv`, each with an attachment filename identifying the actual requested build `12.1.0.69587`:

| Table | Bytes | URL |
| --- | ---: | --- |
| JournalEncounter | 387374 | https://wago.tools/db2/JournalEncounter/csv?build=12.1.0.69587 |
| JournalEncounterSection | 3159173 | https://wago.tools/db2/JournalEncounterSection/csv?build=12.1.0.69587 |
| JournalSectionXDifficulty | 144744 | https://wago.tools/db2/JournalSectionXDifficulty/csv?build=12.1.0.69587 |
| Difficulty | 2957 | https://wago.tools/db2/Difficulty/csv?build=12.1.0.69587 |

Temporary full bodies and response metadata are in `/tmp/wow-mechanics-research/` (local investigation artifacts, not repository dependencies or redistributed datasets).

## Verified data and interpretation limits

JournalEncounter identifies Ula'tek as journal encounter 2895, JournalInstanceID 1320, DungeonEncounterID 3492 and OrderIndex 8. These namespaces must remain distinct; DungeonEncounterID has not been verified against a live WCL report.

Difficulty row 15 names Heroic, instance type 2. JournalSectionXDifficulty explicitly associates section 37254 with difficulty 15 (row 19364). Section 37254, encounter 2895, contains the explicit Heroic statement that Ula'tek casts Soul Constrictor on players who mitigate Spectral Coil's damage; the embedded Spell ID is 1300685 and the section SpellID is 1287265. The same description occurs in section 37042 beneath Heroic-associated parent 37039 (association row 19147).

Other explicit Heroic associations include section 36999 (row 19118): Blightscale Rawlings cast Poisonous Bite, linked Spell ID 1287036; and section 37004 (row 19123): Blightscale Vipers cast Petrifying Sting, linked Spell ID 1303414. These are candidate bounded facts, not a claim that the whole encounter has been resolved.

Many sections have empty bodies and require spell-table text substitution. Text contains difficulty conditionals such as `$[!15`; do not implement a generic renderer or assume every row applies to Heroic. Whole-encounter coverage, spell numerical effects, inherited section eligibility, server hotfix state, release-channel status and live combat-event mappings remain unverified. Linked spell IDs are candidates for investigation, not verified WCL detection rules. A matching source build proves snapshot identity, not that an arbitrary report shares the build or hotfix state.

## Terms and update behavior

- Actual Icy Veins terms URL discovered in page links: https://www.icy-veins.com/terms (body acquired, 5,244 characters). `/terms-of-service` returned 404. Terms describe an AS IS/AS AVAILABLE service, permit modification or discontinuation, and disclaim completeness and reliability. No explicit open-content redistribution license was found in the fetched terms. Accessibility is not redistribution permission. Avoid bundling guide bodies; any curated strategy should be an original concise paraphrase with attribution.
- Blizzard legal FAQ acquired: https://www.blizzard.com/en-us/legal/c1ae32ac-7ff9-4ac3-a03b-fc04b8697010/blizzard-legal-faq . Its fansite answer describes a limited personal, noncommercial license and retention of copyright notices; this is not a blanket open-data license for a public code repository.
- Blizzard website terms body acquired: https://www.blizzard.com/en-gb/legal/511dbf9e-2b2d-4047-8243-4c5c65e0ebf1/terms-of-use-for-blizzard-s-websites . Reviewed in full: its limited personal-use license excludes unauthorized distribution and downloading beyond stated permissions. Application to third-party-hosted game-data extracts is not established; this is not an open-data license.
- Wago Tools home page extraction requires JavaScript; inspected raw HTML exposed no obvious terms link. Wago Tools data redistribution permission remains unknown. Wago.io WeakAura terms and the unrelated industrial WAGO company's terms are not evidence of Wago Tools licensing.
- Wago responses use build-specific attachment names and `Cache-Control: max-age=0`. This verifies acquisition metadata, not immutability or a freshness service-level agreement. Rechecking an explicit build and manually reviewing changes is sufficient for this bounded slice; no source plugin framework is justified.

## Implementation and checks

Selected the simpler offline, manually reviewed snapshot with optional fixed-source rechecks. Bundled entries are original concise paraphrases with row locators and fingerprints; no full tables or guide bodies are distributed. Tests include only the three short journal excerpts needed to exercise the checked claims and their numeric difficulty links, attributed to the Wago URLs above; these excerpts are not relicensed game data. Wago redistribution permissions remain unknown. No claim of legal clearance for wholesale source reuse is made.

The command checks reviewed row fingerprints and guide passages, not arbitrary semantic conflicts across the web. Changed rows produce an unresolved snapshot conflict; missing passages produce a missing-source warning. This conservative check can flag harmless edits; manual review is required. It cannot establish that an otherwise matching guide contains no contradictory text elsewhere.

- Ran incremental red → green command tests for knowledge categories, identity, difficulty, unknown patch/build, retrieval failure, missing source rows, changed source rows, build mismatch and missing local knowledge.
- Initial live verification found a false conflict caused by CSV CRLF versus normalized LF inside quoted text. Added a failing regression, normalized line endings, and reran successfully.
- `python3 -m unittest discover -s tests -v`: 39 tests pass (31 existing, eight mechanics tests including multiple subcases).
- Pre-commit parallel Standards and Spec reviews found two bugs: an empty build caused an uncaught exception, and missing source rows masked conflicts in present rows. Both were reproduced with failing command tests and fixed; empty contexts now return `invalid_context`, and missing plus changed rows disclose both conditions, including changed row IDs. Full regressions, `py_compile` and `git diff --check` pass after correction.
- Copied-skill subprocess succeeds from another directory with WCL variables removed.
- Synthetic composition invokes real WCL and localization command entrypoints, uses an inferred mechanic ID to inspect a participant window and resolve a display name, and verifies serialized evidence is unchanged. The fixture is an interface-composition check, not a verified live Ula'tek report or official localized-name assertion.
- Live `query ulatek --branch retail --difficulty heroic --build 12.1.0.69587 --verify-sources` exits 0 after the newline fix; both Wago selected-row fingerprints and the Icy Veins strategy passage match.

Remaining limitations: three claims only; no full encounter strategy or spell effect renderer; no live WCL signal validation or report composition; no server-hotfix or release-channel guarantee; no automatic updates/cache/retries; no general multi-source semantic conflict resolver. Exact guide build applicability and Wago redistribution terms remain unknown. Existing wcl-data supports only index and participant death windows, not general raid-event queries.
