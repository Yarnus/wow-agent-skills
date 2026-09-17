#!/usr/bin/env python3
"""Resolve game Spell IDs using build-identified Wago Tools zhCN SpellName data."""
import argparse
import csv
import hashlib
import http.client
import os
import tempfile
import io
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

SOURCE = 'https://wago.tools/db2/SpellName/csv'
BUILD = r'\d+\.\d+\.\d+\.\d+'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    spells = commands.add_parser('spells')
    spells.add_argument('ids', nargs='*', type=int)
    spells.add_argument('--input')
    spells.add_argument('--build')
    spells.add_argument('--refresh', action='store_true')
    spells.add_argument('--cache-dir', type=Path, default=Path.home() / '.cache/wow-localization')
    args = parser.parse_args(argv)
    try:
        if bool(args.ids) == bool(args.input) or (args.build and not re.fullmatch(BUILD, args.build)):
            raise ValueError
        items = (json.loads(sys.stdin.read() if args.input == '-' else Path(args.input).read_text(encoding='utf-8'))
                 if args.input else [{'spell_id': i} for i in args.ids])
        if not isinstance(items, list) or not items:
            raise ValueError
        for item in items:
            if (not isinstance(item, dict) or set(item) - {'spell_id', 'original_name'}
                    or type(item.get('spell_id')) is not int or item['spell_id'] <= 0
                    or ('original_name' in item and not isinstance(item['original_name'], str))):
                raise ValueError
    except (OSError, ValueError, UnicodeError):
        print(json.dumps({'status': 'error', 'error': 'invalid_input', 'results': []}))
        return 1
    source = SOURCE + '?' + urllib.parse.urlencode({'locale': 'zhCN', **({'build': args.build} if args.build else {})})
    error = None
    cache_path = args.cache_dir.expanduser() / ((args.build or 'default') + '.zhCN.json')
    cached = None
    try:
        envelope = json.loads(cache_path.read_text(encoding='utf-8'))
        data = envelope['data']
        if (envelope['sha256'] == hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                and data['source'] == source and isinstance(data['build'], str)
                and re.fullmatch(BUILD, data['build']) and isinstance(data['names'], dict) and data['names']
                and all(isinstance(key, str) and re.fullmatch(r'[1-9][0-9]*', key)
                        and isinstance(value, list)
                        and all(isinstance(name, str) and name.strip() for name in value)
                        and len(value) == len(set(value)) for key, value in data['names'].items())):
            cached = data
    except (OSError, ValueError, KeyError, TypeError):
        pass
    data = cached
    cache_status = 'hit' if cached else 'miss'
    if not cached or args.refresh:
        downloaded = False
        temporary = None
        try:
            with urllib.request.urlopen(urllib.request.Request(source, headers={'User-Agent': 'wow-localization/1.0'}), timeout=120) as response:
                filename = response.headers.get_filename()
                match = re.fullmatch(r'SpellName\.(' + BUILD + r')\.csv', filename or '')
                if not match or response.headers.get_content_type() != 'text/csv':
                    raise ValueError
                build = match.group(1)
                names = {}
                reader = csv.DictReader(io.StringIO(response.read().decode('utf-8-sig')), strict=True)
                if reader.fieldnames != ['ID', 'Name_lang']:
                    raise ValueError
                for row in reader:
                    if (None in row or row['Name_lang'] is None or not re.fullmatch(r'[0-9]+', row['ID'])
                            or int(row['ID']) <= 0):
                        raise ValueError
                    spell_id, name = str(int(row['ID'])), row['Name_lang'].strip()
                    if name and name not in names.setdefault(spell_id, []):
                        names[spell_id].append(name)
                if not names:
                    raise ValueError
                data = {'names': names, 'build': build, 'source': source}
            downloaded = True
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=cache_path.parent, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump({'data': data, 'sha256': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}, handle)
            os.replace(temporary, cache_path)
            cache_status = 'refreshed' if args.refresh else 'stored'
        except (OSError, http.client.HTTPException, ValueError, csv.Error) as exc:
            if downloaded:
                error = 'cache_write_failed'
                cache_status = 'write_failed'
            else:
                error = 'invalid_upstream_data' if isinstance(exc, (ValueError, csv.Error)) else 'upstream_error'
                data = cached
                cache_status = 'fallback' if cached else 'miss'
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    names, build = (data['names'], data['build']) if data else ({}, None)
    if data and args.build and args.build != build and not error:
        error = 'build_mismatch'
    results = []
    for item in items:
        spell_id = item['spell_id']
        matches = names.get(str(spell_id), [])
        name = matches[0] if len(matches) == 1 else None
        results.append({'spell_id': spell_id, 'original_name': item.get('original_name'), 'localized_name': name,
                        'display_name': name or item.get('original_name') or str(spell_id),
                        'locale': 'zhCN', 'build': build, 'source': source,
                        'match_status': ('upstream_error' if not data else 'matched' if name else 'ambiguous' if matches else 'missing'),
                        'build_status': 'unknown' if build is None else 'matched' if args.build == build else 'mismatch' if args.build else 'not_requested'})
    print(json.dumps({'status': ('degraded' if data else 'error') if error else 'ok',
                      'error': error, 'cache_status': cache_status, 'results': results}, ensure_ascii=False))
    return 1 if error else 0


if __name__ == '__main__':
    raise SystemExit(main())
