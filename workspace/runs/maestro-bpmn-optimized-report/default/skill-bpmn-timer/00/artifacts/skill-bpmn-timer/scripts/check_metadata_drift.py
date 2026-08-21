#!/usr/bin/env python3
"""
Check package metadata files for drift against a BPMN source file.

Verifies that entry-points.json, bindings_v2.json, operate.json, and
package-descriptor.json are consistent with the given BPMN file.

Usage:
  python3 check_metadata_drift.py --bpmn <file.bpmn> --project-dir <dir>

Args:
  --bpmn         Source .bpmn file
  --project-dir  Directory containing the five metadata JSON files

Exit codes:
  0  All checks passed (no drift)
  1  Drift detected or input error
"""
import argparse
import json
import os
import sys

try:
    import defusedxml.ElementTree as ET
except ImportError:
    print('ERROR: defusedxml required — pip install defusedxml', file=sys.stderr)
    sys.exit(1)

BPMN_NS = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
UIPATH_NS = 'http://uipath.org/schema/bpmn'


def bpmn(tag):
    return f'{{{BPMN_NS}}}{tag}'


def uipath(tag):
    return f'{{{UIPATH_NS}}}{tag}'


def load_json(path, label):
    if not os.path.isfile(path):
        return None, f'MISSING: {label} not found at {path}'
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f'INVALID JSON: {label}: {e}'


def parse_entry_points_from_bpmn(bpmn_path):
    try:
        tree = ET.parse(bpmn_path)
    except Exception as e:
        return None, str(e)

    root = tree.getroot()
    process = root.find(bpmn('process'))
    if process is None:
        return None, 'No bpmn:process element found'

    entry_points = []
    for start in process.findall(bpmn('startEvent')):
        start_id = start.get('id', '')
        ext = start.find(bpmn('extensionElements'))
        if ext is None:
            continue
        ep_elem = ext.find(uipath('entryPointId'))
        if ep_elem is None:
            continue
        ep_id = ep_elem.get('value', '')
        if ep_id:
            entry_points.append((ep_id, start_id))

    return entry_points, None


def main():
    parser = argparse.ArgumentParser(
        description='Check package metadata files for drift against a BPMN source'
    )
    parser.add_argument('--bpmn', required=True, help='Source .bpmn file')
    parser.add_argument('--project-dir', required=True, help='Directory with metadata JSON files')
    args = parser.parse_args()

    if not os.path.isfile(args.bpmn):
        print(f'ERROR: File not found: {args.bpmn}', file=sys.stderr)
        sys.exit(1)

    bpmn_filename = os.path.basename(args.bpmn)
    d = args.project_dir
    failures = []

    entry_points, err = parse_entry_points_from_bpmn(args.bpmn)
    if err:
        print(f'ERROR: {err}', file=sys.stderr)
        sys.exit(1)

    ep_json, err = load_json(os.path.join(d, 'entry-points.json'), 'entry-points.json')
    if err:
        failures.append(err)
    else:
        existing_ids = {ep['id']: ep for ep in ep_json.get('entryPoints', [])}
        for ep_id, start_id in entry_points:
            if ep_id not in existing_ids:
                failures.append(f'entry-points.json: missing entry for entryPointId={ep_id!r}')
            else:
                expected_path = f'/content/{bpmn_filename}#{start_id}'
                actual_path = existing_ids[ep_id].get('filePath', '')
                if actual_path != expected_path:
                    failures.append(
                        f'entry-points.json: id={ep_id!r} filePath={actual_path!r}'
                        f', expected {expected_path!r}'
                    )

    bindings, err = load_json(os.path.join(d, 'bindings_v2.json'), 'bindings_v2.json')
    if err:
        failures.append(err)
    else:
        if bindings.get('version') != '2.0':
            failures.append(
                f'bindings_v2.json: version={bindings.get("version")!r}, expected "2.0"'
            )
        if not isinstance(bindings.get('resources'), list):
            failures.append('bindings_v2.json: "resources" must be an array')

    operate, err = load_json(os.path.join(d, 'operate.json'), 'operate.json')
    if err:
        failures.append(err)
    else:
        actual_main = operate.get('main', '')
        if actual_main != bpmn_filename:
            failures.append(
                f'operate.json: main={actual_main!r}, expected {bpmn_filename!r}'
            )

    descriptor, err = load_json(os.path.join(d, 'package-descriptor.json'), 'package-descriptor.json')
    if err:
        failures.append(err)
    else:
        content = descriptor.get('content', [])
        required = {
            f'content/{bpmn_filename}',
            'content/bindings_v2.json',
            'content/entry-points.json',
            'content/operate.json',
        }
        missing = required - set(content)
        for m in sorted(missing):
            failures.append(f'package-descriptor.json: missing content entry {m!r}')

    if failures:
        for f in failures:
            print(f'DRIFT: {f}')
        sys.exit(1)

    total_checks = 4 + len(entry_points)
    print(f'OK: {total_checks} checks passed, no drift detected')


if __name__ == '__main__':
    main()
