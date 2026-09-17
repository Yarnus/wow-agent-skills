#!/usr/bin/env python3
"""Query a bounded, manually reviewed Heroic Ula'tek knowledge snapshot."""
import argparse
import csv
import hashlib
import html
import io
import json
import re
import urllib.request
import http.client
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    query = parser.add_subparsers(dest='command', required=True).add_parser('query')
    query.add_argument('boss')
    query.add_argument('--verify-sources', action='store_true')
    query.add_argument('--branch', required=True)
    query.add_argument('--difficulty', required=True)
    context = query.add_mutually_exclusive_group()
    context.add_argument('--build')
    context.add_argument('--patch')
    args = parser.parse_args(argv)
    error = None
    if args.boss.casefold() not in {'ulatek', "ula'tek", '乌拉特克'}:
        error = 'ambiguous_identity' if args.boss in {'8', '8号', 'boss', 'last'} else 'unsupported_identity'
    elif args.branch != 'retail':
        error = 'unsupported_branch'
    elif args.difficulty != 'heroic':
        error = 'difficulty_mismatch'
    elif (args.build is not None or args.patch is not None) and not re.fullmatch(
            r'\d+\.\d+\.\d+\.\d+' if args.build is not None else r'\d+\.\d+(?:\.\d+)?',
            args.build if args.build is not None else args.patch):
        error = 'invalid_context'
    if error:
        print(json.dumps({'status': 'error', 'error': error, 'mechanics': []}))
        return 1
    try:
        result = json.loads((Path(__file__).resolve().parents[1] / 'references/ulatek.json').read_text(encoding='utf-8'))
        if not isinstance(result, dict) or not all(isinstance(result.get(k), list) and result[k] for k in ('sources', 'mechanics', 'knowledge_gaps')):
            raise ValueError
    except (OSError, ValueError):
        print(json.dumps({'status': 'error', 'error': 'knowledge_unavailable', 'mechanics': []}))
        return 1
    matched = args.build == '12.1.0.69587'
    result['applicability'] = {'status': 'snapshot_match' if matched else 'unknown',
                               'requested_build': args.build, 'requested_patch': args.patch,
                               'source_build': '12.1.0.69587', 'branch': args.branch, 'difficulty': args.difficulty}
    result['status'] = 'ok' if matched else 'degraded'
    result['error'] = (None if matched else 'context_unknown'
                       if args.build is None and args.patch is None else 'patch_applicability_unknown')
    if args.verify_sources:
        for source in result['sources']:
            try:
                with urllib.request.urlopen(urllib.request.Request(source['url'], headers={'User-Agent': 'wow-mechanics/1.0'}), timeout=120) as response:
                    body = response.read().decode('utf-8-sig')
                    source['verification'] = 'matched'
                    if 'table' in source:
                        expected = source['table'] + '.' + source['build'] + '.csv'
                        if response.headers.get_filename() != expected:
                            source['verification'] = 'build_mismatch'
                        else:
                            reader = csv.DictReader(io.StringIO(body), strict=True)
                            if not set(source['fields']) <= set(reader.fieldnames or []):
                                raise ValueError
                            rows = {}
                            for row in reader:
                                if row['ID'] in source['row_hashes']:
                                    if row['ID'] in rows or any(row.get(k) is None for k in source['fields']):
                                        raise ValueError
                                    rows[row['ID']] = {k: row[k].replace('\r\n', '\n').replace('\r', '\n') for k in source['fields']}
                            changed = [key for key, row in rows.items()
                                       if hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest() != source['row_hashes'][key]]
                            if changed:
                                source['verification'] = 'conflict'
                                result['conflicts'].append({'source': source['id'], 'kind': 'snapshot_content_changed',
                                                            'row_ids': changed, 'resolution': 'unresolved; manual review required'})
                            if set(rows) != set(source['row_hashes']):
                                source['verification'] = 'missing'
                    else:
                        text = ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', body)).split())
                        if not all(p in text for p in source['required_passages']):
                            source['verification'] = 'missing'
            except (OSError, http.client.HTTPException):
                source['verification'] = 'fetch_failed'
            except (ValueError, csv.Error):
                source['verification'] = 'invalid_content'
        if any(s['verification'] != 'matched' for s in result['sources']):
            result['status'], result['error'] = 'degraded', 'source_verification_failed'
        statuses = {s['id']: s['verification'] for s in result['sources']}
        for mechanic in result['mechanics']:
            for claim in [mechanic['fact'], *mechanic['strategies'], *mechanic['signals']]:
                claim['verification'] = 'source_matched' if all(statuses[s] == 'matched' for s in claim['sources']) else 'unverified'
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
