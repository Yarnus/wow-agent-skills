"""Synthetic WCL HTTP responses exercised through the command interface."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/wcl-data/scripts/wcl_data.py"


def report():
    return {
        "code": "AbC123", "revision": 2, "title": "Synthetic raid", "visibility": "public",
        "startTime": 1700000000000, "endTime": 1700000020000,
        "zone": {"id": 53, "encounters": [{"id": 99}],
                 "difficulties": [{"id": 4, "sizes": [10, 30]}]},
        "masterData": {"gameVersion": 1, "actors": [
            {"id": 10, "gameID": 0, "name": "Alpha", "server": "Realm", "type": "Player", "subType": "Priest"},
            {"id": 20, "gameID": 900, "name": "Boss", "type": "NPC"}]},
        "fights": [{"id": 7, "encounterID": 99, "name": "Boss", "startTime": 1000,
                    "endTime": 20000, "kill": False, "inProgress": False, "difficulty": 4,
                    "keystoneLevel": None, "friendlyPlayers": [10]}],
    }


class Response(io.BytesIO):
    headers = {}


class CommandTests(unittest.TestCase):
    def invoke(self, args, reports, credentials=None):
        spec = importlib.util.spec_from_file_location("wcl_data", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.requests = []
        replies = iter(reports)

        def http(request, **kwargs):
            if request.full_url.endswith("/oauth/token"):
                return Response(b'{"access_token":"secret-token","expires_in":3600}')
            self.requests.append(json.loads(request.data))
            value = next(replies)
            if isinstance(value, Exception):
                raise value
            return Response(json.dumps({"data": {"reportData": {"report": value}}}).encode())

        output = io.StringIO()
        with patch.dict(os.environ, credentials if credentials is not None else {
                "WCL_CLIENT_ID": "secret-id", "WCL_CLIENT_SECRET": "secret-secret"}, clear=True), \
                patch("urllib.request.urlopen", side_effect=http), contextlib.redirect_stdout(output):
            status = module.main(args)
        self.assertNotIn("secret-", output.getvalue())
        return status, json.loads(output.getvalue())

    def test_deaths_discovers_all_participant_deaths_once_and_truncates_display(self):
        data = report()
        data["masterData"]["actors"].append({
            "id": 11, "gameID": 0, "name": "Beta", "server": "Realm",
            "type": "Player", "subType": "Mage"})
        data["fights"][0]["friendlyPlayers"] = [10, 11]
        revision = {"code": "AbC123", "revision": 2}
        def page(events, cursor):
            return revision | {"events": {"data": events, "nextPageTimestamp": cursor}}
        events = [
            {"timestamp": 8000, "type": "death", "targetID": 10, "feign": True},
            {"timestamp": 9000, "type": "death", "targetID": 11, "feign": False},
            {"timestamp": 10000, "type": "death", "targetID": 10},
            {"timestamp": 11000, "type": "death", "targetID": 10, "feign": False},
            {"timestamp": 12000, "type": "death", "targetID": 20},
            {"timestamp": 13000, "type": "death", "targetID": 11, "feign": False},
        ]
        status, result = self.invoke(
            ["deaths", "AbC123", "--fight-id", "7", "--limit", "2"],
            [data, revision, page(events[:3], 10500), page(events[3:], None), revision])
        self.assertEqual(status, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["identity"], {
            "report_code": "AbC123", "report_revision": 2, "fight_id": 7})
        self.assertEqual(result["attempt"]["participants"], [
            {"actor_id": 10, "name": "Alpha", "server": "Realm", "class": "Priest"},
            {"actor_id": 11, "name": "Beta", "server": "Realm", "class": "Mage"},
        ])
        self.assertEqual(result["deaths"], [
            {"actor_id": 11, "death": 1, "timestamp": 9000},
            {"actor_id": 10, "death": 1, "timestamp": 10000},
        ])
        self.assertEqual(result["death_classification"], {
            "candidate_count": 4, "excluded_feign_count": 1,
            "missing_feign_count": 1, "policy": "exclude_explicit_true"})
        self.assertEqual(result["display"], {"matched": 4, "returned": 2, "truncated": True})
        self.assertEqual(result["coverage"]["scope"], "participant_deaths")
        self.assertTrue(result["coverage"]["query_complete"])
        self.assertEqual(result["coverage"]["death_pagination"], {
            "pages": 2, "terminated_explicitly": True})
        self.assertFalse(result["coverage"]["whole_attempt_events"])
        self.assertFalse(result["coverage"]["complete_bundle"])
        death_requests = [r for r in self.requests if "filterExpression" in r["variables"]]
        self.assertEqual(len(death_requests), 2)
        self.assertEqual({r["variables"]["filterExpression"] for r in death_requests}, {"type = 'death'"})

    def test_deaths_reports_no_death_after_filtering_explicit_feigns(self):
        revision = {"code": "AbC123", "revision": 2}
        page = revision | {"events": {"data": [
            {"timestamp": 8000, "type": "death", "targetID": 10, "feign": True}],
            "nextPageTimestamp": None}}
        status, result = self.invoke(
            ["deaths", "AbC123", "--fight-id", "7"],
            [report(), revision, page, revision])
        self.assertEqual(status, 0)
        self.assertEqual(result["status"], "no_death")
        self.assertEqual(result["deaths"], [])
        self.assertEqual(result["death_classification"], {
            "candidate_count": 0, "excluded_feign_count": 1,
            "missing_feign_count": 0, "policy": "exclude_explicit_true"})
        self.assertEqual(result["display"], {"matched": 0, "returned": 0, "truncated": False})
        self.assertTrue(result["coverage"]["query_complete"])

    def test_deaths_rejects_unsupported_fight_and_invalid_upstream_death_fields(self):
        for extra in [["--fight-id", "99"], ["--fight-id", "7", "--limit", "-1"]]:
            with self.subTest(extra=extra):
                status, result = self.invoke(["deaths", "AbC123"] + extra, [report(),
                    {"code": "AbC123", "revision": 2}])
                self.assertEqual(status, 1)
                self.assertEqual(result["status"], "error")
                self.assertFalse(result["coverage"]["query_complete"])
        revision = {"code": "AbC123", "revision": 2}
        def page(event):
            return revision | {"events": {"data": [event], "nextPageTimestamp": None}}
        for field, value in [("targetID", "10"), ("targetID", True), ("targetID", None),
                             ("feign", "true"), ("feign", 1), ("feign", None)]:
            with self.subTest(field=field, value=value):
                event = {"timestamp": 8000, "type": "death", "targetID": 10}
                event[field] = value
                status, result = self.invoke(
                    ["deaths", "AbC123", "--fight-id", "7"],
                    [report(), revision, page(event)])
                self.assertEqual(status, 1)
                self.assertEqual(result["status"], "error")
                self.assertNotIn("deaths", result)
                self.assertFalse(result["coverage"]["query_complete"])

    def test_deaths_rejects_revision_changes_during_and_after_paginated_search(self):
        revision = {"code": "AbC123", "revision": 2}
        changed = {"code": "AbC123", "revision": 3}
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        page = revision | {"events": {"data": [death], "nextPageTimestamp": None}}
        for replies in [
            [report(), revision, page | {"revision": 3}],
            [report(), revision, page, changed],
        ]:
            with self.subTest(replies=replies):
                status, result = self.invoke(
                    ["deaths", "AbC123", "--fight-id", "7"], replies)
                self.assertEqual(status, 1)
                self.assertIn("Revision", result["error"])
                self.assertNotIn("deaths", result)
                self.assertFalse(result["coverage"]["query_complete"])

    def test_fractional_discovery_timestamp_round_trips_into_guarded_window(self):
        revision = {"code": "AbC123", "revision": 2}
        death = {"timestamp": 8000.5, "type": "death", "targetID": 10}
        page = revision | {"events": {"data": [death], "nextPageTimestamp": None}}
        status, discovery = self.invoke(
            ["deaths", "AbC123", "--fight-id", "7"],
            [report(), revision, page, revision])
        self.assertEqual(status, 0)
        selected = discovery["deaths"][0]
        self.assertEqual(selected["timestamp"], 8000.5)
        identity = discovery["identity"]
        status, window = self.invoke(
            ["death-window", identity["report_code"], "--fight-id", str(identity["fight_id"]),
             "--actor-id", str(selected["actor_id"]), "--death", str(selected["death"]),
             "--expected-revision", str(identity["report_revision"]),
             "--expected-death-timestamp", str(selected["timestamp"])],
            [report(), revision, page, revision, page, revision])
        self.assertEqual(status, 0)
        self.assertEqual(window["status"], "ok")
        self.assertEqual(window["death"], death)
        self.assertEqual(window["events"], [death])

    def test_guard_syntax_and_values_are_rejected_without_network_requests(self):
        base = ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"]
        for extra in [
            ["--expected-revision", "2"],
            ["--expected-death-timestamp", "8000"],
            ["--expected-revision", "2", "--expected-death-timestamp", "8000"],
            ["--death", "1", "--expected-revision", "0", "--expected-death-timestamp", "8000"],
            ["--death", "1", "--expected-revision", "2", "--expected-death-timestamp", "-1"],
        ]:
            with self.subTest(extra=extra):
                status, result = self.invoke(base + extra, [])
                self.assertEqual(status, 1)
                self.assertEqual(result["status"], "error")
                self.assertEqual(self.requests, [])

    def test_guard_rejects_nonfinite_and_negative_fractional_timestamps_before_network(self):
        for timestamp in ["nan", "inf", "-inf", "1e999", "-0.5"]:
            with self.subTest(timestamp=timestamp):
                status, result = self.invoke(
                    ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10",
                     "--death", "1", "--expected-revision", "2",
                     "--expected-death-timestamp=" + timestamp], [])
                self.assertEqual(status, 1)
                self.assertEqual(result["status"], "error")
                self.assertIn("timestamp", result["error"])
                self.assertEqual(self.requests, [])

    def test_guarded_window_rejects_revision_mismatch_before_death_search(self):
        revision = {"code": "AbC123", "revision": 2}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--death", "1",
             "--expected-revision", "3", "--expected-death-timestamp", "8000"],
            [report(), revision])
        self.assertEqual(status, 1)
        self.assertIn("Revision", result["error"])
        self.assertEqual([r for r in self.requests if "filterExpression" in r["variables"]], [])

    def test_guarded_window_rejects_stale_timestamp_before_event_window_and_never_falls_back(self):
        revision = {"code": "AbC123", "revision": 2}
        def page(events):
            return revision | {"events": {"data": events, "nextPageTimestamp": None}}
        candidates = [
            {"timestamp": 8000, "type": "death", "targetID": 10},
            {"timestamp": 12000, "type": "death", "targetID": 10},
        ]
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--death", "1",
             "--expected-revision", "2", "--expected-death-timestamp", "12000"],
            [report(), revision, page(candidates), revision])
        self.assertEqual(status, 1)
        self.assertIn("timestamp", result["error"])
        self.assertEqual([r for r in self.requests if "filterExpression" in r["variables"]], [
            self.requests[2]])

    def test_guarded_window_rejects_missing_candidate_without_fallback(self):
        revision = {"code": "AbC123", "revision": 2}
        page = revision | {"events": {"data": [], "nextPageTimestamp": None}}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--death", "1",
             "--expected-revision", "2", "--expected-death-timestamp", "8000"],
            [report(), revision, page, revision])
        self.assertEqual(status, 1)
        self.assertIn("ordinal", result["error"])
        self.assertNotIn("events", result)

    def test_guarded_window_checks_revision_between_discovery_and_window(self):
        revision = {"code": "AbC123", "revision": 2}
        changed = {"code": "AbC123", "revision": 3}
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        page = revision | {"events": {"data": [death], "nextPageTimestamp": None}}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--death", "1",
             "--expected-revision", "2", "--expected-death-timestamp", "8000"],
            [report(), revision, page, changed])
        self.assertEqual(status, 1)
        self.assertIn("Revision", result["error"])
        self.assertEqual([r for r in self.requests if "filterExpression" in r["variables"]], [
            self.requests[2]])

    def test_guarded_window_uses_the_discovered_identity_and_timestamp(self):
        revision = {"code": "AbC123", "revision": 2}
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        page = revision | {"events": {"data": [death], "nextPageTimestamp": None}}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--death", "1",
             "--expected-revision", "2", "--expected-death-timestamp", "8000"],
            [report(), revision, page, revision, page, revision])
        self.assertEqual(status, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["identity"]["report_revision"], 2)
        self.assertEqual(result["death"]["timestamp"], 8000)
        self.assertEqual(result["events"], [death])

    def test_observed_feign_is_excluded_before_automatic_death_selection(self):
        deaths = json.loads((Path(__file__).parent / 'fixtures/wcl/death-classification.json').read_text())
        def page(events):
            return {'code': 'AbC123', 'revision': 2, 'events': {'data': events, 'nextPageTimestamp': None}}
        status, result = self.invoke(
            ['death-window', 'AbC123', '--fight-id', '7', '--actor-id', '10'],
            [report(), {'code': 'AbC123', 'revision': 2}, page(deaths),
             page(deaths), {'code': 'AbC123', 'revision': 2}])
        self.assertEqual(status, 0)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['deaths'], [{'death': 1, 'timestamp': 12000}])
        self.assertEqual(result['death'], deaths[1])
        self.assertEqual(result['death_classification'], {
            'candidate_count': 1, 'excluded_feign_count': 1,
            'missing_feign_count': 1, 'policy': 'exclude_explicit_true'})
        self.assertEqual(result['events'], deaths)

    def test_feign_classification_selection_and_invalid_fields(self):
        first = {'timestamp': 8000, 'type': 'death', 'targetID': 10}
        fake = first | {'timestamp': 10000, 'feign': True}
        second = first | {'timestamp': 12000, 'feign': False}
        revision = {'code': 'AbC123', 'revision': 2}
        def page(events):
            return revision | {'events': {'data': events, 'nextPageTimestamp': None}}
        args = ['death-window', 'AbC123', '--fight-id', '7', '--actor-id', '10']
        code, result = self.invoke(args, [report(), revision, page([fake]), revision])
        self.assertEqual((code, result['status']), (0, 'no_death'))
        self.assertEqual(result['deaths'], [])
        self.assertEqual(result['death_classification']['excluded_feign_count'], 1)
        self.assertEqual(result['death_classification']['candidate_count'], 0)
        for extra, expected in [([], 'needs_selection'), (['--death', '2'], 'ok')]:
            replies = [report(), revision, page([first, fake, second])]
            if extra:
                replies.append(page([first, fake, second]))
            code, result = self.invoke(args + extra, replies + [revision])
            self.assertEqual((code, result['status']), (0, expected))
            self.assertEqual(result['deaths'], [{'death': 1, 'timestamp': 8000},
                                                {'death': 2, 'timestamp': 12000}])
            self.assertEqual(result['death_classification']['missing_feign_count'], 1)
            if extra:
                self.assertEqual(result['death'], second)
        for value in [None, 0, 1, 'true', 'false', [], {}]:
            for stage in ['search', 'window']:
                with self.subTest(value=value, stage=stage):
                    malformed = first | {'feign': value}
                    replies = [report(), revision, page([malformed]), page([malformed])]
                    if stage == 'window':
                        replies = [report(), revision, page([first]), page([malformed])]
                    code, result = self.invoke(args, replies + [revision])
                    self.assertEqual((code, result['status']), (1, 'error'))
                    self.assertIn('feign', result['error'])
                    self.assertNotIn('deaths', result)
                    self.assertFalse(result['coverage']['query_complete'])

    def test_window_feign_cannot_substitute_for_selected_death(self):
        death = {'timestamp': 8000, 'type': 'death', 'targetID': 10}
        revision = {'code': 'AbC123', 'revision': 2}
        def page(event):
            return revision | {'events': {'data': [event], 'nextPageTimestamp': None}}
        code, result = self.invoke(
            ['death-window', 'AbC123', '--fight-id', '7', '--actor-id', '10'],
            [report(), revision, page(death), page(death | {'feign': True}), revision])
        self.assertEqual(code, 1)
        self.assertFalse(result['coverage']['query_complete'])

    def test_index_lists_only_completed_raid_attempts_and_their_players(self):
        data = report()
        data["fights"] += [data["fights"][0] | {"id": 8, "encounterID": 0},
                           data["fights"][0] | {"id": 9, "inProgress": True}]
        status, result = self.invoke(["index", "https://www.warcraftlogs.com/reports/AbC123"],
                                     [data, {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        self.assertEqual([f["fight_id"] for f in result["attempts"]], [7])
        self.assertEqual(result["attempts"][0]["participants"][0]["actor_id"], 10)
        self.assertEqual(result["identity"], {"report_code": "AbC123", "report_revision": 2})
        self.assertEqual(result["source"]["time_basis"], "report_relative_ms")
        self.assertFalse(result["coverage"]["whole_attempt_events"])
        self.assertFalse(result["display"]["truncated"])

    def test_malformed_npc_game_ids_are_not_published_as_identities(self):
        for game_id in ("unknown", True, -5, 1.5):
            with self.subTest(game_id=game_id):
                data = report()
                data["masterData"]["actors"][1]["gameID"] = game_id
                status, result = self.invoke(["index", "AbC123"], [data, {"code": "AbC123", "revision": 2}])
                self.assertEqual(status, 1)
                self.assertNotIn("actors", result)

    def test_window_missing_known_selected_death_is_inconsistent(self):
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"],
            [report(), {"code": "AbC123", "revision": 2},
             {"code": "AbC123", "revision": 2, "events": {"data": [death], "nextPageTimestamp": None}},
             {"code": "AbC123", "revision": 2, "events": {"data": [], "nextPageTimestamp": None}},
             {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 1)
        self.assertFalse(result["coverage"]["query_complete"])

    def test_malformed_event_actor_ids_cannot_be_filtered_into_complete_results(self):
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        def page(event):
            return {"code": "AbC123", "revision": 2, "events": {"data": [event], "nextPageTimestamp": None}}
        for field, value in [("targetID", "10"), ("targetID", True), ("targetID", None), ("sourceID", 10.0)]:
            for stage in ("death_search", "window"):
                with self.subTest(field=field, value=value, stage=stage):
                    malformed = death | {field: value}
                    replies = [report(), {"code": "AbC123", "revision": 2}]
                    replies += [page(malformed)] if stage == "death_search" else [page(death), page(malformed)]
                    replies += [{"code": "AbC123", "revision": 2}]
                    status, result = self.invoke(
                        ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"], replies)
                    self.assertEqual(status, 1)
                    self.assertFalse(result["coverage"]["query_complete"])

    def test_actor_selection_uses_returned_report_ids_not_expression_ids(self):
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        other = {"timestamp": 7500, "type": "death", "targetID": 20}
        def page(events):
            return {"code": "AbC123", "revision": 2, "events": {"data": events, "nextPageTimestamp": None}}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"],
            [report(), {"code": "AbC123", "revision": 2}, page([other, death]),
             page([other, death]), {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        self.assertEqual(result["events"], [death])
        self.assertEqual(result["coverage"]["upstream_window_scope"], "all_actors")
        self.assertEqual(result["display"]["matched"], 1)

    def test_flexible_raid_difficulty_with_empty_sizes_is_included(self):
        data = report()
        data["zone"]["difficulties"] = [{"id": 5, "sizes": [20]}, {"id": 4, "sizes": []}]
        status, result = self.invoke(["index", "AbC123"], [data, {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        self.assertEqual([f["fight_id"] for f in result["attempts"]], [7])

    def test_existing_environment_credential_names_are_supported(self):
        status, result = self.invoke(["index", "AbC123"], [report(), {"code": "AbC123", "revision": 2}],
                                     {"WCL_ID": "secret-id", "WCL_SECRET": "secret-secret"})
        self.assertEqual(status, 0)
        self.assertEqual(result["status"], "ok")

    def test_chinese_region_report_url_is_accepted(self):
        status, result = self.invoke(["index", "https://cn.warcraftlogs.com/reports/AbC123?fight=2&type=damage-done"],
                                     [report(), {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        self.assertEqual(result["identity"]["report_code"], "AbC123")

    def test_environment_actor_is_preserved_without_inventing_npc_identity(self):
        data = report()
        data["masterData"]["actors"].append({"id": -1, "gameID": 0, "name": "Environment", "type": "NPC"})
        status, result = self.invoke(["index", "AbC123"], [data, {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        environment = next(a for a in result["actors"] if a["actor_id"] == -1)
        self.assertEqual(environment["name"], "Environment")
        self.assertIsNone(environment["npc_id"])

    def test_nonfinite_payload_fields_cannot_escape_as_invalid_json(self):
        data = report()
        data["masterData"]["actors"][1]["gameID"] = float("nan")
        status, result = self.invoke(["index", "AbC123"], [data, {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 1)
        self.assertEqual(result["status"], "error")

    def test_rate_limit_is_explicit_without_leaking_upstream_body(self):
        error = HTTPError("https://www.warcraftlogs.com/api/v2/client", 429, "secret-token",
                          {"Retry-After": "30"}, io.BytesIO(b"secret-secret"))
        status, result = self.invoke(["index", "AbC123"], [error])
        self.assertEqual(status, 1)
        self.assertIn("rate limit", result["error"])

    def test_independent_script_entrypoint_help_and_missing_credentials(self):
        with tempfile.TemporaryDirectory() as cwd:
            env = {k: v for k, v in os.environ.items() if not k.startswith("WCL_")}
            help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], cwd=cwd,
                                         env=env, capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0)
            self.assertIn("death-window", help_result.stdout)
            missing = subprocess.run([sys.executable, str(SCRIPT), "index", "AbC123"], cwd=cwd,
                                     env=env, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            self.assertEqual(json.loads(missing.stdout)["status"], "error")
            self.assertEqual(missing.stderr, "")

    def test_revision_changes_at_each_stage_prevent_success(self):
        death = {"code": "AbC123", "revision": 2, "events": {
            "data": [{"timestamp": 8000, "type": "death", "targetID": 10}], "nextPageTimestamp": None}}
        final = {"code": "AbC123", "revision": 2}
        replies = [report(), final, death, death, final]
        for position in [1, 2, 3, 4]:
            changed = list(replies)
            changed[position] = replies[position] | {"revision": 3}
            with self.subTest(position=position):
                status, result = self.invoke(
                    ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"], changed)
                self.assertEqual(status, 1)
                self.assertNotIn("events", result)

    def test_selected_second_death_has_resolvable_event_actor_identities(self):
        deaths = [{"timestamp": 8000, "type": "death", "targetID": 10},
                  {"timestamp": 19000, "type": "death", "targetID": 10}]
        event = {"timestamp": 18500, "type": "damage", "sourceID": 20, "targetID": 10, "abilityGameID": 123}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--death", "2"],
            [report(), {"code": "AbC123", "revision": 2},
             {"code": "AbC123", "revision": 2, "events": {"data": deaths, "nextPageTimestamp": None}},
             {"code": "AbC123", "revision": 2, "events": {"data": [event, deaths[1]], "nextPageTimestamp": None}},
             {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        self.assertEqual(result["death"], deaths[1])
        self.assertEqual(result["coverage"]["actual_window_ms"], [9000, 20000])
        boss = next(a for a in result["actors"] if a["actor_id"] == 20)
        self.assertEqual(boss["npc_id"], 900)
        self.assertEqual(boss["name"], "Boss")

    def test_invalid_selectors_and_malformed_identity_are_rejected(self):
        args = ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"]
        for extra in [["--actor-id", "20"], ["--fight-id", "99"], ["--death", "0"],
                      ["--before-ms", "-1"], ["--limit", "-1"]]:
            with self.subTest(extra=extra):
                status, result = self.invoke(args + extra, [report(), {"code": "AbC123", "revision": 2}])
                self.assertEqual(status, 1)
                self.assertEqual(result["status"], "error")
        for mutate in [lambda r: r["masterData"].update(actors=[]),
                       lambda r: r["fights"][0].update(startTime=float("nan")),
                       lambda r: r["fights"][0].update(id=True),
                       lambda r: r["masterData"]["actors"].append(r["masterData"]["actors"][0]),
                       lambda r: r.update(revision=None)]:
            data = report()
            mutate(data)
            with self.subTest(data=data):
                status, result = self.invoke(["index", "AbC123"], [data, {"code": "AbC123", "revision": 2}])
                self.assertEqual(status, 1)
                self.assertNotIn("attempts", result)

    def test_upstream_failure_after_a_page_returns_only_a_safe_error(self):
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"],
            [report(), {"code": "AbC123", "revision": 2},
             {"code": "AbC123", "revision": 2, "events": {
                 "data": [{"timestamp": 8000, "type": "death", "targetID": 10}], "nextPageTimestamp": 9000}},
             OSError("secret-token")])
        self.assertEqual(status, 1)
        self.assertFalse(result["coverage"]["query_complete"])
        self.assertNotIn("events", result)
        self.assertNotIn("deaths", result)

    def test_invalid_pagination_never_publishes_partial_evidence(self):
        for page in [{"data": []}, {"data": [], "nextPageTimestamp": 1000},
                     {"data": [], "nextPageTimestamp": 21000},
                     {"data": [], "nextPageTimestamp": float("nan")},
                     {"data": [], "nextPageTimestamp": True},
                     {"data": "invalid", "nextPageTimestamp": None},
                     {"data": [{"timestamp": 999, "type": "death", "targetID": 10}], "nextPageTimestamp": None},
                     {"data": [{"timestamp": 8000, "type": "cast", "targetID": 10}], "nextPageTimestamp": None}]:
            with self.subTest(page=page):
                status, result = self.invoke(
                    ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"],
                    [report(), {"code": "AbC123", "revision": 2},
                     {"code": "AbC123", "revision": 2, "events": page}])
                self.assertEqual(status, 1)
                self.assertEqual(result["status"], "error")
                self.assertFalse(result["coverage"]["query_complete"])
                self.assertNotIn("events", result)

    def test_multiple_deaths_require_selection_and_no_death_is_explicit(self):
        for deaths, expected in [([], "no_death"),
                                 ([{"timestamp": 8000, "type": "death", "targetID": 10},
                                   {"timestamp": 12000, "type": "death", "targetID": 10}], "needs_selection")]:
            with self.subTest(expected=expected):
                status, result = self.invoke(
                    ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10"],
                    [report(), {"code": "AbC123", "revision": 2},
                     {"code": "AbC123", "revision": 2, "events": {"data": deaths, "nextPageTimestamp": None}},
                     {"code": "AbC123", "revision": 2}])
                self.assertEqual(status, 0)
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["deaths"], [{"death": i + 1, "timestamp": d["timestamp"]}
                                                    for i, d in enumerate(deaths)])
                self.assertFalse(result["coverage"]["query_complete"])
                self.assertTrue(result["coverage"]["death_pagination"]["terminated_explicitly"])
                self.assertNotIn("events", result)

    def test_death_window_collects_all_pages_before_display_truncation(self):
        death = {"timestamp": 8000, "type": "death", "targetID": 10}
        damage = {"timestamp": 7500, "type": "damage", "sourceID": 20, "targetID": 10, "abilityGameID": 123}
        cast = {"timestamp": 8100, "type": "cast", "sourceID": 10, "targetID": 20, "abilityGameID": 456}
        page = lambda events, cursor: {"code": "AbC123", "revision": 2,
                                       "events": {"data": events, "nextPageTimestamp": cursor}}
        status, result = self.invoke(
            ["death-window", "AbC123", "--fight-id", "7", "--actor-id", "10", "--limit", "1"],
            [report(), {"code": "AbC123", "revision": 2}, page([death], None),
             page([damage, death], 8100), page([cast], None), {"code": "AbC123", "revision": 2}])
        self.assertEqual(status, 0)
        self.assertEqual(result["events"], [damage])
        self.assertEqual(result["display"], {"matched": 3, "returned": 1, "truncated": True})
        self.assertEqual(result["coverage"]["actual_window_ms"], [1000, 13000])
        self.assertEqual(result["coverage"]["requested_window_ms"], [-2000, 13000])
        self.assertTrue(result["coverage"]["query_complete"])
        self.assertEqual(result["coverage"]["event_pagination"]["pages"], 2)
        self.assertFalse(result["coverage"]["whole_attempt_events"])
        event_requests = [r for r in self.requests if "filterExpression" in r["variables"]]
        self.assertEqual(event_requests[0]["variables"]["filterExpression"], "type = 'death'")
        self.assertEqual(event_requests[1]["variables"]["filterExpression"], "")
        self.assertEqual(event_requests[2]["variables"]["endTime"], 13000)


if __name__ == "__main__":
    unittest.main()
