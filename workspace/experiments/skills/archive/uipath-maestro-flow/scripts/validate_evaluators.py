#!/usr/bin/env python3
"""
Validate evaluator JSON files for uipath-maestro-flow eval sets.

Checks each file against the rules in evaluators-guide.md:
- Required top-level fields (id, name, version, evaluatorTypeId, evaluatorConfig)
- evaluatorTypeId is one of the 7 valid internal values
- LLM-judge types have a non-empty evaluatorConfig.model
- Deterministic types do not carry evaluatorConfig.model
- No duplicate id values across the set of files (copy-paste guard)

Usage:
  python3 validate_evaluators.py <file.json> [<file2.json> ...]
  python3 validate_evaluators.py --dir <directory>

Args:
  files         One or more evaluator JSON file paths
  --dir         Scan a directory for all *.json files instead

Exit codes:
  0  All files pass
  1  One or more files fail (findings printed to stdout)
"""
import argparse
import glob
import json
import os
import sys

VALID_TYPE_IDS = {
    'uipath-exact-match',
    'uipath-json-similarity',
    'uipath-contains',
    'uipath-llm-judge-output-semantic-similarity',
    'uipath-llm-judge-output-strict-json-similarity',
    'uipath-llm-judge-trajectory-similarity',
    'uipath-llm-judge-trajectory-simulation',
}

LLM_JUDGE_TYPE_IDS = {
    'uipath-llm-judge-output-semantic-similarity',
    'uipath-llm-judge-output-strict-json-similarity',
    'uipath-llm-judge-trajectory-similarity',
    'uipath-llm-judge-trajectory-simulation',
}

DETERMINISTIC_TYPE_IDS = {
    'uipath-exact-match',
    'uipath-json-similarity',
    'uipath-contains',
}

REQUIRED_FIELDS = ['id', 'name', 'version', 'evaluatorTypeId', 'evaluatorConfig']


def validate_file(path, data):
    errors = []

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        errors.append(f'missing required fields: {", ".join(missing)}')
        return errors

    type_id = data['evaluatorTypeId']
    if type_id not in VALID_TYPE_IDS:
        errors.append(
            f'evaluatorTypeId={type_id!r} is not valid; '
            f'must be one of: {", ".join(sorted(VALID_TYPE_IDS))}'
        )

    cfg = data['evaluatorConfig']
    if not isinstance(cfg, dict):
        errors.append('evaluatorConfig must be an object')
        return errors

    model = cfg.get('model')

    if type_id in LLM_JUDGE_TYPE_IDS:
        if not model or not isinstance(model, str) or not model.strip():
            errors.append(
                f'evaluatorTypeId={type_id!r} is an llm-judge type — '
                'evaluatorConfig.model must be a non-empty string '
                '(omitting model causes a 500 from the LLM gateway)'
            )

    if type_id in DETERMINISTIC_TYPE_IDS and model:
        errors.append(
            f'evaluatorTypeId={type_id!r} is a deterministic type — '
            'evaluatorConfig.model must not be set'
        )

    if not data.get('id') or not isinstance(data.get('id'), str):
        errors.append('id must be a non-empty string (use a UUID)')

    return errors


def main():
    parser = argparse.ArgumentParser(
        description='Validate evaluator JSON files against evaluators-guide.md rules'
    )
    parser.add_argument('files', nargs='*', help='Evaluator JSON file paths')
    parser.add_argument('--dir', help='Directory to scan for *.json files')
    args = parser.parse_args()

    paths = list(args.files)
    if args.dir:
        paths += sorted(glob.glob(os.path.join(args.dir, '*.json')))

    if not paths:
        print('ERROR: no files specified — pass file paths or --dir', file=sys.stderr)
        sys.exit(1)

    failures = []
    seen_ids = {}
    all_data = []

    for path in paths:
        if not os.path.isfile(path):
            print(f'FAIL [{path}]: file not found')
            failures.append(path)
            continue
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f'FAIL [{path}]: invalid JSON — {e}')
            failures.append(path)
            continue

        errors = validate_file(path, data)
        if errors:
            for err in errors:
                print(f'FAIL [{path}]: {err}')
            failures.append(path)
        else:
            all_data.append((path, data))

    for path, data in all_data:
        eid = data.get('id', '')
        if eid in seen_ids:
            print(
                f'FAIL [{path}]: duplicate id={eid!r} also found in {seen_ids[eid]} '
                '(regenerate UUID before reusing across projects)'
            )
            failures.append(path)
        else:
            seen_ids[eid] = path

    if failures:
        print(f'\n{len(failures)} file(s) failed, {len(paths) - len(failures)} passed')
        sys.exit(1)

    print(f'OK: {len(paths)} file(s) passed')


if __name__ == '__main__':
    main()
