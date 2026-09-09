#!/usr/bin/env python3
"""Validate advanced local `uip maestro flow eval` artifacts.

This checker intentionally inspects files rather than command stdout. It proves
that the agent did more than run commands: the evaluator JSON and eval-set JSON
must contain generated evaluator refs, a pinned entry point, search text,
trajectory criteria, and a staged file-input reference.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path("EvalAdvanced")
MODEL = "gpt-4.1-2025-04-14"

EXPECTED_TYPES = {
    "uipath-llm-judge-output-strict-json-similarity",
    "uipath-llm-judge-trajectory-similarity",
    "uipath-llm-judge-trajectory-simulation",
    "uipath-contains",
}
DISPLAY_NAMES = {
    "strict-json-evaluator",
    "trajectory-evaluator",
    "trajectory-simulation-evaluator",
    "contains-evaluator",
}
SEARCH_TEXT_KEYS = {"searchtext"}
TRAJECTORY_KEYS = {"expectedagentbehavior"}
FILE_REF_KEYS = {
    "file",
    "files",
    "filepath",
    "filepaths",
    "inputfile",
    "inputfiles",
    "attachment",
    "attachments",
}
PATH_LIKE_RE = re.compile(r"(?:^|[./\\])[\w .-]+\.[A-Za-z0-9]{2,8}\b")
NON_FIXTURE_SUFFIXES = (".json", ".flow", ".bpmn")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load_jsons(root: Path) -> list[tuple[Path, Any]]:
    docs: list[tuple[Path, Any]] = []
    for path in root.rglob("*.json"):
        try:
            docs.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return docs


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def has_nonempty_key(value: Any, normalized_keys: set[str]) -> bool:
    for item in walk(value):
        if not isinstance(item, dict):
            continue
        for key, child in item.items():
            if normalize_key(key) in normalized_keys and meaningful(child):
                return True
    return False


def contains_fixture_path(value: Any) -> bool:
    for item in walk(value):
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        match = PATH_LIKE_RE.search(text)
        if match and not match.group(0).lower().endswith(NON_FIXTURE_SUFFIXES):
            return True
    return False


def has_staged_file_reference(value: Any) -> bool:
    for item in walk(value):
        if not isinstance(item, dict):
            continue
        for key, child in item.items():
            if normalize_key(key) in FILE_REF_KEYS and meaningful(child):
                return True
    return contains_fixture_path(value)


def evaluator_type(doc: Any) -> str | None:
    if not isinstance(doc, dict):
        return None
    return doc.get("evaluatorTypeId") or doc.get("typeId")


def model_value(doc: dict) -> str | None:
    cfg = doc.get("evaluatorConfig")
    if isinstance(cfg, dict):
        return cfg.get("model") or cfg.get("modelName")
    return doc.get("model") or doc.get("modelName")


def main() -> None:
    if not ROOT.is_dir():
        fail(f"{ROOT} directory does not exist")
    docs = load_jsons(ROOT)
    if not docs:
        fail(f"no JSON files found under {ROOT}")

    found_types: set[str] = set()
    found_evaluator_ids: set[str] = set()
    llm_without_model: list[str] = []
    for path, doc in docs:
        etype = evaluator_type(doc)
        if etype in EXPECTED_TYPES:
            found_types.add(etype)
            if isinstance(doc.get("id"), str):
                found_evaluator_ids.add(doc["id"])
            if "llm-judge" in etype and model_value(doc) != MODEL:
                llm_without_model.append(f"{path}: model={model_value(doc)!r}")

    missing = EXPECTED_TYPES - found_types
    if missing:
        fail(f"missing evaluator type(s): {sorted(missing)}")
    if llm_without_model:
        fail("LLM evaluator(s) missing required model: " + " | ".join(llm_without_model))
    print(f"OK: found advanced evaluator types: {sorted(found_types)}")

    eval_sets = [
        (p, d)
        for p, d in docs
        if isinstance(d, dict)
        and d.get("name") == "Advanced Set"
        and isinstance(d.get("evaluations"), list)
    ]
    if not eval_sets:
        fail('no eval set named "Advanced Set" found')
    set_path, eval_set = eval_sets[0]

    entry = eval_set.get("selectedEntrypoint") or eval_set.get("entryPoint")
    if not entry:
        fail(f"{set_path} has no selectedEntrypoint/entryPoint")

    refs = eval_set.get("evaluatorRefs")
    if not isinstance(refs, list) or len(refs) < 4:
        fail(f"{set_path} should reference at least 4 evaluators, got {refs!r}")
    bad_refs = [
        r
        for r in refs
        if str(r) in DISPLAY_NAMES
        or (str(r) not in found_evaluator_ids and not str(r).endswith(".json"))
    ]
    if bad_refs:
        fail(
            "evaluatorRefs should use generated evaluator ids/file refs, "
            f"not display names: {bad_refs!r}"
        )
    print(
        f"OK: {set_path} pins entry point {entry!r} and uses generated "
        "evaluator ids/file refs"
    )

    if not has_nonempty_key(eval_set, SEARCH_TEXT_KEYS):
        fail("eval set does not contain non-empty contains search-text criteria")
    if not has_nonempty_key(eval_set, TRAJECTORY_KEYS):
        fail("eval set does not contain non-empty trajectory expectedAgentBehavior criteria")
    if not has_staged_file_reference(eval_set):
        fail("eval set does not contain a staged input-file reference")

    cases = eval_set.get("evaluations") or []
    if len(cases) < 3:
        fail(f"expected at least 3 data points, got {len(cases)}")
    print(
        "OK: eval set contains search text, trajectory criteria, input-file "
        f"metadata, and {len(cases)} data points"
    )


if __name__ == "__main__":
    main()
