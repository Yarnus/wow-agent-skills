# wow-agent-skills

Composable World of Warcraft skills for agents. Each skill provides one useful capability; the agent decides which capabilities to combine for the user's task.

## Status

The first `wcl-data` vertical slice is implemented: Report Index discovery and participant death-window queries with provenance, pagination, and display metadata. Synthetic-response tests and authorized live Report Index/death-window checks pass. Live multi-page retrieval remains unverified. Other skills and the broader first-release scope remain planned.

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
