#!/usr/bin/env python3
"""Inventory a Worksoft Certify JSON database export for genome extraction.

Usage:
  certify-export-inventory.py profile <EXPORT_DIR> [--out DIR]   # vocabulary, results, call graph, roots, clusters, layouts, screens
  certify-export-inventory.py cards   <EXPORT_DIR> [--out DIR]   # one compact card per process
  certify-export-inventory.py dump    <EXPORT_DIR> <PROCESS_NAME> # one process, step by step, in execution order
  certify-export-inventory.py targets <EXPORT_DIR> [--out DIR]   # UI target catalog: windows + controls with parsed Certify locators
  certify-export-inventory.py data    <EXPORT_DIR> [--out DIR]   # test data: layouts + recordsets as named rows, process -> recordset links

Writes certify-profile.txt / certify-cards.txt / certify-targets.{json,md} / certify-test-data.{json,md} /
certify-process-data.json into --out (default: current directory); dump prints to stdout.
Never prints values of variables whose name contains password/pwd/secret/token (account user names are kept: they are
identity, not secrets).
"""
import argparse
import collections
import json
import os
import re
import sys

META = {'UniqueKey', 'CreatedDt', 'CreatedBy', 'ModifiedDt', 'ModifiedBy', 'EF6State'}
SENSITIVE = re.compile(r'passw|pwd|secret|token', re.I)
SYS_PREFIXES = ('Execution.', 'Operating System.', 'Variable.', 'Text.', 'Number.', 'Date.', 'Record Set.', 'Browser.', 'Window.')
NOISE_ACTIONS = ('Execution.Wait', 'Operating System.Capture Screen Image')


class D(dict):
    def __missing__(self, k):
        return None


def conv(o):
    if isinstance(o, dict):
        return D({k: conv(v) for k, v in o.items()})
    if isinstance(o, list):
        return [conv(x) for x in o]
    return o


class Export:
    def __init__(self, root):
        self.root = root
        L = lambda f: conv(json.load(open(os.path.join(root, f), encoding='utf-8-sig'))) if os.path.exists(os.path.join(root, f)) else []
        self.P = L('Processes.json'); self.C = L('Components.json'); self.A = L('ComponentActions.json'); self.PR = L('ComponentActionParms.json')
        self.V = L('Variables.json'); self.LY = L('Layouts.json'); self.RS = L('Recordsets.json'); self.M = L('MapObjects.json')
        self.AT = L('Attributes.json'); self.IL = L('InterfaceLibraries.json'); self.AP = L('Applications.json'); self.PF = L('ProcessFolders.json')
        self.comp = {c['ComponentID']: c for c in self.C}
        self.act = {a['ComponentActionID']: a for a in self.A}
        self.parm = {p['ComponentActionParmsID']: p for p in self.PR}
        self.var = {v['VariableID']: v for v in self.V}
        self.proc = {p['ProcessID']: p for p in self.P}
        self.lay = {l['LayoutID']: l for l in self.LY}
        self.rs = {r['RecordSetID']: r for r in self.RS}
        self.il = {i['InterfaceLibraryID']: i['Name'] for i in self.IL}
        self.appver = {v['ApplicationVersionID']: a['Name'] for a in self.AP for v in (a['ApplicationVersions'] or [])}
        self.objwin, self.objname = {}, {}
        for m in self.M:
            self.objwin[m['ObjectID']] = m['Name']; self.objname[m['ObjectID']] = m['Name']
            for k in m['ChildTrackObjects'] or []:
                self.objwin[k['ObjectID']] = m['Name']; self.objname[k['ObjectID']] = k['Name']
        self.fpath = {}
        if isinstance(self.PF, dict):
            self._walk(self.PF, '')
        self.edges = collections.defaultdict(list)
        for p in self.P:
            for s in self.ordered(p):
                if s['Skip']:
                    continue
                for ta in s['TestStepActions'] or []:
                    t = ta['ExecProcessID']
                    if t in self.proc and t != p['ProcessID']:
                        self.edges[p['ProcessID']].append(t)
        self.called = set(t for ts in self.edges.values() for t in ts)

    def _walk(self, f, path):
        self.fpath[f['FolderID']] = path + '\\' + f['Name']
        for c in f['ChildFolders'] or []:
            self._walk(c, path + '\\' + f['Name'])

    def aname(self, aid):
        a = self.act.get(aid)
        return f"{self.comp.get(a['ComponentID'], {}).get('LogicalName')}.{a['Name']}" if a else f"?{aid}"

    def folder(self, p):
        return self.fpath.get(p['ProcessFolderID'], '?')

    @staticmethod
    def ordered(p):
        return sorted(p['TestSteps'] or [], key=lambda x: (x['CertifySequence'] or 0, x['TestStepID']))

    def safe(self, name, value):
        return '***' if name and SENSITIVE.search(str(name)) else value

    def parms(self, step):
        out = {}
        for ta in step['TestStepActions'] or []:
            out[self.parm.get(ta['ComponentActionParmsID'], {}).get('Name')] = ta
        return out

    def records(self, rsid):
        r = self.rs.get(rsid)
        ids = [d['LayoutVariablesID'] for d in (r['RecordSetDatas'] or [])] if r else []
        return max(collections.Counter(ids).values()) if ids else 0


def parse_desc(desc):
    desc = (desc or '').replace('\r\n', '\n')
    parts = re.split(r'\n\s*([A-Za-z][A-Za-z /]+)\n\s*\*{3,}\s*\n', '\n' + desc)
    return {parts[i].strip().lower(): [l.strip() for l in parts[i + 1].strip().split('\n') if l.strip()] for i in range(1, len(parts) - 1, 2)}


def profile(x: Export):
    L = []
    pr = lambda *a: L.append(' '.join(str(v) for v in a))
    steps = [s for p in x.P for s in (p['TestSteps'] or [])]
    pr(f"## EXPORT {x.root}: processes={len(x.P)} steps={len(steps)} skipped={sum(1 for s in steps if s['Skip'])} layouts={len(x.LY)} recordsets={len(x.RS)} map windows={len(x.M)}")
    pr("\n## APPLICATIONS:", [(a['Name'], [x.il.get(iv['InterfaceLibraryID']) for v in (a['ApplicationVersions'] or []) for iv in (v['InterfaceAppVers'] or [])]) for a in x.AP])
    pr("\n## COMPONENT ACTIONS by usage (comp.action uses | parms)")
    use = collections.Counter(s['ComponentActionID'] for s in steps)
    for aid, n in use.most_common():
        ps = [p['Name'] for p in x.PR if p['ComponentActionID'] == aid]
        pr(f"  {x.aname(aid)} uses={n} | {ps[:10]}{'…' if len(ps) > 10 else ''}")
    pr("\n## RESULTS (Name, ResultLogStatusID, ExecutionStatusID):", collections.Counter((r['Name'], r['ResultLogStatusID'], r['ExecutionStatusID']) for s in steps for r in (s['TestStepResults'] or [])).most_common())
    bc = collections.Counter()
    for p in x.P:
        for s in p['TestSteps'] or []:
            for r in s['TestStepResults'] or []:
                if r['ExecutionStatusID'] != 1:
                    bc[(r['Name'], r['ResultLogStatusID'], r['ExecutionStatusID'], x.aname(s['ComponentActionID']))] += 1
    pr("## BRANCHING (result, log, exec, action):", bc.most_common(25))
    pr("\n## SENSITIVE VARIABLES (values never printed):", sorted({v['Name'] for v in x.V if SENSITIVE.search(v['Name'] or '')}))
    roots = [p for p in x.P if p['ProcessID'] not in x.called]
    pr(f"\n## CALL GRAPH: callers={len(x.edges)} called={len(x.called)} roots={len(roots)} leaves={sum(1 for p in x.P if p['ProcessID'] not in x.edges)}")
    pr("\n## FOLDERS (path: processes, statuses, steps)")
    byf = collections.defaultdict(list)
    for p in x.P:
        byf[x.folder(p)].append(p)
    for f in sorted(byf):
        ps = byf[f]
        pr(f"  {f}: {len(ps)} | status {dict(collections.Counter(p['ProcessStatusID'] for p in ps))} | steps {sum(len(p['TestSteps'] or []) for p in ps)}")

    def sig(p):
        names = []
        for t in x.edges[p['ProcessID']]:
            n = x.proc[t]['Name']
            if not names or names[-1] != n:
                names.append(n)
        return tuple(names)
    clusters = collections.defaultdict(list)
    for p in roots:
        clusters[sig(p)].append(p)
    pr(f"\n## ROOT CLUSTERS by ordered callee signature: {len(clusters)}")
    for s, ps in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        pr(f"### size={len(ps)} callees={list(s) if s else 'NONE (leaf root)'}")
        for p in sorted(ps, key=lambda p: (x.folder(p), p['Name'])):
            pr(f"    {x.folder(p)} | {p['Name']} | steps={len([s for s in x.ordered(p) if not s['Skip']])} | layout={x.lay.get(p['LayoutID'], {}).get('Name')} | rs={x.rs.get(p['RecordSetID'], {}).get('Name')} records={x.records(p['RecordSetID'])} | status={p['ProcessStatusID']} | modified={str(p['ModifiedDt'])[:10]}")
    callers = collections.defaultdict(set)
    for pid, ts in x.edges.items():
        for t in ts:
            callers[t].add(pid)
    pr("\n## CALLED PROCESSES (folder | name | steps | #callers)")
    for p in sorted(x.P, key=lambda p: (x.folder(p), p['Name'])):
        if p['ProcessID'] in x.called:
            pr(f"  {x.folder(p)} | {p['Name']} | {len(p['TestSteps'] or [])} | callers={len(callers[p['ProcessID']])}")
    pr("\n## LAYOUTS (name | variables | recordsets)")
    for l in x.LY:
        vn = [x.var.get(lv['VariableID'], {}).get('Name') for lv in sorted(l['LayoutVariables'] or [], key=lambda v: v['CertifySequence'] or 0)]
        pr(f"  {l['Name']} | {vn} | rs={[r['Name'] for r in (l['RecordSets'] or [])][:10]}")
    pr("\n## MAP WINDOWS (app | window | physical | #controls | control types)")
    for m in x.M:
        kids = m['ChildTrackObjects'] or []
        pr(f"  {x.appver.get(m['ApplicationVersionID'])} | {m['Name']} | {(m['PhysicalName'] or '')[:50]} | {len(kids)} | {dict(collections.Counter(x.comp.get(k['ComponentID'], {}).get('LogicalName') for k in kids).most_common(6))}")
    byname = collections.defaultdict(list)
    for p in x.P:
        byname[re.sub(r'^c(?=workday|hire|interview|jobreq|start|verify|complete|verify)', '', p['Name'].strip().lower())].append(p)
    pr("\n## NAME COLLISIONS (copies across folders)")
    for k, v in sorted(byname.items()):
        if len(v) > 1:
            pr("  ", k, '->', [(x.folder(p), len(p['TestSteps'] or [])) for p in v])
    return '\n'.join(L)


def cards(x: Export):
    L = []
    pr = lambda *a: L.append(' '.join(str(v) for v in a))
    for p in sorted(x.P, key=lambda p: (x.folder(p), p['Name'])):
        live = [s for s in x.ordered(p) if not s['Skip']]
        d = parse_desc(p['Description'])
        pr(f"### {p['Name']}  [{x.folder(p)}] id={p['ProcessID']} status={p['ProcessStatusID']} steps={len(live)} skipped={len(x.ordered(p)) - len(live)} modified={str(p['ModifiedDt'])[:10]}")
        if d.get('objective'):
            pr(f"  objective: {' '.join(d['objective'])[:300]}")
        if d.get('input variables'):
            pr(f"  inputs(doc): {', '.join(d['input variables'])[:300]}")
        if d.get('output variables') and d['output variables'] != ['NA']:
            pr(f"  outputs(doc): {', '.join(d['output variables'])[:200]}")
        l = x.lay.get(p['LayoutID'])
        if l:
            vn = [x.var.get(v['VariableID'], {}).get('Name') for v in sorted(l['LayoutVariables'] or [], key=lambda v: v['CertifySequence'] or 0)]
            pr(f"  layout: {l['Name']} vars={vn} | recordset: {x.rs.get(p['RecordSetID'], {}).get('Name')} records={x.records(p['RecordSetID'])}")
        calls, wins, phases, labels, checks, sets, finds, branches, data_in = [], [], [], [], [], [], [], [], []
        for i, s in enumerate(live, 1):
            an = x.aname(s['ComponentActionID'])
            tas = x.parms(s)
            val = lambda k: x.safe(k, (tas.get(k) or {}).get('CertifyValue'))
            vref = lambda k: x.var.get((tas.get(k) or {}).get('VariableID'), {}).get('Name')
            if an == 'Execution.Execute Process':
                t = next((ta['ExecProcessID'] for ta in (s['TestStepActions'] or []) if ta['ExecProcessID']), None)
                rsn = next((x.rs.get(ta['ExecRecordSetID'], {}).get('Name') for ta in (s['TestStepActions'] or []) if ta['ExecRecordSetID']), None)
                calls.append(x.proc.get(t, {}).get('Name', f'?{t}') + (f"[rs={rsn}]" if rsn else ''))
            elif an == 'Execution.Comment':
                phases.append(str(val('Comment'))[:60])
            elif an == 'Execution.Label':
                labels.append(str(val('Comment'))[:40])
            elif an.startswith('Variable.') or (an.endswith('.Set') and an.startswith(('Number', 'Text'))):
                sets.append(f"{vref('Variable')}={val('Value') or ('T[' + str(vref('Value')) + ']' if vref('Value') else '')}"[:70])
            elif an.split('.')[0] in ('Text', 'Number', 'Date') or an.startswith('Record Set.'):
                sets.append(f"{vref('Variable') or vref('Result') or ''}<-{an.split('.')[1]}({val('RecordSet') or val('File') or ''})")
            if not an.startswith(SYS_PREFIXES):
                w = x.objwin.get(s['ObjectID'])
                if w and (not wins or wins[-1] != w):
                    wins.append(w)
                if '.Verify' in an or an.endswith('.Visible'):
                    checks.append(f"{x.objname.get(s['ObjectID'])}:{an.split('.')[1]}({val('Condition') or val('Criteria') or val('Visible') or ''} {val('Value') or vref('Value') or ''})".replace('  ', ' ')[:80])
                if an.startswith('Table.Find'):
                    finds.append(f"{x.objname.get(s['ObjectID'])}:{val('Row Matching String 1') or val('Match Value 1') or vref('Row Matching String 1') or vref('Match Value 1') or ''}"[:70])
                if an.endswith(('.Input', '.Select', '.Input Autocomplete', '.Set', '.Type Keys', '.Select Node', '.Input Into Cell')):
                    src = vref('Value') or vref('Item') or vref('Key') or vref('Typed Value') or vref('NodePath')
                    lit = val('Value') or val('Item') or val('Typed Value') or val('NodePath') or val('State')
                    data_in.append(f"{x.objname.get(s['ObjectID'])}<-{('T[' + src + ']') if src else repr(lit)[:40]}")
            if an == 'Text.Compare':
                checks.append(f"Compare({vref('Value1') or val('Value1')} {val('Condition')} {vref('Value2') or val('Value2')})"[:80])
            for r in s['TestStepResults'] or []:
                if r['ExecutionStatusID'] != 1:
                    branches.append(f"s{i}:{an.split('.')[-1]} on {r['Name']}(log{r['ResultLogStatusID']})->exec{r['ExecutionStatusID']}:{r['ExecTestStepID']}")
        for label, items, cap in (('calls', calls, 60), ('screens', wins, 40), ('phases', phases, 30), ('labels', labels, 30), ('inputs(ui)', data_in, 40), ('table-finds', finds, 12), ('checks', checks, 20), ('vars', sets, 20), ('branches', branches, 16)):
            if items:
                pr(f"  {label}: {items[:cap]}{'…' if len(items) > cap else ''}")
        pr("")
    return '\n'.join(L)


def dump(x: Export, name):
    p = next((q for q in x.P if q['Name'] == name), None)
    if not p:
        return f"no process named {name!r}"
    L = []
    pr = lambda *a: L.append(' '.join(str(v) for v in a))
    pr(f"# {p['Name']}  [{x.folder(p)}] id={p['ProcessID']} layout={x.lay.get(p['LayoutID'], {}).get('Name')} recordset={x.rs.get(p['RecordSetID'], {}).get('Name')} status={p['ProcessStatusID']}")
    pr("DESCRIPTION:", (p['Description'] or '').replace('\r\n', ' / ')[:1500])
    l = x.lay.get(p['LayoutID'])
    if l:
        lv = {v['LayoutVariablesID']: x.var.get(v['VariableID'], {}).get('Name') for v in l['LayoutVariables'] or []}
        r = x.rs.get(p['RecordSetID'])
        if r:
            pr("RECORDSET VALUES:", {lv.get(d['LayoutVariablesID']): x.safe(lv.get(d['LayoutVariablesID']), d['CertifyValue']) for d in (r['RecordSetDatas'] or [])})
    pr("")
    for i, st in enumerate(x.ordered(p), 1):
        an = x.aname(st['ComponentActionID'])
        ps = []
        for ta in st['TestStepActions'] or []:
            pn = x.parm.get(ta['ComponentActionParmsID'], {}).get('Name') or ta['ComponentActionParmsID']
            v = x.safe(pn, ta['CertifyValue'])
            extra = ''
            if ta['ExecProcessID']:
                extra += f" ->PROC:{x.proc.get(ta['ExecProcessID'], {}).get('Name')}"
            if ta['ExecLayoutID']:
                extra += f" ->LAYOUT:{x.lay.get(ta['ExecLayoutID'], {}).get('Name')}"
            if ta['ExecRecordSetID']:
                extra += f" ->RS:{x.rs.get(ta['ExecRecordSetID'], {}).get('Name')}"
            if ta['VariableID']:
                extra += f" ->VAR:{x.var.get(ta['VariableID'], {}).get('Name')}"
            if v not in (None, '') or extra:
                ps.append(f"{pn}={v!r}{extra}")
        res = [f"{r['Name']}:log{r['ResultLogStatusID']}/exec{r['ExecutionStatusID']}" + (f"->{r['ExecTestStepID']}" if r['ExecTestStepID'] else '')
               for r in (st['TestStepResults'] or []) if r['ExecutionStatusID'] != 1 or r['ResultLogStatusID'] not in (1, 2)]
        skip = ' [SKIP]' if st['Skip'] else ''
        obj = x.objname.get(st['ObjectID'], st['ObjectID'])
        win = x.objwin.get(st['ObjectID'])
        pr(f"{i:>3}.{skip} {an:<34} obj={(f'{win} / {obj}' if win and win != obj else obj)!s:<50} {'; '.join(ps)}")
        if res:
            pr(f"      results: {res}")
        if st['Narrative'] and an not in NOISE_ACTIONS:
            pr(f"      » {st['Narrative'][:160]}")
    return '\n'.join(L)


def _parse_locator(v):
    """Certify locator XML -> {tagname, instance, frame, findby:[{n, criteria, v}]}."""
    import html
    d = {}
    for k in ('frame', 'tagname', 'instance'):
        mm = re.search(rf'<{k}>(.*?)</{k}>', v or '', re.S)
        if mm:
            d[k] = html.unescape(mm.group(1))
    fb = re.search(r'<findby>(.*?)</findby>', v or '', re.S)
    d['findby'] = [{'n': html.unescape(n), 'criteria': c or 'isequalto', 'v': html.unescape(val)}
                   for n, c, val in re.findall(r'<n>(.*?)</n>\s*<v(?: criteria="([^"]*)")?>(.*?)</v>', fb.group(1), re.S)] if fb else []
    return d


def targets(x: Export):
    """UI target catalog: every window and control with its parsed locator (feeds execution's target migration)."""
    cat = []
    for w in x.M:
        wl = [_parse_locator(p['CertifyValue']) for p in (w['ObjectIdParmValues'] or []) if p['CertifyValue']]
        ctrls = [{'objectId': c['ObjectID'], 'name': c['Name'], 'physicalName': c['PhysicalName'], 'description': c['Description'],
                  'type': (c['Component'] or {}).get('LogicalName'),
                  'locators': [_parse_locator(p['CertifyValue']) for p in (c['ObjectIdParmValues'] or []) if p['CertifyValue']]}
                 for c in (w['ChildTrackObjects'] or [])]
        cat.append({'objectId': w['ObjectID'], 'app': x.appver.get(w['ApplicationVersionID']), 'name': w['Name'],
                    'physicalName': w['PhysicalName'], 'description': w['Description'], 'locators': wl, 'controls': ctrls})
    names = collections.Counter(p['n'].lower() for w in cat for c in w['controls'] for l in c['locators'] for p in l['findby'])
    md = ["# Certify UI target catalog\n", f"{len(cat)} windows, {sum(len(w['controls']) for w in cat)} controls. "
          f"Locator attributes: {', '.join(f'{k} ({v})' for k, v in names.most_common())}\n"]
    for w in cat:
        wsel = '; '.join(f"{p['n']} {p['criteria']} {p['v']!r}" for l in w['locators'] for p in l['findby']) or '(no window locator)'
        md.append(f"\n## {w['name']} [{w['app']}] objectId={w['objectId']} — {wsel}\n")
        for c in w['controls']:
            locs = ' | '.join(f"{l.get('tagname')}#{l.get('instance') or 1}: " + ', '.join(f"{p['n']} {p['criteria']} {p['v'][:60]!r}" for p in l['findby']) for l in c['locators']) or '(no locator)'
            md.append(f"- {c['objectId']} `{c['name']}` ({c['type']}) — {locs}")
    return cat, '\n'.join(md)


def data(x: Export):
    """Layouts + recordsets as named rows; process -> layout/recordset links. Secrets redacted, user names kept."""
    lv = {}
    lay_vars = {}
    for l in x.LY:
        vs = sorted(l['LayoutVariables'] or [], key=lambda v: v['CertifySequence'] or 0)
        lay_vars[l['LayoutID']] = [x.var.get(v['VariableID'], {}).get('Name') or f"var{v['VariableID']}" for v in vs]
        for v in vs:
            lv[v['LayoutVariablesID']] = x.var.get(v['VariableID'], {}).get('Name') or f"var{v['VariableID']}"
    out = []
    for r in x.RS:
        cells = r['RecordSetDatas'] or []
        n = max(collections.Counter(c['LayoutVariablesID'] for c in cells).values()) if cells else 0
        rows, idx = [dict() for _ in range(n)], collections.Counter()
        for c in cells:  # export order == row order per variable
            k = c['LayoutVariablesID']; name = lv.get(k, f"lv{k}")
            rows[idx[k]][name] = x.safe(name, c['CertifyValue']); idx[k] += 1
        out.append({'id': r['RecordSetID'], 'name': r['Name'], 'layout': x.lay.get(r['LayoutID'], {}).get('Name'),
                    'layoutId': r['LayoutID'], 'variables': lay_vars.get(r['LayoutID'], []), 'rows': rows})
    pd = {}
    for p in x.P:
        calls = [{'callee': x.proc.get(ta['ExecProcessID'], {}).get('Name'), 'layout': x.lay.get(ta['ExecLayoutID'], {}).get('Name'),
                  'recordset': x.rs.get(ta['ExecRecordSetID'], {}).get('Name'), 'mode': ta['RecordSetMode']}
                 for s in x.ordered(p) if not s['Skip'] for ta in (s['TestStepActions'] or []) if ta['ExecProcessID']]
        pd[p['Name']] = {'layout': x.lay.get(p['LayoutID'], {}).get('Name'), 'recordset': x.rs.get(p['RecordSetID'], {}).get('Name'),
                         'recordsetId': p['RecordSetID'], 'status': p['ProcessStatusID'], 'folder': x.folder(p), 'calls': calls}
    md = ["# Certify test data by layout (secrets redacted)\n"]
    by_layout = collections.defaultdict(list)
    for r in out:
        by_layout[r['layout'] or '(no layout)'].append(r)
    for lay, items in sorted(by_layout.items()):
        md.append(f"\n## Layout `{lay}` — variables: {', '.join(items[0]['variables'])}\n")
        for r in sorted(items, key=lambda q: q['name']):
            md.append(f"\n### Recordset `{r['name']}` (id {r['id']}, {len(r['rows'])} row(s))")
            for i, row in enumerate(r['rows'][:6], 1):
                md.append(f"- row {i}: " + '; '.join(f"`{k}`={json.dumps(v, ensure_ascii=False)}" for k, v in row.items() if v not in (None, '')))
            if len(r['rows']) > 6:
                md.append(f"- … {len(r['rows']) - 6} more rows")
    dup = [k for k, v in collections.Counter(r['name'] for r in out).items() if v > 1]
    if dup:
        md.append(f"\nDuplicate recordset names (pick the one with rows): {dup}")
    return out, pd, '\n'.join(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['profile', 'cards', 'dump', 'targets', 'data'])
    ap.add_argument('export_dir')
    ap.add_argument('process_name', nargs='?')
    ap.add_argument('--out', default='.')
    a = ap.parse_args()
    x = Export(a.export_dir)
    if a.command == 'dump':
        if not a.process_name:
            ap.error('dump requires PROCESS_NAME')
        print(dump(x, a.process_name))
        return 0
    os.makedirs(a.out, exist_ok=True)
    W = lambda name, content: (open(os.path.join(a.out, name), 'w', encoding='utf-8').write(content), print(f"written {os.path.join(a.out, name)}"))
    if a.command == 'targets':
        cat, md = targets(x)
        W('certify-targets.json', json.dumps(cat, indent=1, ensure_ascii=False)); W('certify-targets.md', md)
        return 0
    if a.command == 'data':
        rs, pd, md = data(x)
        W('certify-test-data.json', json.dumps(rs, indent=1, ensure_ascii=False))
        W('certify-process-data.json', json.dumps(pd, indent=1, ensure_ascii=False)); W('certify-test-data.md', md)
        return 0
    text = profile(x) if a.command == 'profile' else cards(x)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f'certify-{a.command}.txt')
    open(path, 'w', encoding='utf-8').write(text)
    print(f"written {path} ({len(text.splitlines())} lines)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
