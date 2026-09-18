#!/usr/bin/env python3
"""Write <slug>-genome/source/step-map.json from a written genome and its source artifacts.

Usage:
  genome-step-map.py <GENOME.md> [--out DIR]     # default --out: <slug>-genome/source next to the genome

The step map is the Source Map in machine-readable form: one entry per component workflow step with the source
processes it was built from and the recordsets that drive them, so execution can tie built activities to source
controls and test cases to source rows without re-reading the prose.

Framework-agnostic: step -> source artifacts is read from each component genome's Source Map table (first cell = the
step key, second = the cell naming `Name` (id) references), step names from its Workflow section, and the data links
from source/process-data.json. A reference is a process only when the id resolves to a process of that name - root
processes and their recordsets share names, and recordset ids appear in the same prose.
"""
import argparse
import json
import os
import re
import sys

NON_STEP_KEYS = {'workflow step', 'step', 'component', 'row schema', 'excluded', 'superseded', 'source artifacts',
                 'interaction patterns', 'process status', 'login data', 'data files', 'dead code', 'orphans'}
STEP_NAME = re.compile(r'^(\d+)\.\s+\*\*(?:Test case:\s*)?(.+?)\*\*')
NAME_ID = re.compile(r'`([^`]+)`\s*\((?:id\s*)?(\d{3,6})')
BACKTICK = re.compile(r'`([^`]+)`')
BARE_ID = re.compile(r'(recordsets?\s+)?\b(\d{3,6})\b')
DATA_WORD = re.compile(r'(layout|recordset)s?\s*$', re.I)
COMPONENT_ROW = re.compile(r'^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*\[([^\]]+)\]\(([^)]+)\)')
PROJECT = re.compile(r'project\s+`?([A-Za-z0-9_.\-]+)`?')
LAYOUT_ROW = re.compile(r'^\|\s*`([^`]+)/`\s*\|\s*(\d+)\s*\|')


def section(text, head):
    m = re.search(rf'^## {head}\s*$(.*?)(?=^## |\Z)', text, re.S | re.M)
    return m.group(1) if m else ''


def table_rows(text):
    for row in text.splitlines():
        row = row.strip()
        if row.startswith('|') and not set(row) <= set('|-: '):
            yield [c.strip() for c in row.strip('|').split('|')]


def components(path, text):
    """[(number, name, genome path, project)] - the components of a process genome, or the file itself."""
    comp_section = section(text, 'Components')
    folder = {}  # component number -> folder inside the shared test project
    for row in comp_section.splitlines():
        m = LAYOUT_ROW.match(row.strip())
        if m:
            folder[m.group(2)] = m.group(1)
    out = []
    for row in comp_section.splitlines():
        m = COMPONENT_ROW.match(row.strip())
        if not m:
            continue
        num, name, ctype, _, link = m.groups()
        proj = (PROJECT.search(ctype) or [None, None])[1]
        if proj and num in folder:
            proj = f"{proj}/{folder[num]}"
        out.append((int(num), name, os.path.join(os.path.dirname(path), link.replace('/', os.sep)), proj))
    if not out:  # a component genome on its own
        out = [(1, re.search(r'^# Genome:\s*(.+)$', text, re.M).group(1).strip(), path,
                (PROJECT.search(text) or [None, None])[1])]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('genome')
    ap.add_argument('--out')
    a = ap.parse_args()
    text = open(a.genome, encoding='utf-8').read()
    slug = os.path.splitext(a.genome)[0]
    out_dir = a.out or os.path.join(slug, 'source')
    pd = json.load(open(os.path.join(out_dir, 'process-data.json'), encoding='utf-8'))
    td = json.load(open(os.path.join(out_dir, 'test-data.json'), encoding='utf-8'))
    if isinstance(pd, dict):
        sys.exit("process-data.json is name-keyed: regenerate it with the source guide's current script (names repeat)")
    by_id = {p['id']: p for p in pd}
    by_name = {}
    for p in pd:
        by_name.setdefault(p['name'], []).append(p)
    rs_by_id = {r['id']: r['name'] for r in td}
    rs_names = {r['name'] for r in td}
    warn = []

    def refs(cell, where):
        procs, rsets, seen = [], [], set()
        for name, num in NAME_ID.findall(cell):
            num = int(num)
            p = by_id.get(num)
            if p and p['name'].lower() == name.lower():
                if num not in seen:
                    seen.add(num)
                    procs.append(p)
            elif rs_by_id.get(num, '').lower() == name.lower() or name in rs_names:
                rsets.append(name)
            elif p:
                warn.append(f"{where}: id {num} is `{p['name']}`, the genome says `{name}`")
            else:
                warn.append(f"{where}: `{name}` (id {num}) is neither a process nor a recordset")
        for m in BACKTICK.finditer(cell):  # named without an id: unique process names only
            if DATA_WORD.search(cell[max(0, m.start() - 14):m.start()]):
                continue  # `name` introduced as a layout or recordset; roots share their name with both
            hit = by_name.get(m.group(1))
            if hit and len(hit) == 1 and hit[0]['id'] not in seen:
                seen.add(hit[0]['id'])
                procs.append(hit[0])
        for prefix, num in BARE_ID.findall(cell):  # bare id lists ("shared prelude of 7442, 7447, …")
            num = int(num)
            if prefix:
                if num in rs_by_id:
                    rsets.append(rs_by_id[num])
            elif num in by_id and num not in seen:
                seen.add(num)
                procs.append(by_id[num])
        return procs, rsets

    rows = []
    for num, comp, cpath, project in components(a.genome, text):
        ctext = open(cpath, encoding='utf-8').read()
        names = {}
        for line in section(ctext, 'Workflow').splitlines():
            m = STEP_NAME.match(line.strip())
            if m:
                names[m.group(1)] = m.group(2).strip()
        for cells in table_rows(section(ctext, 'Source Map')):
            key, cell = cells[0], cells[1] if len(cells) > 1 else ''
            if key.lower() in NON_STEP_KEYS:
                continue
            procs, named = refs(cell, f"{comp} step {key}")
            if not procs:
                warn.append(f"{comp} step {key}: no source process resolved")
                continue
            rows.append((num, comp, os.path.basename(cpath), project, key,
                         names.get(key) or (f"step {key}" if key[:1].isdigit() else key), procs, named))

    # In scope = reachable from the processes the non-library components were built from. Recordsets passed in by a
    # caller outside that set drive another scenario (the variant suite left unbuilt) and are noise on a shared step.
    scope = {p['id'] for r in rows if r[0] > 1 for p in r[6]} or set(by_id)
    frontier = list(scope)
    while frontier:
        for c in (by_id.get(frontier.pop()) or {}).get('calls', []):
            if c['calleeId'] not in scope:
                scope.add(c['calleeId'])
                frontier.append(c['calleeId'])
    passed = {}
    for p in pd:
        if p['id'] in scope:
            for c in p['calls']:
                if c.get('recordset'):
                    passed.setdefault(c['calleeId'], set()).add(c['recordset'])

    steps = []
    for num, comp, cfile, project, key, name, procs, named in rows:
        rs = []  # what drives the step: each process's own recordset, the ones it passes on, the ones passed to it
        for p in procs:
            if p['id'] not in scope:
                warn.append(f"{comp} step {key}: `{p['name']}` ({p['id']}) is not reachable from the built roots")
            for r in ([p['recordset']] if p.get('recordset') else []) \
                    + [c['recordset'] for c in p['calls'] if c.get('recordset')] + sorted(passed.get(p['id'], ())):
                if r not in rs:
                    rs.append(r)
        for r in named:
            if r not in rs:
                rs.append(r)
        steps.append({'component': f"{num} {comp}", 'componentGenome': cfile, 'project': project, 'step': key,
                      'name': name, 'sourceProcesses': [{'name': p['name'], 'id': p['id']} for p in procs],
                      'recordsets': rs})

    doc = {'genome': os.path.basename(a.genome), 'sourceArtifacts': ['targets.json', 'test-data.json', 'process-data.json'],
           'note': 'Source process names repeat across folders; the id identifies the copy the step was built from.',
           'steps': steps}
    path = os.path.join(out_dir, 'step-map.json')
    open(path, 'w', encoding='utf-8').write(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"written {path}: {len(steps)} steps, {sum(len(s['sourceProcesses']) for s in steps)} process refs, "
          f"{len({r for s in steps for r in s['recordsets']})} recordsets")
    for w in warn:
        print('  WARN', w)
    return 0


if __name__ == '__main__':
    sys.exit(main())
