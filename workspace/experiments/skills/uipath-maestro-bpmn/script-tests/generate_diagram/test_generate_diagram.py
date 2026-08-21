"""Tests for generate_diagram.py"""
import os
import shutil
import subprocess
import sys
import tempfile

import defusedxml.ElementTree as ET

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'generate_diagram.py')
FIXTURE = os.path.join(os.path.dirname(__file__), 'input_no_diagram.bpmn')

BPMNDI = 'http://www.omg.org/spec/BPMN/20100524/DI'
DC = 'http://www.omg.org/spec/DD/20100524/DC'


def run(bpmn_path, out_path=None):
    cmd = [sys.executable, SCRIPT, '--bpmn', bpmn_path]
    if out_path:
        cmd += ['--out', out_path]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_generates_shapes_and_edges():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'out.bpmn')
        result = run(FIXTURE, out)
        assert result.returncode == 0, result.stderr

        tree = ET.parse(out)
        root = tree.getroot()
        diagram = root.find(f'{{{BPMNDI}}}BPMNDiagram')
        assert diagram is not None, 'BPMNDiagram element missing'

        plane = diagram.find(f'{{{BPMNDI}}}BPMNPlane')
        assert plane is not None

        shapes = plane.findall(f'{{{BPMNDI}}}BPMNShape')
        edges = plane.findall(f'{{{BPMNDI}}}BPMNEdge')

        shape_elements = {s.get('bpmnElement') for s in shapes}
        assert 'Start_1' in shape_elements
        assert 'Task_1' in shape_elements
        assert 'End_1' in shape_elements
        assert len(shapes) == 3

        edge_elements = {e.get('bpmnElement') for e in edges}
        assert 'Flow_1' in edge_elements
        assert 'Flow_2' in edge_elements
        assert len(edges) == 2


def test_correct_node_sizes():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'out.bpmn')
        run(FIXTURE, out)

        tree = ET.parse(out)
        root = tree.getroot()
        plane = root.find(f'.//{{{BPMNDI}}}BPMNPlane')

        sizes = {}
        for shape in plane.findall(f'{{{BPMNDI}}}BPMNShape'):
            bounds = shape.find(f'{{{DC}}}Bounds')
            elem_id = shape.get('bpmnElement')
            sizes[elem_id] = (int(bounds.get('width')), int(bounds.get('height')))

        assert sizes['Start_1'] == (36, 36), f'startEvent size wrong: {sizes["Start_1"]}'
        assert sizes['Task_1'] == (100, 80), f'task size wrong: {sizes["Task_1"]}'
        assert sizes['End_1'] == (36, 36), f'endEvent size wrong: {sizes["End_1"]}'


def test_left_to_right_ordering():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'out.bpmn')
        run(FIXTURE, out)

        tree = ET.parse(out)
        root = tree.getroot()
        plane = root.find(f'.//{{{BPMNDI}}}BPMNPlane')

        x_by_elem = {}
        for shape in plane.findall(f'{{{BPMNDI}}}BPMNShape'):
            bounds = shape.find(f'{{{DC}}}Bounds')
            x_by_elem[shape.get('bpmnElement')] = int(bounds.get('x'))

        assert x_by_elem['Start_1'] < x_by_elem['Task_1'] < x_by_elem['End_1'], \
            f'Not left-to-right: {x_by_elem}'


def test_replaces_existing_diagram():
    with tempfile.TemporaryDirectory() as tmp:
        bpmn_with_diagram = os.path.join(tmp, 'test.bpmn')
        shutil.copy(FIXTURE, bpmn_with_diagram)

        run(bpmn_with_diagram)
        run(bpmn_with_diagram)

        tree = ET.parse(bpmn_with_diagram)
        root = tree.getroot()
        diagrams = root.findall(f'{{{BPMNDI}}}BPMNDiagram')
        assert len(diagrams) == 1, f'Expected 1 diagram, got {len(diagrams)}'


def test_missing_file_exits_1():
    result = run('/nonexistent/path.bpmn')
    assert result.returncode == 1
    assert 'ERROR' in result.stderr


if __name__ == '__main__':
    test_generates_shapes_and_edges()
    test_correct_node_sizes()
    test_left_to_right_ordering()
    test_replaces_existing_diagram()
    test_missing_file_exits_1()
    print('All tests passed.')
