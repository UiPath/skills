#!/usr/bin/env python3
"""Migrate legacy troubleshoot manifests to coder-eval protected mocks.

The default mode validates every legacy scenario without writing. Pass
``--apply`` to write ``data/uip-fixture.json``, update ``task.yaml``, move the
maintainer README out of the old response tree, and remove ``data/m``.

This is intentionally a one-way migration. It rejects ambiguous normalized
commands instead of silently choosing a legacy first-match rule.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_GLOB = "**/data/m/r/manifest.json"
NOISE_VALUE_FLAGS = frozenset({"--output"})


def _prune_doc_keys(node: object) -> object:
    if isinstance(node, dict):
        return {
            key: _prune_doc_keys(value)
            for key, value in node.items()
            if not (isinstance(key, str) and key.startswith("_"))
        }
    if isinstance(node, list):
        return [_prune_doc_keys(value) for value in node]
    return node


def _strip_doc_keys(text: str) -> str:
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return text
    pruned = _prune_doc_keys(parsed)
    if pruned == parsed:
        return text
    trailing = "\n" if text.endswith("\n") else ""
    return json.dumps(pruned, indent=2, ensure_ascii=False) + trailing


def _stdout(value: object) -> str:
    if isinstance(value, str):
        return _strip_doc_keys(value)
    return json.dumps(_prune_doc_keys(value), indent=2, ensure_ascii=False) + "\n"


def _argv(match: str) -> list[str]:
    try:
        argv = shlex.split(match, posix=True)
    except ValueError as exc:
        raise ValueError(f"invalid command match {match!r}: {exc}") from exc
    if not argv:
        raise ValueError("command match must not be empty")
    return argv


def _normalized_key(argv: list[str]) -> tuple[str, ...]:
    expanded: list[str] = []
    for raw in argv:
        if raw.startswith("-") and "=" in raw:
            flag, value = raw.split("=", 1)
            expanded.append(flag)
            if value:
                expanded.append(value)
        else:
            expanded.append(raw)

    cleaned: list[str] = []
    skip_next = False
    for token in expanded:
        if skip_next:
            skip_next = False
            continue
        if token in NOISE_VALUE_FLAGS:
            skip_next = True
            continue
        cleaned.append(token)
    return tuple(sorted(cleaned))


def _read_response(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def _build_fixture(manifest_path: Path) -> tuple[dict[str, object], bool]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != 2 or not isinstance(manifest.get("rules"), list):
        raise ValueError(f"{manifest_path}: expected a version 2 rules manifest")

    responses: list[dict[str, object]] = []
    by_key: dict[tuple[str, ...], dict[str, object]] = {}
    docsai_passthrough = False
    for index, rule in enumerate(manifest["rules"]):
        if not isinstance(rule, dict) or not isinstance(rule.get("match"), str):
            raise ValueError(f"{manifest_path}: rule {index} has no string match")
        if not rule["match"].strip():
            # Empty legacy matches were unreachable: the dispatcher rejected
            # them before either token or substring matching.
            continue
        argv = _argv(rule["match"])
        if rule.get("passthrough"):
            if argv != ["docsai", "ask"]:
                raise ValueError(f"{manifest_path}: unsupported passthrough command {argv!r}")
            docsai_passthrough = True
            continue
        filename = rule.get("file")
        if not isinstance(filename, str) or not filename:
            raise ValueError(f"{manifest_path}: rule {index} has neither file nor passthrough")
        response_path = manifest_path.parent / filename
        if not response_path.is_file():
            raise ValueError(f"{manifest_path}: missing response file {filename}")
        response: dict[str, object] = {
            "argv": argv,
            "match_mode": "normalized",
            "exit_code": int(rule.get("exit_code", 0)),
            "stdout": _strip_doc_keys(_read_response(response_path)),
        }
        key = _normalized_key(argv)
        previous = by_key.get(key)
        if previous is not None:
            comparable = {k: v for k, v in response.items() if k != "argv"}
            previous_comparable = {k: v for k, v in previous.items() if k != "argv"}
            if comparable != previous_comparable:
                raise ValueError(
                    f"{manifest_path}: normalized command conflict between "
                    f"{previous['argv']!r} and {argv!r}"
                )
            continue
        by_key[key] = response
        responses.append(response)

    default_raw = manifest.get("unmocked_default")
    if isinstance(default_raw, dict):
        default = {
            "exit_code": int(default_raw.get("exit_code", 0)),
            "stdout": _stdout(default_raw.get("response", "")),
        }
    else:
        default = {
            "exit_code": 1,
            "stderr": "protected mock: command is not configured\n",
        }

    fixture: dict[str, object] = {
        "version": 1,
        "responses": responses,
        "default": default,
    }
    expected_calls = manifest.get("expected_calls")
    if isinstance(expected_calls, list):
        fixture["expected_calls"] = expected_calls
    return fixture, docsai_passthrough


def _section_bounds(lines: list[str], name: str) -> tuple[int, int]:
    start = next((index for index, line in enumerate(lines) if line.rstrip("\r\n") == f"{name}:"), -1)
    if start < 0:
        raise ValueError(f"task.yaml has no {name} section")
    end = len(lines)
    top_level = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:")
    for index in range(start + 1, len(lines)):
        if top_level.match(lines[index]):
            end = index
            break
    return start, end


def _rewrite_task_yaml(text: str, docsai_passthrough: bool) -> str:
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    sandbox_start, sandbox_end = _section_bounds(lines, "sandbox")
    body = lines[sandbox_start + 1 : sandbox_end]

    cleaned: list[str] = []
    index = 0
    while index < len(body):
        line = body[index]
        stripped = line.strip()
        if stripped == "- type: template_dir" and index + 1 < len(body):
            path_line = body[index + 1]
            path = path_line.strip().removeprefix("path:").strip()
            if path == "data" or path.replace("\\", "/").endswith("_shared/mock_template"):
                index += 2
                continue
            cleaned.extend(
                [
                    f"    - type: template_dir{newline}",
                    f"      path: {path}{newline}",
                ]
            )
            index += 2
            continue
        if stripped.startswith("mock_path_dirs:"):
            if cleaned and "Prepend ./m" in cleaned[-1]:
                cleaned.pop()
            index += 1
            while index < len(body) and body[index].strip() == "- m":
                index += 1
            continue
        cleaned.append(line)
        index += 1

    for index, line in enumerate(cleaned):
        if line.strip() != "template_sources:":
            continue
        has_source = any(candidate.strip() == "- type: template_dir" for candidate in cleaned[index + 1 :])
        if not has_source:
            cleaned.pop(index)
        break

    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    protected = [
        f"  protected_mocks:{newline}",
        f"    - tool: uip{newline}",
        f"      fixture: data/uip-fixture.json{newline}",
        f"      max_requests: 100{newline}",
    ]
    if docsai_passthrough:
        protected.extend(
            [
                f"      passthrough_argv_prefixes:{newline}",
                f"        - [docsai, ask]{newline}",
            ]
        )
    sandbox = [f"sandbox:{newline}", *cleaned, *protected, newline]
    lines[sandbox_start:sandbox_end] = sandbox

    pre_start, pre_end = _section_bounds(lines, "pre_run")
    pre_run = "".join(lines[pre_start:pre_end])
    if "python m/seal" not in pre_run:
        raise ValueError("task.yaml pre_run does not contain the expected seal command")
    if len(re.findall(r"^  - command:", pre_run, flags=re.MULTILINE)) != 1:
        raise ValueError("task.yaml pre_run contains commands in addition to seal")
    del lines[pre_start:pre_end]
    return "".join(lines)


def _migrate(manifest_path: Path, *, apply: bool) -> tuple[int, bool]:
    fixture, docsai_passthrough = _build_fixture(manifest_path)
    task_dir = manifest_path.parents[3]
    task_path = task_dir / "task.yaml"
    task_text = task_path.read_text(encoding="utf-8")
    rewritten = _rewrite_task_yaml(task_text, docsai_passthrough)
    if not apply:
        return len(fixture["responses"]), docsai_passthrough  # type: ignore[arg-type]

    data_dir = task_dir / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "uip-fixture.json").write_text(
        json.dumps(fixture, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    task_path.write_text(rewritten, encoding="utf-8")

    old_readme = manifest_path.parent / "README.md"
    if old_readme.is_file():
        new_readme = task_dir / "README.md"
        if new_readme.exists():
            raise ValueError(f"{task_dir}: both legacy and task-root README exist")
        shutil.move(old_readme, new_readme)
    shutil.rmtree(task_dir / "data" / "m")
    return len(fixture["responses"]), docsai_passthrough  # type: ignore[arg-type]


def _repair_migrated_tasks(root: Path, *, apply: bool) -> int:
    """Remove legacy multiline mock paths and any empty source collection."""
    repaired = 0
    for task_path in root.glob("**/task.yaml"):
        text = task_path.read_text(encoding="utf-8")
        if "protected_mocks:" not in text:
            continue
        lines = text.splitlines(keepends=True)
        lines = [line for line in lines if line.strip() != "- m"]
        orphaned_source = next(
            (index for index, line in enumerate(lines) if line.startswith("  - type: template_dir")),
            None,
        )
        if orphaned_source is not None:
            newline = "\r\n" if lines[orphaned_source].endswith("\r\n") else "\n"
            lines.insert(orphaned_source, f"  template_sources:{newline}")
            index = orphaned_source + 1
            while index < len(lines) and not lines[index].startswith("  protected_mocks:"):
                if lines[index].startswith("  - type: template_dir"):
                    lines[index] = "  " + lines[index]
                elif lines[index].startswith("    path:"):
                    lines[index] = "  " + lines[index]
                index += 1
        filtered = "".join(lines)
        filtered = re.sub(
            r"^  template_sources:\r?\n(?=  protected_mocks:)",
            "",
            filtered,
            flags=re.MULTILINE,
        )
        if filtered == text:
            continue
        repaired += 1
        if apply:
            task_path.write_text(filtered, encoding="utf-8")
    return repaired


def _repair_readmes(root: Path, *, apply: bool) -> int:
    """Replace obsolete mock-layout descriptions with the protected boundary."""
    markers = (
        "mock_template",
        "manifest.json",
        "data/m/r",
        "mocks/uip",
        "m/uip",
        "mocks/responses",
        "mock dispatcher",
    )
    note = (
        "\n## Fixture isolation\n\n"
        "`data/uip-fixture.json` is a finite command/response map mounted only into "
        "coder-eval's host-side protected mock service. The evaluated agent receives a "
        "bounded `uip` client and cannot read the fixture or mock implementation.\n"
    )
    repaired = 0
    for readme_path in root.glob("**/README.md"):
        if "_shared" in readme_path.parts or not (readme_path.parent / "task.yaml").is_file():
            continue
        text = readme_path.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines(keepends=True) if not any(marker in line for marker in markers)]
        rewritten = "".join(lines).rstrip() + "\n"
        if "## Fixture isolation" not in rewritten:
            rewritten += note
        if rewritten == text:
            continue
        repaired += 1
        if apply:
            readme_path.write_text(rewritten, encoding="utf-8")
    return repaired


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    manifests = sorted(args.root.glob(MANIFEST_GLOB))
    response_count = 0
    passthrough_count = 0
    for manifest in manifests:
        responses, passthrough = _migrate(manifest, apply=args.apply)
        response_count += responses
        passthrough_count += int(passthrough)
    repaired = _repair_migrated_tasks(args.root, apply=args.apply)
    readmes = _repair_readmes(args.root, apply=args.apply)
    action = "Migrated" if args.apply else "Validated"
    print(
        f"{action} {len(manifests)} scenarios: {response_count} finite responses, "
        f"{passthrough_count} docsai passthrough configurations, "
        f"{repaired} migrated task YAML repairs, {readmes} README repairs"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
