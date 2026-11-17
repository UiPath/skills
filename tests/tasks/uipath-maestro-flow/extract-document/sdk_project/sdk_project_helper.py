#!/usr/bin/env python3
"""Checks the SDK route of sdk_project: PermitDesk/PermitDesk/.flow-sdk/PermitDesk.flow.ts
calls dynamicExtract() with no model, and the compiled PermitDesk.flow holds an Extract
document node that reads the `permit` input, extracts the three requested fields (permit
number, holder name, expiry date), and has an inputs.processorKey whose idpProcessor
resource file is in the solution. Run from the sandbox root; exit 0 when all hold, else print why and exit 1."""
import glob
import json
import re
import sys

SRC = 'PermitDesk/PermitDesk/.flow-sdk/PermitDesk.flow.ts'
FLOW = 'PermitDesk/PermitDesk/PermitDesk.flow'
RESOURCES = 'PermitDesk/resources/**/*.json'


def fail(why: str) -> None:
    print(why)
    sys.exit(1)


try:
    source = open(SRC, encoding='utf-8').read()
except OSError:
    fail(f'{SRC} is missing')
if 'dynamicExtract(' not in source:
    fail(f'{SRC} calls no dynamicExtract()')
if re.search(r'\bmodel\s*:\s*\{', source):
    fail(f'{SRC} passes a model block; dynamicExtract() needs none')

flow = json.load(open(FLOW, encoding='utf-8'))
nodes = [n for n in flow.get('nodes', []) if n.get('type') == 'uipath.ixp.extract-document-builder']
if len(nodes) != 1:
    fail(f'{FLOW} holds {len(nodes)} Extract document node(s), expected 1')
inputs = nodes[0].get('inputs') or {}
file_ref = inputs.get('fileRef')
ref_text = file_ref if isinstance(file_ref, str) else json.dumps(file_ref)
if '$vars.start.output.permit' not in ref_text:
    fail(f'the Extract document node reads {ref_text!r}, not the declared permit input')

fields = []
schema = inputs.get('schemaDocument') or {}
for group in ((schema.get('outputSchema') or {}).get('properties') or {}).values():
    holder = (group.get('items') or group) if isinstance(group, dict) else {}
    fields.extend(name.lower() for name in (holder.get('properties') or {}))
wanted = {'permit number': ('permit', 'number'), 'holder name': ('holder',), 'expiry date': ('expir',)}
for label, words in wanted.items():
    if not any(all(w in f for w in words) for f in fields):
        fail(f'the taxonomy has no {label} field (fields: {sorted(fields)})')

key = inputs.get('processorKey')
if not isinstance(key, str) or not key:
    fail(f'the Extract document node in {FLOW} has no inputs.processorKey')

for path in glob.glob(RESOURCES, recursive=True):
    try:
        resource = json.load(open(path, encoding='utf-8')).get('resource') or {}
    except (OSError, ValueError, AttributeError):
        continue
    if str(resource.get('kind', '')).lower() == 'idpprocessor' and resource.get('key') == key:
        sys.exit(0)
fail(f'no idpProcessor resource file under PermitDesk/resources/ has key {key}')
