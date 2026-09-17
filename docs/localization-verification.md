# Localization slice verification

## Design and reuse

The public interface is one standalone `spells` command returning ordered name records. HTTP retrieval, CSV validation, build identification, ambiguity handling, and snapshot caching stay inside the module. Tests cross the command seam, substitute only external HTTP responses, and use real temporary cache directories. No shared framework or WCL adapter was introduced.

Reviewed `../wcl-report-data/wcl_raid_coach/ability_names.py` and `tests/test_ability_names.py`. Reused the CSV/filename-build/checksum validation ideas under MIT, with attribution in the independent skill license. Its diagnostics, DatasetError, storage helpers, mandatory initialization, and fixed 400,000-row threshold were not imported. Duplicate conflicting names are per-ID ambiguity here rather than a failure of all lookups. The old repository was left unchanged.

## Source checks

Direct HTTPS probes returned HTTP 200 for:

- `https://wago.tools/db2/SpellName/csv?locale=zhCN`: attachment `SpellName.12.1.5.69848.csv`, 10,321,113 bytes, 416,158 parsed data rows, no duplicate IDs in this response.
- `https://wago.tools/db2/SpellName/csv?locale=zhCN&build=12.1.0.69587`: attachment `SpellName.12.1.0.69587.csv`.

The response Date headers identified 17 September 2026; these are observed snapshots, not a release-channel assertion. Columns were `ID,Name_lang`. Example source records: 17 → 真言术：盾, 116 → 寒冰箭, 188443 → 闪电链. Some zhCN records contained English/test names, preserved verbatim.

The first Python CLI live check failed safely with `upstream_error`: Wago returned HTTP 403 for the default Python-urllib User-Agent. A bounded comparison verified HTTP 200 with the descriptive `wow-localization/1.0` User-Agent. A failing command regression was added before that implementation change. Subsequent actual CLI runs succeeded without any `WCL_*` environment variables, from a temporary directory, for default and pinned builds and a pinned cache hit. ID 999999999 returned `missing` without blocking known names.

No external-interface availability assumption or browser-challenge workaround was needed. No additional research workflow was needed once direct probes identified working acquisition and build metadata. Availability and schema stability are not guaranteed, and downloaded game data is not redistributed or relicensed with the code.

## Checks run

- Incremental red → green command tests for batch names, fallback/ambiguity, upstream failure, cache reuse and failed refresh, build mismatch, invalid input, malformed source data, cache-write failure, cache corruption, and identifying User-Agent.
- `python3 -m unittest discover -s tests -v`: 31 tests pass (19 WCL and 12 localization).
- `python3 -m py_compile skills/wow-localization/scripts/wow_localization.py` and `git diff --check` pass.
- Independent copied skill subprocess from a different working directory, no WCL credentials, JSON stdin, real cache populated via synthetic HTTP.
- Composition test executes the real `wcl-data` command over synthetic report/event responses, extracts only positive `abilityGameID` values, resolves names, and checks serialized evidence is unchanged.
- Actual Wago CLI queries without WCL credentials: default build, pinned build, known/missing IDs, and cache hit all exit 0 after the User-Agent fix.

## Remaining limits

- Live report-to-localization composition was not rerun against an authorized WCL report; composition is tested with synthetic WCL HTTP data. Existing WCL live checks remain separately documented.
- Default build may be PTR/test data. No release discovery or automatic Report build inference exists.
- Missing mappings are relative to a validated snapshot. CSV checks detect malformed/truncated syntax, not a syntactically valid table shortened at a row boundary; no authoritative row-count manifest was found or claimed.
- Cache checksum detects accidental corruption, not malicious local modification. Snapshot caches have no TTL, automatic retries, eviction, or cross-process locking; atomic replacement prevents partial-file publication. The entire table is held in memory.
- Failure, ambiguity, and mismatch cases are synthetic regressions, not claims that live Wago produced each condition.
- No NPC names, translation, mechanics, WeakAura parsing, additional locales, or Classic support was added.
