# wow-agent-skills

Composable World of Warcraft skills for agents. Each skill provides one useful capability; the agent decides which capabilities to combine for the user's task.

## Status

Two vertical slices are implemented: `wcl-data` Report Index discovery and participant death-window queries, and independent `wow-localization` batch zhCN Spell ID lookup with build/source metadata and caching. Synthetic regressions and live source checks pass. WCL live multi-page retrieval and live cross-skill report composition remain unverified. Mechanics and the broader first-release scope remain planned.

## Use wcl-data

Python 3.11+ is required; there are no third-party runtime dependencies. Configure `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET` privately in the environment (or the existing `WCL_ID` / `WCL_SECRET` pair), then run:

```bash
python3 skills/wcl-data/scripts/wcl_data.py index REPORT
python3 skills/wcl-data/scripts/wcl_data.py death-window REPORT --fight-id 7 --actor-id 10
```

Install or copy the entire `skills/wcl-data/` directory as one independent skill. It contains its own script and license and does not import repository-root modules or the old project. See [the skill instructions](skills/wcl-data/SKILL.md) for selection, coverage, error semantics, and current limitations.

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
