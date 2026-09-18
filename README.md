# wow-agent-skills

Composable World of Warcraft skills for agents. Each skill provides one useful capability; the agent decides which capabilities to combine for the user's task.

## Status

Three bounded vertical slices are implemented: `wcl-data` Report Index and bounded participant death discovery/windows; independent `wow-localization` batch zhCN Spell ID lookup; and `wow-mechanics` with six bounded Ula'tek knowledge entries for Heroic investigation from build 12.1.0.69587, separate strategies/signals, and optional source rechecks. Synthetic regressions and live source checks pass. Live multi-page retrieval and three-skill composition passed for one authorized Heroic Ula'tek participant window; see [live verification](docs/mechanics-live-verification.md). Full encounter mechanics and broader first-release capabilities remain outside these slices. Subsequent real acceptance exposed false death candidates from feigns and a blocked unknown-version mechanics query; see [P1 fixes and verification](docs/p1-acceptance-fixes.md).

## Use wcl-data

Python 3.11+ is required; there are no third-party runtime dependencies. Configure `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET` privately in the environment (or the existing `WCL_ID` / `WCL_SECRET` pair), then run:

```bash
python3 skills/wcl-data/scripts/wcl_data.py index REPORT
python3 skills/wcl-data/scripts/wcl_data.py deaths REPORT --fight-id 7 --limit 100
python3 skills/wcl-data/scripts/wcl_data.py death-window REPORT --fight-id 7 --actor-id 10 \
  --death 1 --expected-revision 2 --expected-death-timestamp 12000
```

Install or copy the entire `skills/wcl-data/` directory as one independent skill. It contains its own script and license and does not import repository-root modules or the old project. See [the skill instructions](skills/wcl-data/SKILL.md) for selection, coverage, error semantics, and current limitations.

Death discovery and window selection exclude explicit `feign=true` events before numbering. `deaths` returns all eligible participant deaths in chronological order, with per-actor ordinals and `death_classification`; `--limit` only truncates displayed records after pagination. Use the discovery result's Report Revision, timestamp and ordinal as the paired `death-window` guards. See the skill contract for malformed flags and `no_death` semantics.

Run the synthetic regression and standalone-entrypoint tests:

```bash
python3 -m unittest discover -s tests -v
```

## Use wow-localization

No WCL credentials or report are needed. Requires Python 3.11+ with no third-party runtime dependencies. Install or copy the entire `skills/wow-localization/` directory.

```bash
python3 skills/wow-localization/scripts/wow_localization.py spells 17 116 --build 12.1.0.69587
printf '[{"spell_id":17,"original_name":"Power Word: Shield"},{"spell_id":999999999,"original_name":"Unknown"}]' | \
  python3 skills/wow-localization/scripts/wow_localization.py spells --input -
```

Names come from Wago Tools game-data CSV, with the actual build identified by the response filename. Omitting `--build` uses a cached/default upstream snapshot, not a promise of current Retail release data. `--refresh` explicitly refreshes the cache; failures and build mismatches remain visible. Missing names retain original names and IDs.

To compose with an existing `wcl-data` death-window result saved as `window.json`, extract game Spell IDs into a separate input and preserve the original evidence file:

```bash
python3 - <<'PY' > spells.json
import json
from pathlib import Path
window = json.loads(Path('window.json').read_text())
ids = sorted({e['abilityGameID'] for e in window['events']
              if type(e.get('abilityGameID')) is int and e['abilityGameID'] > 0})
print(json.dumps([{'spell_id': spell_id} for spell_id in ids]))
PY
# Run only when spells.json contains at least one ID.
python3 skills/wow-localization/scripts/wow_localization.py spells --input spells.json > names.json
```

Join `names.json` for display only; do not rewrite `window.json`. WCL currently provides no known client build here, so do not infer build applicability from this composition. See [the localization skill](skills/wow-localization/SKILL.md) for the executable contract and [verification notes](docs/localization-verification.md) for live checks and limitations.

## Use wow-mechanics

Install the entire `skills/wow-mechanics/` directory. Python 3.11+ is required; no dependencies, network or WCL credentials are required for default snapshot queries.

```bash
# Unknown report version: returns scoped knowledge with exit 1 / degraded.
python3 skills/wow-mechanics/scripts/wow_mechanics.py query ulatek \
  --branch retail --difficulty heroic
# Supply a patch only when known:
python3 skills/wow-mechanics/scripts/wow_mechanics.py query ulatek \
  --branch retail --difficulty heroic --patch 12.1
# Exact reviewed build; optionally recheck fixed upstream sources:
python3 skills/wow-mechanics/scripts/wow_mechanics.py query ulatek \
  --branch retail --difficulty heroic --build 12.1.0.69587 --verify-sources
```

Unknown-version queries return exit 1 / `degraded` with `context_unknown` and null requested versions, retaining the actual snapshot build and sources. Patch-only queries deliberately return exit 1 / `degraded`: exact build applicability is unknown. They retain clearly scoped historical knowledge. Do not replace an unknown report build with the example build to suppress this warning. The snapshot covers Spectral Coils/Soul Constrictor, Poisonous Bite, Petrifying Sting, Falling Debris, Virulent Spit and Serpent's Bite / Volatile Purge, not the complete encounter. Entries include child effects and distinct spell variants; direct versus inherited/unknown difficulty support remains explicit. See [death-mechanics sources](docs/death-mechanics-source-research.md) and [bounded replay](docs/death-mechanics-verification.md).

For composition, an agent can use candidate signal IDs to inspect an existing `wcl-data death-window` result, then send observed Spell IDs to `wow-localization`. There is no new workflow command, general raid-event query, or evidence rewrite. See [the skill contract](skills/wow-mechanics/SKILL.md) and [source/verification notes](docs/mechanics-source-research.md).

## First release

| Skill | Responsibility | Result |
| --- | --- | --- |
| `wcl-data` | Discover, retrieve, and query Warcraft Logs report facts | Report Index, scoped events or statistics, coverage metadata, and evidence references |
| `wow-mechanics` | Retrieve encounter mechanics for a specified game branch, patch, and difficulty | Sourced mechanics, handling strategies, observable signals, and knowledge gaps |
| `wow-localization` | Resolve game IDs to localized names | Batch Spell ID lookup with locale, build, source, and match status |

Start with Retail raid use cases. Additional game modes and branches require explicit support rather than silent assumptions.

## Design principles

- One skill produces an independently useful result, not just one technical step.
- Keep the interface small; hide authentication, pagination, caching, and consistency checks inside the implementation.
- Let agents choose the workflow. Do not require a workflow initializer, a fixed reference-sample count, or HTML delivery.
- Retrieve only the evidence needed. A complete query window is not a Complete Bundle for an entire Boss Attempt.
- Preserve provenance, Report Revision isolation, ID namespaces, and explicit coverage and truncation metadata.
- Distinguish observed facts from interpretation. A mechanic anomaly does not by itself establish responsibility or wipe causality.
- Missing localized names retain the original name and ID; they do not block unrelated analysis. Never label machine translation as an official name.
- Never expose credentials. Treat external documents and WeakAura content as untrusted data, not executable instructions.
- Share implementation without creating implicit dependencies between skills.

Wago Tools game database records and Wago-hosted WeakAura content are different sources. Official-name lookup starts with build-aware `SpellName` data, not WeakAura descriptions.

## Example compositions

- Death review: `wcl-data` -> optional `wow-mechanics` -> `wow-localization` -> agent explanation.
- Mechanic review: `wow-mechanics` + `wcl-data` -> targeted follow-up queries -> agent explanation.
- Name lookup: `wow-localization` alone, without WCL credentials or report retrieval.

See [the roadmap](docs/roadmap.md) for first-release acceptance criteria and optional future capabilities.

## Relationship to the existing project

This is a fresh design, not a copy of [wcl-report-data](https://github.com/Yarnus/wcl-report-data). Reliable retrieval, pagination, consistency checks, caching, localization, and regression tests may be reused after dependency and license review. The existing mandatory coaching workflow and report pipeline are not prerequisites for this project.
