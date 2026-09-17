"""Exercise the standalone command with synthetic Wago HTTP responses."""
import contextlib
import importlib.util
import io
import hashlib
import json
import os
from email.message import Message
from pathlib import Path
import tempfile
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/wow-localization/scripts/wow_localization.py"


class Response(io.BytesIO):
    def __init__(self, body="ID,Name_lang\n17,真言术：盾\n116,寒冰箭\n", build="12.1.0.69587"):
        super().__init__(body.encode())
        self.headers = Message()
        self.headers['Content-Type'] = 'text/csv; charset=UTF-8'
        if build:
            self.headers['Content-Disposition'] = f'attachment; filename="SpellName.{build}.csv"'


class CommandTests(unittest.TestCase):
    def invoke(self, args, reply=None):
        spec = importlib.util.spec_from_file_location("wow_localization", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = io.StringIO()
        def http(request, **kwargs):
            self.assertTrue(request.full_url.startswith('https://wago.tools/db2/SpellName/csv?'))
            self.assertIn('locale=zhCN', request.full_url)
            if isinstance(reply, Exception):
                raise reply
            return reply or Response()
        with patch.dict(os.environ, {}, clear=True), patch('urllib.request.urlopen', side_effect=http), contextlib.redirect_stdout(output):
            code = module.main(args)
        return code, json.loads(output.getvalue())

    def test_missing_and_ambiguous_names_preserve_input_order_and_original(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'input.json'
            path.write_text(json.dumps([{'spell_id': 999, 'original_name': 'Unknown'}, {'spell_id': 17}, {'spell_id': 116}]))
            code, result = self.invoke(['spells', '--input', str(path), '--cache-dir', root],
                                      Response('ID,Name_lang\n17,盾\n17,另一名称\n116,寒冰箭\n'))
        self.assertEqual(code, 0)
        self.assertEqual([r['match_status'] for r in result['results']], ['missing', 'ambiguous', 'matched'])
        self.assertEqual([r['display_name'] for r in result['results']], ['Unknown', '17', '寒冰箭'])
        self.assertIsNone(result['results'][0]['localized_name'])
        self.assertEqual(result['results'][0]['spell_id'], 999)
        self.assertEqual(result['results'][0]['original_name'], 'Unknown')
        self.assertEqual(result['results'][2]['build_status'], 'not_requested')

    def test_upstream_failure_is_not_a_missing_mapping(self):
        with tempfile.TemporaryDirectory() as root:
            code, result = self.invoke(['spells', '17', '--cache-dir', root], OSError('private upstream details'))
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['results'][0]['match_status'], 'upstream_error')
        self.assertIsNone(result['results'][0]['build'])
        self.assertEqual(result['results'][0]['display_name'], '17')
        self.assertNotIn('private', json.dumps(result))

    def test_cache_reuse_refresh_failure_and_build_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            args = ['spells', '17', '--cache-dir', root, '--build', '12.1.0.69587']
            self.invoke(args)
            code, cached = self.invoke(args, AssertionError('no network on cache hit'))
            self.assertEqual(code, 0)
            self.assertEqual(cached['cache_status'], 'hit')
            code, stale = self.invoke(args + ['--refresh'], OSError('offline'))
            self.assertEqual(code, 1)
            self.assertEqual(stale['status'], 'degraded')
            self.assertEqual(stale['cache_status'], 'fallback')
            self.assertEqual(stale['results'][0]['localized_name'], '真言术：盾')
            code, other = self.invoke(args[:-1] + ['12.1.5.69848'], OSError('offline'))
            self.assertEqual(other['results'][0]['match_status'], 'upstream_error')

    def test_build_mismatch_is_disclosed_with_actual_build(self):
        with tempfile.TemporaryDirectory() as root:
            code, result = self.invoke(['spells', '17', '--cache-dir', root, '--build', '12.1.5.69848'])
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'degraded')
        self.assertEqual(result['results'][0]['build'], '12.1.0.69587')
        self.assertEqual(result['results'][0]['build_status'], 'mismatch')
        self.assertEqual(result['error'], 'build_mismatch')

    def test_invalid_input_is_rejected_before_network(self):
        for items in ([], {}, [True], [{'spell_id': True}], [{'spell_id': -1}], [{'spell_id': '17'}],
                      [{'spell_id': 1.5}], [{'actor_id': 17}], [{'spell_id': 17, 'original_name': 42}]):
            with self.subTest(items=items), tempfile.TemporaryDirectory() as root:
                path = Path(root) / 'input.json'
                path.write_text(json.dumps(items))
                code, result = self.invoke(['spells', '--input', str(path), '--cache-dir', root], AssertionError('invalid input must not fetch'))
                self.assertEqual(code, 1)
                self.assertEqual(result['error'], 'invalid_input')
                self.assertEqual(result['results'], [])

    def test_malformed_upstream_never_publishes_partial_names_or_poisoned_cache(self):
        for body, build in [('ID,Name_lang\n17,盾\nbad,坏\n', '12.1.0.69587'),
                            ('ID,Name_lang\n17,盾\n0,坏\n', '12.1.0.69587'),
                            ('ID,Name_lang\n17,盾\n', None),
                            ('<html>challenge</html>', '12.1.0.69587'),
                            ('ID,Name_lang\n', '12.1.0.69587'),
                            ('ID,Name_lang\n17,"unfinished', '12.1.0.69587')]:
            with self.subTest(body=body, build=build), tempfile.TemporaryDirectory() as root:
                args = ['spells', '17', '--cache-dir', root]
                code, result = self.invoke(args, Response(body, build))
                self.assertEqual(code, 1)
                self.assertEqual(result['error'], 'invalid_upstream_data')
                self.assertIsNone(result['results'][0]['localized_name'])
                code, recovered = self.invoke(args)
                self.assertEqual(code, 0)
                self.assertEqual(recovered['results'][0]['localized_name'], '真言术：盾')

    def test_cache_write_failure_keeps_downloaded_names(self):
        with tempfile.TemporaryDirectory() as root:
            blocked = Path(root) / 'not-a-directory'
            blocked.write_text('occupied')
            code, result = self.invoke(['spells', '17', '--cache-dir', str(blocked)])
        self.assertEqual(code, 1)
        self.assertEqual(result['error'], 'cache_write_failed')
        self.assertEqual(result['status'], 'degraded')
        self.assertEqual(result['results'][0]['localized_name'], '真言术：盾')

    def test_corrupt_cache_is_replaced_not_used_as_names(self):
        invalid = {'names': {'17': [42]}, 'build': 'unknown', 'source': 'https://wago.tools/db2/SpellName/csv?locale=zhCN'}
        signed_invalid = json.dumps({'data': invalid, 'sha256': hashlib.sha256(json.dumps(invalid, sort_keys=True).encode()).hexdigest()})
        for content in ('[]', '{broken', '{"data": null, "sha256": "bad"}', signed_invalid):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as root:
                args = ['spells', '17', '--cache-dir', root]
                self.invoke(args)
                for path in Path(root).glob('*.json'):
                    path.write_text(content)
                code, result = self.invoke(args)
                self.assertEqual(code, 0)
                self.assertEqual(result['cache_status'], 'stored')
                self.assertEqual(result['results'][0]['localized_name'], '真言术：盾')

    def test_copied_skill_runs_from_stdin_without_wcl_credentials(self):
        with tempfile.TemporaryDirectory() as root:
            cache = str(Path(root) / 'cache')
            self.invoke(['spells', '17', '--cache-dir', cache])
            destination = Path(root) / 'installed'
            shutil.copytree(SCRIPT.parents[1], destination)
            env = {k: v for k, v in os.environ.items() if not k.startswith('WCL_')}
            result = subprocess.run([sys.executable, str(destination / 'scripts/wow_localization.py'),
                                     'spells', '--input', '-', '--cache-dir', cache],
                                    input='[{"spell_id":17,"original_name":"Power Word: Shield"}]',
                                    cwd=root, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['results'][0]['localized_name'], '真言术：盾')

    def test_wcl_game_spell_composition_preserves_original_evidence(self):
        from test_wcl_data import CommandTests as WclCommandTests, report
        death = {'timestamp': 8000, 'type': 'death', 'targetID': 10}
        event = {'timestamp': 7500, 'type': 'damage', 'sourceID': 20, 'targetID': 10, 'abilityGameID': 116}
        def page(events):
            return {'code': 'AbC123', 'revision': 2, 'events': {'data': events, 'nextPageTimestamp': None}}
        code, evidence = WclCommandTests().invoke(
            ['death-window', 'AbC123', '--fight-id', '7', '--actor-id', '10'],
            [report(), {'code': 'AbC123', 'revision': 2}, page([death]), page([event, death]),
             {'code': 'AbC123', 'revision': 2}])
        self.assertEqual(code, 0)
        before = json.dumps(evidence, sort_keys=True)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'spells.json'
            path.write_text(json.dumps([{'spell_id': event['abilityGameID']} for event in evidence['events']
                                        if type(event.get('abilityGameID')) is int and event['abilityGameID'] > 0]))
            code, names = self.invoke(['spells', '--input', str(path), '--cache-dir', root])
        self.assertEqual(code, 0)
        self.assertEqual([r['spell_id'] for r in names['results']], [116])
        self.assertEqual(names['results'][0]['localized_name'], '寒冰箭')
        self.assertEqual(json.dumps(evidence, sort_keys=True), before)

    def test_wago_receives_an_identifying_user_agent(self):
        def wago(request, **kwargs):
            if request.get_header('User-agent') != 'wow-localization/1.0':
                raise OSError('Wago rejects default Python user agent')
            return Response()
        spec = importlib.util.spec_from_file_location('wow_localization', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as root, patch('urllib.request.urlopen', side_effect=wago), contextlib.redirect_stdout(io.StringIO()) as output:
            code = module.main(['spells', '17', '--cache-dir', root])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())['results'][0]['localized_name'], '真言术：盾')

    def test_batch_names_without_wcl_credentials(self):
        with tempfile.TemporaryDirectory() as root:
            code, result = self.invoke(['spells', '17', '116', '--cache-dir', root, '--build', '12.1.0.69587'])
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual([r['localized_name'] for r in result['results']], ['真言术：盾', '寒冰箭'])
        self.assertEqual(result['results'][0], {
            'spell_id': 17, 'original_name': None, 'localized_name': '真言术：盾',
            'display_name': '真言术：盾', 'locale': 'zhCN', 'build': '12.1.0.69587',
            'source': 'https://wago.tools/db2/SpellName/csv?locale=zhCN&build=12.1.0.69587',
            'match_status': 'matched', 'build_status': 'matched'})
