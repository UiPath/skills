#!/usr/bin/env python3
"""
Generate bpmndi:BPMNDiagram (shapes + edges) for a BPMN file.

Reads all flow nodes and sequence flows from bpmn:process, computes a
left-to-right BFS layout using fixed per-type dimensions, then inserts or
replaces the BPMNDiagram section.

Usage:
  python3 generate_diagram.py --bpmn <file.bpmn> [--out <output.bpmn>]

Args:
  --bpmn    Input .bpmn file (must contain bpmn:process)
  --out     Output path (default: overwrite --bpmn)
"""
import argparse
import re
import sys
from collections import defaultdict, deque

try:
    import defusedxml.ElementTree as ET
except ImportError:
    print('ERROR: defusedxml required — pip install defusedxml', file=sys.stderr)
    sys.exit(1)

BPMN_NS = 'http://www.omg.org/spec/BPMN/20100524/MODEL'

EVENT_TAGS = {
    'startEvent', 'endEvent', 'intermediateThrowEvent',
    'intermediateCatchEvent', 'boundaryEvent',
}
GATEWAY_TAGS = {
    'exclusiveGateway', 'parallelGateway', 'inclusiveGateway',
    'eventBasedGateway', 'complexGateway',
}

X_START = 160
Y_START = 100
H_GAP = 60
V_GAP = 30


def local(element):
    tag = element.tag
    return tag.split('}')[1] if '}' in tag else tag


def node_size(tag):
    if tag in EVENT_TAGS:
        return 36, 36
    if tag in GATEWAY_TAGS:
        return 50, 50
    return 100, 80


def collect_process(process_elem):
    nodes = {}   # id -> local_tag
    flows = {}   # id -> (sourceRef, targetRef)
    for child in process_elem:
        lt = local(child)
        cid = child.get('id')
        if not cid:
            continue
        if lt == 'sequenceFlow':
            flows[cid] = (child.get('sourceRef', ''), child.get('targetRef', ''))
        elif lt not in ('extensionElements',):
            nodes[cid] = lt
    return nodes, flows


def bfs_levels(nodes, flows):
    adj = defaultdict(list)
    for src, tgt in flows.values():
        if src in nodes and tgt in nodes:
            adj[src].append(tgt)

    starts = sorted(nid for nid, lt in nodes.items() if lt == 'startEvent')
    if not starts:
        starts = sorted(nodes)[:1]

    levels = {}
    visited = set()
    q = deque()
    for s in starts:
        levels[s] = 0
        visited.add(s)
        q.append(s)

    while q:
        cur = q.popleft()
        for nxt in sorted(adj[cur]):
            if nxt not in visited:
                visited.add(nxt)
                levels[nxt] = levels[cur] + 1
                q.append(nxt)

    max_lvl = max(levels.values()) if levels else 0
    for nid in nodes:
        if nid not in levels:
            max_lvl += 1
            levels[nid] = max_lvl

    return levels


def compute_layout(nodes, flows):
    levels = bfs_levels(nodes, flows)

    by_level = defaultdict(list)
    for nid, lvl in levels.items():
        by_level[lvl].append(nid)
    for lvl in by_level:
        by_level[lvl].sort()

    level_max_w = {
        lvl: max(node_size(nodes[nid])[0] for nid in nids)
        for lvl, nids in by_level.items()
    }

    x_by_level = {}
    x = X_START
    for lvl in sorted(by_level):
        x_by_level[lvl] = x
        x += level_max_w[lvl] + H_GAP

    positions = {}
    for lvl in sorted(by_level):
        nids = by_level[lvl]
        max_h = max(node_size(nodes[nid])[1] for nid in nids)
        y = Y_START
        for nid in nids:
            w, h = node_size(nodes[nid])
            positions[nid] = (x_by_level[lvl], y, w, h)
            y += max_h + V_GAP

    return positions


def center(pos):
    x, y, w, h = pos
    return x + w // 2, y + h // 2


def build_diagram_xml(nodes, flows, positions, process_id):
    lines = [
        f'  <bpmndi:BPMNDiagram id="Diagram_1">',
        f'    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="{process_id}">',
    ]
    for nid in sorted(positions):
        x, y, w, h = positions[nid]
        lines.append(f'      <bpmndi:BPMNShape id="S_{nid}" bpmnElement="{nid}">'
                     f'<dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" /></bpmndi:BPMNShape>')
    for fid in sorted(flows):
        src, tgt = flows[fid]
        if src not in positions or tgt not in positions:
            continue
        cx1, cy1 = center(positions[src])
        cx2, cy2 = center(positions[tgt])
        lines.append(f'      <bpmndi:BPMNEdge id="E_{fid}" bpmnElement="{fid}">'
                     f'<di:waypoint x="{cx1}" y="{cy1}" />'
                     f'<di:waypoint x="{cx2}" y="{cy2}" /></bpmndi:BPMNEdge>')
    lines += ['    </bpmndi:BPMNPlane>', '  </bpmndi:BPMNDiagram>']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate bpmndi:BPMNDiagram for a BPMN file')
    parser.add_argument('--bpmn', required=True, help='Input .bpmn file')
    parser.add_argument('--out', help='Output path (default: overwrite --bpmn)')
    args = parser.parse_args()

    try:
        tree = ET.parse(args.bpmn)
    except ET.ParseError as e:
        print(f'ERROR: XML parse failed: {e}', file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f'ERROR: File not found: {args.bpmn}', file=sys.stderr)
        sys.exit(1)

    root = tree.getroot()
    process_elem = root.find(f'{{{BPMN_NS}}}process')
    if process_elem is None:
        print('ERROR: No bpmn:process element found', file=sys.stderr)
        sys.exit(1)

    process_id = process_elem.get('id', 'Process_1')
    nodes, flows = collect_process(process_elem)

    if not nodes:
        print('ERROR: No flow nodes found in bpmn:process', file=sys.stderr)
        sys.exit(1)

    positions = compute_layout(nodes, flows)
    diagram_xml = build_diagram_xml(nodes, flows, positions, process_id)

    with open(args.bpmn, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(
        r'\s*<bpmndi:BPMNDiagram[\s\S]*?</bpmndi:BPMNDiagram>',
        '',
        content,
    )
    close_tag = '</bpmn:definitions>'
    if close_tag not in content:
        print(f'ERROR: Missing {close_tag} in file', file=sys.stderr)
        sys.exit(1)
    content = content.replace(close_tag, f'\n{diagram_xml}\n{close_tag}')

    out_path = args.out or args.bpmn
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Generated: {len(nodes)} shapes, {len(flows)} edges → {out_path}')


if __name__ == '__main__':
    main()
