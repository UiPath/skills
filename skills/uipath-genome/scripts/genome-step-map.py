#!/usr/bin/env python3
"""Write step-map.json from a written genome and a process inventory derived from its source export.

Usage:
  genome-step-map.py <GENOME.md> --processes <inventory.json> --recordsets <recordsets.json> [--out DIR]

The step map is the Source Map in machine-readable form: one entry per component workflow step with the source
processes it was built from and the recordsets that drive them, so execution can tie built activities to source
controls and test cases to source rows without re-reading the prose. Extraction runs it to prove the Source Map
resolves (every warning is a row that does not); execution runs it at migration preflight into the build's working
folder (default --out: the current directory). Nothing is written beside the genome.

Framework-agnostic. The genome side is read from each component genome's Source Map table (first cell = the step
key, second = the cell naming `Name` (id) references) and its Workflow section. The source side is two JSON files
the framework's own inventory script derives from the export - this script knows no framework and reads no export:

  --processes   a list of {"id", "name", "recordset" (name or null), "calls": [{"calleeId", "recordset"}]}
  --recordsets  a list of {"id", "name"} (other keys ignored, except "drives": false, which excludes an entry that is not a data set)

Source Map rows: a row keyed by a workflow step number (`1`, `2b`, `3-5`) or a step name is a step and must resolve to at least
one source process; every other row (Source framework, Source export, Checkpoints, Inventory, Excluded, Inferred, Data files,
Row schema, …) is contract and is skipped, whatever it is called.

The framework pack's inventory script writes them with its `data` command; its source guide names the two files.
A reference is a process only when the id resolves to a process of that name - root processes and their recordsets
share names, and recordset ids appear in the same prose.

The Source Map rows this script reads are the contract in references/genome-format-guide.md § Source Map; the
extraction-time check is references/extraction-guide.md Step 6b, the execution-time run
references/source-migration-guide.md § Migration preflight.
"""
import argparse
import json
import os
import re
import sys

NON_STEP_KEYS = {'workflow step', 'step', 'component', 'row schema', 'excluded', 'superseded', 'source artifacts',
                 'interaction patterns', 'process status', 'login data', 'data files', 'dead code', 'orphans',
                 'checkpoints', 'source framework', 'source export', 'inventory'}
STEP_NAME = re.compile(r'^(\d+)\.\s+\*\*(?:Test case:\s*)?(.+?)\*\*')
NAME_ID = re.compile(r'`([^`]+)`\s*\((?:id\s*)?(\d{3,6})')
BACKTICK = re.compile(r'`([^`]+)`')
BARE_ID = re.compile(r'(recordsets?\s+)?\b(\d{3,6})\b')
DATA_WORD = re.compile(r'(layout|recordset)s?\s*$', re.I)
COMPONENT_ROW = re.compile(r'^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*\[([^\]]+)\]\(([^)]+)\)')
PROJECT = re.compile(r'project\s+`([A-Za-z0-9_.\-]+)`|project\s+([A-Z][A-Za-z0-9_.\-]*)')  # a project name is backticked or capitalised; "project that" in the blueprint blockquote is neither
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
        proj = project_name(ctype)
        if proj and num in folder:
            proj = f"{proj}/{folder[num]}"
        out.append((int(num), name, os.path.join(os.path.dirname(path), link.replace('/', os.sep)), proj))
    if not out:  # a component genome on its own: the project is named in Build With (or anywhere after the blueprint blockquote)
        out = [(1, re.search(r'^# Genome:\s*(.+)$', text, re.M).group(1).strip(), path,
                project_name(section(text, 'Build With')) or project_name(text))]
    return out


def project_name(text):
    m = PROJECT.search(text or '')
    return (m.group(1) or m.group(2)) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('genome')
    ap.add_argument('--processes', required=True, help='process inventory JSON the framework script derived from the export')
    ap.add_argument('--recordsets', required=True, help='recordset list JSON from the same script')
    ap.add_argument('--out', help='where to write step-map.json; default: current directory')
    a = ap.parse_args()
    text = open(a.genome, encoding='utf-8').read()
    out_dir = a.out or '.'
    pd = json.load(open(a.processes, encoding='utf-8'))
    td = json.load(open(a.recordsets, encoding='utf-8'))
    if isinstance(pd, dict):
        sys.exit("the process inventory is name-keyed: regenerate it with the source guide's current script (names repeat)")
    for p in pd:
        if not isinstance(p, dict) or 'id' not in p or 'name' not in p:
            sys.exit(f"{a.processes}: every entry needs 'id' and 'name' (see the docstring for the contract)")
    by_id = {p['id']: p for p in pd}
    by_name = {}
    for p in pd:
        by_name.setdefault(p['name'], []).append(p)
    other_sources = {r['id']: r['name'] for r in td if not r.get('drives', True)}  # an output file, a URL, a process: provenance a row may cite, never a data set
    td = [r for r in td if r.get('drives', True)]
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
            elif rs_by_id.get(num, '').lower() == name.lower() or name in rs_names or rs_by_id.get(num, '').lower().endswith('::' + name.lower()):
                rsets.append(rs_by_id.get(num, name))  # a path-qualified recordset key (`spec.ts::TABLE`) also answers to its bare name
            elif other_sources.get(num, '').lower() == name.lower():
                pass  # cited for provenance (the file a step writes, a URL it reaches); not a process, not a recordset
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
            # a step row is keyed by the step number (or the step name); every other row (framework, export, checkpoints,
            # inventory, excluded, inferred, data files, …) is contract, not a step, whatever it is called
            is_step = bool(re.match(r'^(?:step\s+)?\d+[a-z]?(?:\s*[-–,]\s*\d+[a-z]?)*$', key, re.I)) or key.lower() in {n.lower() for n in names.values()}
            if not is_step or key.lower() in NON_STEP_KEYS:
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

    doc = {'genome': os.path.basename(a.genome),
           'inventory': {'processes': os.path.abspath(a.processes), 'recordsets': os.path.abspath(a.recordsets)},
           'note': 'Source process names repeat across folders; the id identifies the copy the step was built from. '
                   'Derived at migration preflight from the inventory of the export the Source Map names; regenerate, never edit.',
           'steps': steps}
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'step-map.json')
    open(path, 'w', encoding='utf-8').write(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"written {path}: {len(steps)} steps, {sum(len(s['sourceProcesses']) for s in steps)} process refs, "
          f"{len({r for s in steps for r in s['recordsets']})} recordsets")
    for w in warn:
        print('  WARN', w)
    return 0


if __name__ == '__main__':
    sys.exit(main())
