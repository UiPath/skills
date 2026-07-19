#!/usr/bin/env python3
"""Cross-check each connector activity node in the produced .flow file(s)
against its `connectorMethodInfo` manifest. Catches shape defects that the
built-in `uip maestro flow validate` does not surface: endpoint template vs
objectName, parameter placement (path/query/body), required-parameter
coverage, manifest defaults, JIT-input design cache, and FilterBuilder
filter-tree cache.

Exit code:
  0  no ERROR findings (may still print WARN/INFO)
  1  at least one ERROR
  2  usage error / manifest fetch failed

Usage:
  python3 check_connector_node_shape.py [<flow-file>...]

  With no args, globs every **/*.flow under CWD. Trigger and event nodes
  (uipath.connector.trigger.*, uipath.connector.event.*) are skipped —
  they don't use the JIT / FilterBuilder shape this validator enforces.
"""
import glob, json, os, subprocess, sys


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


def parse_config_blob(configuration):
    if not isinstance(configuration, str) or not configuration.startswith('=jsonString:'):
        return {}
    try:
        return json.loads(configuration[len('=jsonString:'):])
    except Exception:
        return {}


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
    manifest_actions = ((cmi.get('design') or {}).get('actions')) or []
    obj_name = next(
        (c.get('value') for c in (m.get('model', {}).get('context') or [])
         if c.get('name') == 'objectName'),
        None,
    )

    detail = node.get('inputs', {}).get('detail', {}) or {}
    ec = parse_config_blob(detail.get('configuration', '')).get('essentialConfiguration', {}) or {}

    # 1. endpoint must be the templated URL from manifest.path (not the objectName)
    got_ep = detail.get('endpoint')
    if manifest_path and got_ep != manifest_path:
        findings.append(('ERROR', flow_path, nid, 'endpoint-mismatch',
                         f'expected {manifest_path!r} (manifest.path), got {got_ep!r}'))

    # 2. Every declared parameter lives in the section its manifest type says
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

    # 3. Default values — seeded when manifest declares one.
    #    Escalate to ERROR when the parameter has `design.fieldActions` that
    #    reference itself: Studio Web's dap-config walks those rules at
    #    design load and can't resolve the refField if the property isn't
    #    present in inputs, causing DAP-DT-_2003 and failing to render the
    #    whole activity form (including the connection dropdown).
    for p in manifest_params:
        pname, ptype, dv = p.get('name'), p.get('type'), p.get('defaultValue')
        if dv is None:
            continue
        sec_name = sections.get(ptype)
        if not sec_name:
            continue
        sec = detail.get(sec_name) or {}
        if pname in sec:
            continue
        fa = (p.get('design', {}) or {}).get('fieldActions') or []
        self_ref = any(
            r.get('refFieldName') == pname
            for a in fa for r in (a.get('rules') or [])
        )
        sev = 'ERROR' if self_ref else 'INFO'
        note = ' (self-referencing fieldAction → design-load-fatal)' if self_ref else ''
        findings.append((sev, flow_path, nid, 'missing-default',
                         f'{pname}={dv!r} (manifest default) not seeded{note}'))

    # 4. JIT-typed activities need savedJitInputFieldId;
    #    FilterBuilder-typed properties need savedFilterTrees.
    has_jit_api = any(
        a.get('actionType') == 'api'
        and any(r.get('type') == 'path' for r in (a.get('rules') or []))
        for a in manifest_actions
    )
    has_filter_field = any(
        (p.get('design', {}) or {}).get('fieldActions') and p.get('name') == 'queryExpression'
        for p in manifest_params
    )
    if has_jit_api and obj_name and not has_filter_field:
        expected_jit = f'in_{obj_name}'
        if ec.get('savedJitInputFieldId') != expected_jit:
            findings.append(('ERROR', flow_path, nid, 'savedJitInputFieldId-missing',
                             f'JIT activity requires essentialConfiguration.savedJitInputFieldId={expected_jit!r}'))
    if has_filter_field:
        sft = (ec.get('savedFilterTrees') or {}).get('queryExpression')
        if not sft:
            findings.append(('ERROR', flow_path, nid, 'savedFilterTrees-missing',
                             'FilterBuilder activity requires essentialConfiguration.savedFilterTrees.queryExpression '
                             '(schema: {groups, groupOperator, index, filters, uuId})'))

    # 5. optionalConfiguration.fieldsContainer.inputFields — Studio Web's
    #    dap-config builds its DesignProperty registry from this list. Missing
    #    the list, or missing an envelope param from it, causes
    #    "Failed to find DesignProperty for textBlock <textBlock_*>" and any
    #    other DesignProperty lookup at design load. Body fields can be JIT-
    #    filled; path/query envelope params must be present.
    parsed_full = parse_config_blob(detail.get('configuration', ''))
    oc = parsed_full.get('optionalConfiguration', {}) or {}
    fc = oc.get('fieldsContainer') or {}
    input_fields = fc.get('inputFields') or []
    input_field_ids = {f.get('id') or f.get('name') for f in input_fields}
    envelope_params = [
        p for p in manifest_params if p.get('type') in ('path', 'query')
    ]
    for p in envelope_params:
        if p['name'] not in input_field_ids:
            findings.append(('ERROR', flow_path, nid,
                             'fieldsContainer-missing-envelope-param',
                             f"optionalConfiguration.fieldsContainer.inputFields does not include manifest param {p['name']!r} ({p.get('type')}) — dap-config will fail to resolve its DesignProperty"))

    # 6. Non-null connectorVersion / top-level metadata (Studio Web writes these)
    if ec.get('connectorVersion') is None:
        findings.append(('WARN', flow_path, nid, 'connectorVersion-null',
                         'essentialConfiguration.connectorVersion is null'))
    if not detail.get('objectName'):
        findings.append(('WARN', flow_path, nid, 'top-level-objectName-missing',
                         'inputs.detail.objectName absent'))
    if not detail.get('telemetryData'):
        findings.append(('WARN', flow_path, nid, 'telemetryData-missing',
                         'inputs.detail.telemetryData absent'))
    return findings


def check_solution_connection_resources(flow_path):
    """Detect duplicate connection-resource files with matching `key`
    (a symptom of the CLI's node-configure serializer emitting a redundant
    UUID-named resource on top of a properly-scaffolded friendly-named one).
    Walks up from the flow to the solution root, looking for
    `resources/**/connection/<connector>/*.json`.
    """
    findings = []
    flow_dir = os.path.dirname(os.path.abspath(flow_path))
    # Walk up until we find resources/solution_folder
    cur = flow_dir
    for _ in range(6):
        cand = os.path.join(cur, 'resources', 'solution_folder', 'connection')
        if os.path.isdir(cand):
            for conn_dir in glob.glob(os.path.join(cand, '*')):
                by_key = {}
                for rf in glob.glob(os.path.join(conn_dir, '*.json')):
                    try:
                        rd = json.load(open(rf)).get('resource', {})
                    except Exception:
                        continue
                    k = rd.get('key')
                    if k:
                        by_key.setdefault(k, []).append((rf, rd.get('name'), rd.get('spec', {}) or {}))
                for k, entries in by_key.items():
                    if len(entries) < 2:
                        continue
                    # Prefer the entry whose name != key (friendly name) — the other is the CLI-generated duplicate
                    for rf, name, spec in entries:
                        if name == k or spec.get('connectorName') == spec.get('connectorKey'):
                            findings.append(('ERROR', rf, '(solution-resource)',
                                             'duplicate-connection-resource',
                                             f'connection key {k} has ≥2 resource files; this one is malformed (name==key or connectorName==connectorKey — CLI serializer artifact)'))
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
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
        all_findings.extend(check_solution_connection_resources(path))

    if not all_findings:
        print(f'OK: {len(paths)} .flow file(s) — 0 manifest divergences')
        return 0

    for sev, path, nid, check, msg in all_findings:
        print(f'{sev:5}  {path}  {nid:30}  {check:32}  {msg}')

    errors = sum(1 for f in all_findings if f[0] == 'ERROR')
    warns  = sum(1 for f in all_findings if f[0] == 'WARN')
    infos  = sum(1 for f in all_findings if f[0] == 'INFO')
    print(f'---\n{errors} ERROR / {warns} WARN / {infos} INFO across {len(paths)} .flow file(s)')
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
