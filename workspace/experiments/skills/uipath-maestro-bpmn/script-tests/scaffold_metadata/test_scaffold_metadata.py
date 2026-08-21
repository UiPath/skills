"""Tests for scaffold_metadata.py"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'scaffold_metadata.py')
FIXTURE = os.path.join(os.path.dirname(__file__), 'input.bpmn')


def run(bpmn_path, out_dir):
    return subprocess.run(
        [sys.executable, SCRIPT, '--bpmn', bpmn_path, '--out-dir', out_dir],
        capture_output=True, text=True,
    )


def load(out_dir, fname):
    with open(os.path.join(out_dir, fname), encoding='utf-8') as f:
        return json.load(f)


def test_writes_all_five_files():
    with tempfile.TemporaryDirectory() as tmp:
        result = run(FIXTURE, tmp)
        assert result.returncode == 0, result.stderr
        for fname in ('project.uiproj', 'operate.json', 'entry-points.json',
                      'bindings_v2.json', 'package-descriptor.json'):
            assert os.path.isfile(os.path.join(tmp, fname)), f'Missing {fname}'


def test_project_uiproj_fields():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'project.uiproj')
        assert data['ProjectType'] == 'ProcessOrchestration'
        assert data['Name'] == 'input'
        assert data['main'] == 'input.bpmn'


def test_operate_json():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'operate.json')
        assert data['main'] == 'input.bpmn'
        assert data['contentType'] == 'ProcessOrchestration'


def test_entry_points_id_and_file_path():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'entry-points.json')
        eps = data['entryPoints']
        assert len(eps) == 1
        ep = eps[0]
        assert ep['id'] == 'Entry_ManualStart'
        assert ep['filePath'] == '/content/input.bpmn#Start_1'


def test_entry_points_input_schema():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'entry-points.json')
        schema = data['entryPoints'][0]['inputSchema']
        assert schema['type'] == 'object'
        assert 'amount' in schema['properties']
        assert schema['properties']['amount']['type'] == 'number'


def test_entry_points_output_schema():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'entry-points.json')
        schema = data['entryPoints'][0]['outputSchema']
        assert 'result' in schema['properties']
        assert schema['properties']['result']['type'] == 'string'


def test_bindings_v2_shape():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'bindings_v2.json')
        assert data['version'] == '2.0'
        assert isinstance(data['resources'], list)


def test_package_descriptor_content():
    with tempfile.TemporaryDirectory() as tmp:
        run(FIXTURE, tmp)
        data = load(tmp, 'package-descriptor.json')
        content = set(data['content'])
        assert 'content/input.bpmn' in content
        assert 'content/entry-points.json' in content
        assert 'content/bindings_v2.json' in content
        assert 'content/operate.json' in content


def test_no_entry_points_for_plain_start_event():
    plain_bpmn = """\
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:uipath="http://uipath.org/schema/bpmn"
    id="D1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="P1" isExecutable="true">
    <bpmn:startEvent id="S1" name="Start" />
  </bpmn:process>
</bpmn:definitions>
"""
    import os, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        bpmn_path = os.path.join(tmp, 'plain.bpmn')
        with open(bpmn_path, 'w') as f:
            f.write(plain_bpmn)
        out_dir = os.path.join(tmp, 'out')
        result = run(bpmn_path, out_dir)
        assert result.returncode == 0
        data = load(out_dir, 'entry-points.json')
        assert data['entryPoints'] == []


def test_missing_bpmn_exits_1():
    result = run('/nonexistent/file.bpmn', '/tmp')
    assert result.returncode == 1


if __name__ == '__main__':
    test_writes_all_five_files()
    test_project_uiproj_fields()
    test_operate_json()
    test_entry_points_id_and_file_path()
    test_entry_points_input_schema()
    test_entry_points_output_schema()
    test_bindings_v2_shape()
    test_package_descriptor_content()
    test_no_entry_points_for_plain_start_event()
    test_missing_bpmn_exits_1()
    print('All tests passed.')
