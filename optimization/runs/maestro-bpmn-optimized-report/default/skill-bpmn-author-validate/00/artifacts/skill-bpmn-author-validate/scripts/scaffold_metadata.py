#!/usr/bin/env python3
"""
Scaffold the five package metadata files from a BPMN source file.

Reads root start events (uipath:entryPointId) and variables from the BPMN,
then writes project.uiproj, operate.json, entry-points.json, bindings_v2.json,
and package-descriptor.json into --out-dir.

Usage:
  python3 scaffold_metadata.py --bpmn <file.bpmn> --out-dir <dir>

Args:
  --bpmn      Source .bpmn file
  --out-dir   Directory to write the five JSON files (created if absent)

Exit codes:
  0  All files written
  1  Input error (file not found, unparseable XML, no bpmn:process)
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

TYPE_MAP = {
    'string': 'string',
    'integer': 'integer',
    'number': 'number',
    'boolean': 'boolean',
    'array': 'array',
    'object': 'object',
    'json': 'object',
}


def bpmn(tag):
    return f'{{{BPMN_NS}}}{tag}'


def uipath(tag):
    return f'{{{UIPATH_NS}}}{tag}'


def var_to_schema_prop(var_elem):
    vtype = var_elem.get('type', 'string')
    return {'type': TYPE_MAP.get(vtype, 'object')}


def parse_bpmn(bpmn_path):
    try:
        tree = ET.parse(bpmn_path)
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    root = tree.getroot()
    process = root.find(bpmn('process'))
    if process is None:
        print('ERROR: No bpmn:process element found', file=sys.stderr)
        sys.exit(1)

    ext = process.find(bpmn('extensionElements'))
    variables_elem = ext.find(uipath('variables')) if ext is not None else None
    all_vars = list(variables_elem) if variables_elem is not None else []

    entry_points = []
    for start in process.findall(bpmn('startEvent')):
        start_id = start.get('id', '')
        ext_s = start.find(bpmn('extensionElements'))
        if ext_s is None:
            continue
        ep_elem = ext_s.find(uipath('entryPointId'))
        if ep_elem is None:
            continue
        ep_id = ep_elem.get('value', '')
        if not ep_id:
            continue

        input_props = {}
        for v in all_vars:
            if v.get('elementId') == start_id:
                name = v.get('name', v.get('id', ''))
                input_props[name] = var_to_schema_prop(v)

        output_props = {}
        for v in all_vars:
            if not v.get('elementId'):
                ltag = v.tag.split('}')[1] if '}' in v.tag else v.tag
                if ltag in ('output', 'inputOutput'):
                    name = v.get('name', v.get('id', ''))
                    output_props[name] = var_to_schema_prop(v)

        entry_points.append({
            'id': ep_id,
            'start_event_id': start_id,
            'inputSchema': {'type': 'object', 'properties': input_props},
            'outputSchema': {'type': 'object', 'properties': output_props},
        })

    return entry_points


def main():
    parser = argparse.ArgumentParser(
        description='Scaffold package metadata files from a BPMN source file'
    )
    parser.add_argument('--bpmn', required=True, help='Source .bpmn file path')
    parser.add_argument('--out-dir', required=True, help='Output directory for JSON files')
    args = parser.parse_args()

    if not os.path.isfile(args.bpmn):
        print(f'ERROR: File not found: {args.bpmn}', file=sys.stderr)
        sys.exit(1)

    bpmn_filename = os.path.basename(args.bpmn)
    project_name = os.path.splitext(bpmn_filename)[0]

    os.makedirs(args.out_dir, exist_ok=True)

    entry_points_data = parse_bpmn(args.bpmn)

    project_uiproj = {
        'projectVersion': '1.0.0',
        'ProjectType': 'ProcessOrchestration',
        'Name': project_name,
        'main': bpmn_filename,
    }

    operate = {
        'main': bpmn_filename,
        'contentType': 'ProcessOrchestration',
    }

    entry_points_json = {
        'entryPoints': [
            {
                'id': ep['id'],
                'filePath': f'/content/{bpmn_filename}#{ep["start_event_id"]}',
                'inputSchema': ep['inputSchema'],
                'outputSchema': ep['outputSchema'],
            }
            for ep in entry_points_data
        ]
    }

    bindings_v2 = {
        'version': '2.0',
        'resources': [],
    }

    package_descriptor = {
        'content': [
            f'content/{bpmn_filename}',
            'content/bindings_v2.json',
            'content/entry-points.json',
            'content/operate.json',
        ]
    }

    files = {
        'project.uiproj': project_uiproj,
        'operate.json': operate,
        'entry-points.json': entry_points_json,
        'bindings_v2.json': bindings_v2,
        'package-descriptor.json': package_descriptor,
    }

    for fname, data in files.items():
        path = os.path.join(args.out_dir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f'  wrote {fname}')

    ep_count = len(entry_points_data)
    print(f'Scaffolded {len(files)} files for {project_name} ({ep_count} entry point(s))')


if __name__ == '__main__':
    main()
