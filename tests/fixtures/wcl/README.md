# Death classification regression

`death-classification.json` reduces two observed death-event shapes from the authorized local acceptance artifacts. Report identity, player names, realm, resources and unrelated events are omitted. Actor/fight IDs and timestamps are synthetic; the actual `feign: true` marker, absent `feign` on the lethal event, event types and game ability fields are retained.

The fixture exercises classification before candidate numbering through the command interface. It is not a complete report or upstream death page. Boolean false and malformed values are synthetic test cases, not claims about observed upstream encodings. Missing `feign` remains eligible under the existing death-event contract; non-boolean values fail validation rather than being coerced.
