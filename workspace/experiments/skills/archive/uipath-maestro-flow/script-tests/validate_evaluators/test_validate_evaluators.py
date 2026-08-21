"""Tests for validate_evaluators.py"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'validate_evaluators.py')
FIXTURES = os.path.dirname(__file__)

VALID_EXACT = os.path.join(FIXTURES, 'exact_match_valid.json')
VALID_LLM = os.path.join(FIXTURES, 'llm_judge_valid.json')


def run(*paths, dir_arg=None):
    cmd = [sys.executable, SCRIPT] + list(paths)
    if dir_arg:
        cmd += ['--dir', dir_arg]
    return subprocess.run(cmd, capture_output=True, text=True)


def write_json(tmp, name, data):
    path = os.path.join(tmp, name)
    with open(path, 'w') as f:
        json.dump(data, f)
    return path


def base_valid(type_id, model=None):
    d = {
        'id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'name': 'my-eval',
        'version': '1.0',
        'evaluatorTypeId': type_id,
        'evaluatorConfig': {'name': 'my-eval'},
    }
    if model:
        d['evaluatorConfig']['model'] = model
    return d


def test_valid_exact_match_passes():
    result = run(VALID_EXACT)
    assert result.returncode == 0, result.stdout


def test_valid_llm_judge_passes():
    result = run(VALID_LLM)
    assert result.returncode == 0, result.stdout


def test_both_valid_passes():
    result = run(VALID_EXACT, VALID_LLM)
    assert result.returncode == 0, result.stdout


def test_dir_scan_passes():
    result = run(dir_arg=FIXTURES)
    assert result.returncode == 0, result.stdout


def test_llm_judge_missing_model_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_json(tmp, 'e.json', base_valid('uipath-llm-judge-output-semantic-similarity'))
        result = run(path)
        assert result.returncode == 1
        assert 'model' in result.stdout


def test_llm_judge_empty_model_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d = base_valid('uipath-llm-judge-trajectory-similarity', model='')
        path = write_json(tmp, 'e.json', d)
        result = run(path)
        assert result.returncode == 1
        assert 'model' in result.stdout


def test_deterministic_with_model_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d = base_valid('uipath-exact-match', model='gpt-4.1-2025-04-14')
        path = write_json(tmp, 'e.json', d)
        result = run(path)
        assert result.returncode == 1
        assert 'model' in result.stdout


def test_invalid_type_id_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d = base_valid('ExactMatch')  # PascalCase — wrong
        path = write_json(tmp, 'e.json', d)
        result = run(path)
        assert result.returncode == 1
        assert 'evaluatorTypeId' in result.stdout


def test_missing_required_field_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d = base_valid('uipath-exact-match')
        del d['version']
        path = write_json(tmp, 'e.json', d)
        result = run(path)
        assert result.returncode == 1
        assert 'version' in result.stdout


def test_missing_evaluator_config_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d = base_valid('uipath-exact-match')
        del d['evaluatorConfig']
        path = write_json(tmp, 'e.json', d)
        result = run(path)
        assert result.returncode == 1


def test_duplicate_id_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d1 = base_valid('uipath-exact-match')
        d2 = base_valid('uipath-json-similarity')
        p1 = write_json(tmp, 'a.json', d1)
        p2 = write_json(tmp, 'b.json', d2)
        result = run(p1, p2)
        assert result.returncode == 1
        assert 'duplicate' in result.stdout


def test_all_seven_llm_types_require_model():
    llm_types = [
        'uipath-llm-judge-output-semantic-similarity',
        'uipath-llm-judge-output-strict-json-similarity',
        'uipath-llm-judge-trajectory-similarity',
        'uipath-llm-judge-trajectory-simulation',
    ]
    for type_id in llm_types:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_json(tmp, 'e.json', base_valid(type_id))
            result = run(path)
            assert result.returncode == 1, f'{type_id} should require model'


def test_all_three_deterministic_types_pass_without_model():
    det_types = ['uipath-exact-match', 'uipath-json-similarity', 'uipath-contains']
    for type_id in det_types:
        with tempfile.TemporaryDirectory() as tmp:
            d = base_valid(type_id)
            d['id'] = f'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
            path = write_json(tmp, 'e.json', d)
            result = run(path)
            assert result.returncode == 0, f'{type_id} should pass: {result.stdout}'


def test_invalid_json_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'bad.json')
        with open(path, 'w') as f:
            f.write('{not valid json')
        result = run(path)
        assert result.returncode == 1
        assert 'invalid JSON' in result.stdout


def test_missing_file_fails():
    result = run('/nonexistent/path.json')
    assert result.returncode == 1
    assert 'not found' in result.stdout


def test_no_args_exits_1():
    result = run()
    assert result.returncode == 1


if __name__ == '__main__':
    test_valid_exact_match_passes()
    test_valid_llm_judge_passes()
    test_both_valid_passes()
    test_dir_scan_passes()
    test_llm_judge_missing_model_fails()
    test_llm_judge_empty_model_fails()
    test_deterministic_with_model_fails()
    test_invalid_type_id_fails()
    test_missing_required_field_fails()
    test_missing_evaluator_config_fails()
    test_duplicate_id_fails()
    test_all_seven_llm_types_require_model()
    test_all_three_deterministic_types_pass_without_model()
    test_invalid_json_fails()
    test_missing_file_fails()
    test_no_args_exits_1()
    print('All tests passed.')
