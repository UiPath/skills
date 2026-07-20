#!/usr/bin/env python3
"""Cross-check each connector activity node in the produced .flow file(s)
against its `connectorMethodInfo` manifest.

Scope: only shape defects the CLI (`uip maestro flow node add` +
`uip maestro flow node configure`) can and should get right — endpoint
template, parameter placement (path/query/body), required-parameter coverage.
UI-only fields (`optionalConfiguration.fieldsContainer.inputFields`,
top-level `inputs.detail.objectName`, `telemetryData`, non-null
`connectorVersion`) are NOT checked — the CLI never populates them.

Exit code:
  0  no ERROR findings
  1  at least one ERROR
  2  usage error / manifest fetch failed

Usage:
  python3 check_connector_node_shape.py [<flow-file>...]

  With no args, globs every **/*.flow under CWD. Trigger and event nodes
  (uipath.connector.trigger.*, uipath.connector.event.*) are skipped.
"""
import glob, json, subprocess, sys


def run_uip_json(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'uip call failed: {" ".join(args)}\n{p.stderr[:500]}')
    raw = p.stdout
    return json.loads(raw[raw.find('{'):])


_MANIFEST_CACHE = {}
def manifest(node_type):
    if node_type not in _MANIFEST_CACHE:
        d = run_uip_json(['uip', 'maestro', 'flow', 'registry', 'get', node_type, '--output', 'json'])
        _MANIFEST_CACHE[node_type] = d.get('Data', {}).get('Node', {})
    return _MANIFEST_CACHE[node_type]


def check_node(flow_path, node):
    nid = node['id']
    ntype = node.get('type', '')
    findings = []
    if not ntype.startswith('uipath.connector.') or '.trigger.' in ntype or '.event.' in ntype:
        return findings
    try:
        m = manifest(ntype)
    except Exception as e:
        findings.append(('ERROR', flow_path, nid, 'manifest-fetch', str(e)[:200]))
        return findings
    cmi = m.get('connectorMethodInfo', {}) or {}
    manifest_path = cmi.get('path')
    manifest_params = cmi.get('parameters') or []

    detail = node.get('inputs', {}).get('detail', {}) or {}

    # 1. endpoint must be the templated URL from manifest.path
    got_ep = detail.get('endpoint')
    if manifest_path and got_ep != manifest_path:
        findings.append(('ERROR', flow_path, nid, 'endpoint-mismatch',
                         f'expected {manifest_path!r} (manifest.path), got {got_ep!r}'))

    # 2. Every declared parameter lives in the section its manifest type says,
    #    and required parameters are present.
    sections = {'path': 'pathParameters', 'query': 'queryParameters', 'body': 'bodyParameters'}
    for p in manifest_params:
        pname, ptype, required = p.get('name'), p.get('type'), p.get('required')
        expect = sections.get(ptype)
        if not expect:
            continue
        for sec_name in sections.values():
            sec = detail.get(sec_name) or {}
            if pname in sec and sec_name != expect:
                findings.append(('ERROR', flow_path, nid, 'param-in-wrong-section',
                                 f'{pname!r} declared {ptype!r} but found in {sec_name}'))
        if required and pname not in (detail.get(expect) or {}):
            findings.append(('WARN', flow_path, nid, 'required-param-missing',
                             f'{pname!r} ({ptype}) required by manifest, absent from {expect}'))
    return findings


def main():
    paths = sys.argv[1:] or sorted(glob.glob('**/*.flow', recursive=True))
    if not paths:
        print('no .flow files found under CWD', file=sys.stderr)
        return 2

    all_findings = []
    for path in paths:
        try:
            doc = json.load(open(path))
        except Exception as e:
            all_findings.append(('ERROR', path, '-', 'load-error', str(e)[:200]))
            continue
        for n in doc.get('nodes', []):
            all_findings.extend(check_node(path, n))

    if not all_findings:
        print(f'OK: {len(paths)} .flow file(s) — 0 manifest divergences')
        return 0

    for sev, path, nid, check, msg in all_findings:
        print(f'{sev:5}  {path}  {nid:30}  {check:32}  {msg}')

    errors = sum(1 for f in all_findings if f[0] == 'ERROR')
    warns  = sum(1 for f in all_findings if f[0] == 'WARN')
    print(f'---\n{errors} ERROR / {warns} WARN across {len(paths)} .flow file(s)')
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
