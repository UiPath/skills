"""Tests for check_metadata_drift.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'check_metadata_drift.py')
VALID_DIR = os.path.join(os.path.dirname(__file__), 'valid')
VALID_BPMN = os.path.join(VALID_DIR, 'input.bpmn')


def run(bpmn, project_dir):
    return subprocess.run(
        [sys.executable, SCRIPT, '--bpmn', bpmn, '--project-dir', project_dir],
        capture_output=True, text=True,
    )


def copy_valid(tmp):
    for fname in os.listdir(VALID_DIR):
        shutil.copy(os.path.join(VALID_DIR, fname), os.path.join(tmp, fname))


def test_valid_passes():
    result = run(VALID_BPMN, VALID_DIR)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'OK' in result.stdout


def test_wrong_entry_point_id_fails():
    with tempfile.TemporaryDirectory() as tmp:
        copy_valid(tmp)
        ep_path = os.path.join(tmp, 'entry-points.json')
        with open(ep_path) as f:
            data = json.load(f)
        data['entryPoints'][0]['id'] = 'WrongId'
        with open(ep_path, 'w') as f:
            json.dump(data, f)
        result = run(os.path.join(tmp, 'input.bpmn'), tmp)
        assert result.returncode == 1
        assert 'DRIFT' in result.stdout


def test_wrong_file_path_fails():
    with tempfile.TemporaryDirectory() as tmp:
        copy_valid(tmp)
        ep_path = os.path.join(tmp, 'entry-points.json')
        with open(ep_path) as f:
            data = json.load(f)
        data['entryPoints'][0]['filePath'] = '/content/input.bpmn#Wrong_Event'
        with open(ep_path, 'w') as f:
            json.dump(data, f)
        result = run(os.path.join(tmp, 'input.bpmn'), tmp)
        assert result.returncode == 1
        assert 'DRIFT' in result.stdout


def test_wrong_bindings_version_fails():
    with tempfile.TemporaryDirectory() as tmp:
        copy_valid(tmp)
        b_path = os.path.join(tmp, 'bindings_v2.json')
        with open(b_path, 'w') as f:
            json.dump({'version': '1.0', 'resources': []}, f)
        result = run(os.path.join(tmp, 'input.bpmn'), tmp)
        assert result.returncode == 1
        assert 'DRIFT' in result.stdout


def test_wrong_operate_main_fails():
    with tempfile.TemporaryDirectory() as tmp:
        copy_valid(tmp)
        o_path = os.path.join(tmp, 'operate.json')
        with open(o_path, 'w') as f:
            json.dump({'main': 'wrong.bpmn', 'contentType': 'ProcessOrchestration'}, f)
        result = run(os.path.join(tmp, 'input.bpmn'), tmp)
        assert result.returncode == 1
        assert 'DRIFT' in result.stdout


def test_missing_bpmn_entry_in_descriptor_fails():
    with tempfile.TemporaryDirectory() as tmp:
        copy_valid(tmp)
        d_path = os.path.join(tmp, 'package-descriptor.json')
        with open(d_path, 'w') as f:
            json.dump({'content': ['content/bindings_v2.json', 'content/entry-points.json', 'content/operate.json']}, f)
        result = run(os.path.join(tmp, 'input.bpmn'), tmp)
        assert result.returncode == 1
        assert 'DRIFT' in result.stdout


def test_missing_metadata_file_fails():
    with tempfile.TemporaryDirectory() as tmp:
        copy_valid(tmp)
        os.remove(os.path.join(tmp, 'operate.json'))
        result = run(os.path.join(tmp, 'input.bpmn'), tmp)
        assert result.returncode == 1
        assert 'DRIFT' in result.stdout or 'MISSING' in result.stdout


def test_missing_bpmn_exits_1():
    result = run('/nonexistent.bpmn', VALID_DIR)
    assert result.returncode == 1


if __name__ == '__main__':
    test_valid_passes()
    test_wrong_entry_point_id_fails()
    test_wrong_file_path_fails()
    test_wrong_bindings_version_fails()
    test_wrong_operate_main_fails()
    test_missing_bpmn_entry_in_descriptor_fails()
    test_missing_metadata_file_fails()
    test_missing_bpmn_exits_1()
    print('All tests passed.')
