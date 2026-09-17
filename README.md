# wow-agent-skills

Composable World of Warcraft skills for agents. Each skill provides one useful capability; the agent decides which capabilities to combine for the user's task.

## Status

Planning only. No skills or runtime commands are implemented yet.

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
