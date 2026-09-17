# Mechanics fixtures

The CSV fixtures retain three short attributed journal excerpts and their difficulty associations, as described in `docs/mechanics-source-research.md`.

`observed-event-shapes.json` is a reduced, de-identified replay fixture informed by the authorized live check in `docs/mechanics-live-verification.md`. It is not raw evidence. Five events retain observed Spell IDs, event types, source-instance values and selected damage fields. Report-local actor IDs are remapped (35 to 10, 86 to 20, 87 to 21), fight ID is changed to 7, and timestamps are synthetic 2000–6000 ms. All player names, realms, coordinates, resources and other fields are omitted. Timing and causal relationships cannot be inferred from this fixture. Tests add synthetic report metadata, death and HTTP pagination; localization responses are also synthetic.
