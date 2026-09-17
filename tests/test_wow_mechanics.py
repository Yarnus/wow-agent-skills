"""Command-seam regressions; external source responses are synthetic."""
import contextlib
import csv
from email.message import Message
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/wow-mechanics/scripts/wow_mechanics.py'
ARGS = ['query', 'ulatek', '--branch', 'retail', '--difficulty', 'heroic', '--build', '12.1.0.69587']


class CommandTests(unittest.TestCase):
    def invoke(self, args=ARGS, reply=None):
        spec = importlib.util.spec_from_file_location('wow_mechanics', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.dict(os.environ, {}, clear=True), patch('urllib.request.urlopen', side_effect=reply or AssertionError('offline query must not fetch')), contextlib.redirect_stdout(io.StringIO()) as out:
            code = module.main(args)
        return code, json.loads(out.getvalue())

    def sources(self, mode='ok'):
        def respond(request, **kwargs):
            table = request.full_url.split('/db2/')[-1].split('/')[0]
            if table in {'JournalEncounterSection', 'JournalSectionXDifficulty'}:
                body = (Path(__file__).parent / 'fixtures/mechanics' / (table + '.csv')).read_text()
                if mode == 'crlf':
                    body = body.replace('\n', '\r\n')
                if mode == 'missing' and table == 'JournalEncounterSection':
                    body = body.splitlines()[0] + '\n'
                if mode in {'conflict', 'missing_and_conflict'}:
                    body = body.replace('On Heroic difficulty', 'On Normal difficulty')
                if mode == 'missing_and_conflict' and table == 'JournalEncounterSection':
                    reader = csv.DictReader(io.StringIO(body))
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    writer.writerows(row for row in reader if row['ID'] != '36999')
                    body = output.getvalue()
                headers = Message()
                headers['Content-Type'] = 'text/csv'
                build = '12.1.0.99999' if mode == 'mismatch' else '12.1.0.69587'
                headers['Content-Disposition'] = f'attachment; filename="{table}.{build}.csv"'
            else:
                body = '<p>For Heroic: Team 1 takes 1/3/5 and Team 2 takes 2/4/6.</p>'
                headers = Message()
                headers['Content-Type'] = 'text/html'
            response = io.BytesIO(body.encode())
            response.headers = headers
            return response
        return respond

    def test_source_verification_checks_content_missing_conflicts_and_build(self):
        code, result = self.invoke(ARGS + ['--verify-sources'], self.sources())
        self.assertEqual(code, 0)
        self.assertTrue(all(s['verification'] == 'matched' for s in result['sources']))
        code, result = self.invoke(ARGS + ['--verify-sources'], self.sources('crlf'))
        self.assertEqual(code, 0)
        for mode, expected in [('missing', 'missing'), ('conflict', 'conflict'), ('mismatch', 'build_mismatch')]:
            code, result = self.invoke(ARGS + ['--verify-sources'], self.sources(mode))
            self.assertEqual(code, 1)
            self.assertEqual(result['sources'][0]['verification'], expected)
            self.assertTrue(all(m['fact']['verification'] == 'unverified' for m in result['mechanics']))
            if mode == 'conflict':
                self.assertTrue(result['conflicts'])

    def test_missing_row_does_not_hide_a_conflicting_present_row(self):
        code, result = self.invoke(ARGS + ['--verify-sources'], self.sources('missing_and_conflict'))
        self.assertEqual(code, 1)
        self.assertEqual(result['sources'][0]['verification'], 'missing')
        self.assertTrue(result['conflicts'])
        self.assertEqual(result['conflicts'][0]['source'], 'journal')
        self.assertIn('37254', result['conflicts'][0]['row_ids'])
        self.assertNotIn('36999', result['conflicts'][0]['row_ids'])
        self.assertTrue(all(m['fact']['verification'] == 'unverified' for m in result['mechanics']))

    def test_source_failure_is_not_a_verified_snapshot(self):
        code, result = self.invoke(ARGS + ['--verify-sources'], OSError('private upstream body'))
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'degraded')
        self.assertTrue(all(s['verification'] == 'fetch_failed' for s in result['sources']))
        self.assertNotIn('private upstream', json.dumps(result))
        self.assertTrue(all(m['fact']['verification'] == 'unverified' for m in result['mechanics']))

    def test_empty_context_returns_structured_error(self):
        for flag in ('--build', '--patch'):
            with self.subTest(flag=flag):
                code, result = self.invoke(ARGS[:-2] + [flag, ''])
                self.assertEqual(code, 1)
                self.assertEqual(result['error'], 'invalid_context')
                self.assertEqual(result['mechanics'], [])

    def test_identity_and_applicability_are_not_guessed(self):
        for flag, value, error in [('boss', '8', 'ambiguous_identity'), ('boss', 'other', 'unsupported_identity'),
                                  ('--branch', 'classic', 'unsupported_branch'),
                                  ('--difficulty', 'normal', 'difficulty_mismatch')]:
            args = ARGS.copy()
            args[1 if flag == 'boss' else args.index(flag) + 1] = value
            code, result = self.invoke(args)
            self.assertEqual(code, 1)
            self.assertEqual(result['error'], error)
            self.assertEqual(result['mechanics'], [])
        for context in [['--patch', '12.1'], ['--build', '12.1.0.99999']]:
            code, result = self.invoke(ARGS[:-2] + context)
            self.assertEqual(code, 1)
            self.assertEqual(result['applicability']['status'], 'unknown')
            self.assertEqual(result['status'], 'degraded')
        code, result = self.invoke(ARGS[:-2] + ['--build', 'garbage'])
        self.assertEqual(result['error'], 'invalid_context')

    def test_copied_skill_and_missing_dataset(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / 'skill'
            shutil.copytree(SCRIPT.parents[1], destination)
            command = [sys.executable, str(destination / 'scripts/wow_mechanics.py'), *ARGS]
            env = {k: v for k, v in os.environ.items() if not k.startswith('WCL_')}
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            (destination / 'references/ulatek.json').unlink()
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['error'], 'knowledge_unavailable')

    def test_agent_composition_preserves_wcl_evidence(self):
        from test_wcl_data import CommandTests as WclTests, report
        from test_wow_localization import CommandTests as NameTests, Response
        _, knowledge = self.invoke()
        spell_id = knowledge['mechanics'][0]['signals'][0]['spell_ids'][1]
        death = {'timestamp': 8000, 'type': 'death', 'targetID': 10}
        event = {'timestamp': 7500, 'type': 'applydebuff', 'sourceID': 20, 'targetID': 10, 'abilityGameID': spell_id}
        def page(events):
            return {'code': 'AbC123', 'revision': 2, 'events': {'data': events, 'nextPageTimestamp': None}}
        code, evidence = WclTests().invoke(['death-window', 'AbC123', '--fight-id', '7', '--actor-id', '10'],
            [report(), {'code': 'AbC123', 'revision': 2}, page([death]), page([event, death]), {'code': 'AbC123', 'revision': 2}])
        self.assertEqual(code, 0)
        original = json.dumps(evidence, sort_keys=True)
        matches = [e for e in evidence['events'] if e.get('abilityGameID') == spell_id]
        self.assertEqual(len(matches), 1)
        with tempfile.TemporaryDirectory() as root:
            code, names = NameTests().invoke(['spells', str(spell_id), '--cache-dir', root], Response(f'ID,Name_lang\n{spell_id},Synthetic name\n'))
        self.assertEqual(code, 0)
        self.assertEqual(names['results'][0]['spell_id'], 1300685)
        self.assertEqual(json.dumps(evidence, sort_keys=True), original)

    def test_live_observations_do_not_promote_detection_or_build_applicability(self):
        code, result = self.invoke(ARGS[:-2] + ['--patch', '12.1'])
        self.assertEqual(code, 1)
        self.assertEqual(result['applicability']['status'], 'unknown')
        self.assertNotIn('no live WCL mapping has been verified', ' '.join(result['knowledge_gaps']))
        self.assertTrue(all(not s['verified_detection_rule'] for m in result['mechanics'] for s in m['signals']))

    def test_observed_event_shapes_survive_paginated_three_skill_composition(self):
        from test_wcl_data import CommandTests as WclTests, report
        from test_wow_localization import CommandTests as NameTests, Response
        events = json.loads((Path(__file__).parent / 'fixtures/mechanics/observed-event-shapes.json').read_text())
        metadata = report()
        metadata['masterData']['actors'].append({'id': 21, 'gameID': 261874, 'name': 'Add', 'type': 'NPC'})
        death = {'timestamp': 8000, 'type': 'death', 'targetID': 10}
        def page(items, next_time=None):
            return {'code': 'AbC123', 'revision': 2, 'events': {'data': items, 'nextPageTimestamp': next_time}}
        code, evidence = WclTests().invoke(['death-window', 'AbC123', '--fight-id', '7', '--actor-id', '10'],
            [metadata, {'code': 'AbC123', 'revision': 2}, page([death]),
             page(events[:3], 5000), page(events[3:] + [death]), {'code': 'AbC123', 'revision': 2}])
        self.assertEqual(code, 0)
        self.assertEqual(evidence['events'], events + [death])
        self.assertEqual(evidence['coverage']['event_pagination'], {'pages': 2, 'terminated_explicitly': True})
        self.assertIsNone(evidence['applicability']['build'])
        original = json.dumps(evidence, sort_keys=True)
        _, knowledge = self.invoke(ARGS[:-2] + ['--patch', '12.1'])
        candidates = {i for m in knowledge['mechanics'] for s in m['signals'] for i in s['spell_ids']}
        observed = sorted({e['abilityGameID'] for e in evidence['events'] if e.get('abilityGameID') in candidates})
        self.assertEqual(observed, [1287036, 1287265, 1300685])
        with tempfile.TemporaryDirectory() as root:
            code, names = NameTests().invoke(['spells', *map(str, observed), '--build', '12.1.0.69587', '--cache-dir', root],
                Response('ID,Name_lang\n1287036,剧毒撕咬\n1287265,幽魂盘卷\n1300685,灵魂绞杀者\n'))
        self.assertEqual(code, 0)
        self.assertEqual([r['localized_name'] for r in names['results']], ['剧毒撕咬', '幽魂盘卷', '灵魂绞杀者'])
        self.assertEqual(json.dumps(evidence, sort_keys=True), original)
        self.assertEqual(knowledge['applicability']['status'], 'unknown')

    def test_supported_query_separates_knowledge_categories_without_wcl(self):
        code, result = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result['identity']['journal_encounter_id'], 2895)
        self.assertEqual(result['applicability']['status'], 'snapshot_match')
        self.assertFalse(result['coverage']['complete_encounter'])
        mechanic = result['mechanics'][0]
        self.assertEqual(mechanic['fact']['kind'], 'source_statement')
        self.assertEqual(mechanic['strategies'][0]['kind'], 'strategy')
        self.assertEqual(mechanic['signals'][0]['kind'], 'inferred_signal')
        self.assertFalse(mechanic['signals'][0]['verified_detection_rule'])
        self.assertIn(1300685, mechanic['signals'][0]['spell_ids'])
        self.assertTrue(mechanic['fact']['sources'])
        self.assertTrue(result['knowledge_gaps'])
