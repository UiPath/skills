#!/usr/bin/env python3
"""Verify that a delegated Case QuickForm is mirrored into runtime task I/O."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON from {path}: {exc}")


def iter_action_tasks(value: object):
    if isinstance(value, dict):
        if value.get("type") == "action" and isinstance(value.get("data"), dict):
            yield value
        for child in value.values():
            yield from iter_action_tasks(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_action_tasks(child)


def iter_registry_entries(value: object):
    if isinstance(value, dict):
        if "task" in value and "taskType" in value:
            yield value
        for child in value.values():
            yield from iter_registry_entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_registry_entries(child)


def context_by_name(task: dict) -> dict[str, dict]:
    context = task.get("data", {}).get("context", [])
    if not isinstance(context, list):
        fail("QuickForm task data.context must be an array")
    return {
        item.get("name"): item
        for item in context
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }


def matching_sidecar(caseplan_path: Path, schema_id: str) -> tuple[Path, dict]:
    for path in caseplan_path.parent.glob("*.hitl.json"):
        content = load_json(path)
        if isinstance(content, dict) and content.get("schemaId") == schema_id:
            return path, content
    fail(f"no .hitl.json beside {caseplan_path} has schemaId={schema_id!r}")


def as_named_map(entries: object, label: str) -> dict[str, dict]:
    if not isinstance(entries, list):
        fail(f"{label} must be an array")
    result: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            fail(f"{label} contains an entry without a string name")
        name = entry["name"]
        if name in result:
            fail(f"{label} contains duplicate name {name!r}")
        result[name] = entry
    return result


def allowed_runtime_types(native_type: str) -> set[str]:
    return {
        "text": {"string"},
        "number": {"number", "integer", "float", "double"},
        "boolean": {"boolean"},
        "date": {"date"},
        "dateTime": {"datetime"},
    }.get(native_type, {"string"})


def verify_caseplan(caseplan_path: Path) -> tuple[dict, dict]:
    plan = load_json(caseplan_path)
    actions = list(iter_action_tasks(plan))
    quick_actions = []
    for task in actions:
        context = context_by_name(task)
        if context.get("hitlType", {}).get("value") == "quick":
            quick_actions.append(task)
    if len(quick_actions) != 1:
        fail(f"expected exactly one QuickForm action task, found {len(quick_actions)}")

    task = quick_actions[0]
    data = task["data"]
    context = context_by_name(task)
    schema_id = context.get("hitlSchemaId", {}).get("value")
    if not isinstance(schema_id, str) or not schema_id:
        fail("QuickForm task is missing context[hitlSchemaId].value")

    sidecar_path, sidecar = matching_sidecar(caseplan_path, schema_id)
    fields = sidecar.get("fields")
    if not isinstance(fields, list) or not fields:
        fail(f"{sidecar_path} has no fields")

    expected_inputs = {
        field["id"]: field
        for field in fields
        if isinstance(field, dict) and field.get("direction") in {"input", "inOut"}
    }
    expected_outputs = {
        field["id"]: field
        for field in fields
        if isinstance(field, dict) and field.get("direction") in {"output", "inOut"}
    }
    runtime_inputs = as_named_map(data.get("inputs"), "task.data.inputs")
    runtime_outputs = as_named_map(data.get("outputs"), "task.data.outputs")

    if set(runtime_inputs) != set(expected_inputs):
        fail(
            "task.data.inputs names do not equal sidecar input/inOut field IDs: "
            f"actual={sorted(runtime_inputs)}, expected={sorted(expected_inputs)}"
        )
    if set(runtime_outputs) != set(expected_outputs):
        fail(
            "task.data.outputs names do not equal sidecar output/inOut field IDs: "
            f"actual={sorted(runtime_outputs)}, expected={sorted(expected_outputs)}"
        )

    for name, field in expected_inputs.items():
        runtime = runtime_inputs[name]
        binding = field.get("binding")
        if runtime.get("value") != binding:
            fail(f"input {name!r} value must copy sidecar binding {binding!r}")
        slot_id = runtime.get("id")
        if not isinstance(slot_id, str) or not slot_id.startswith("v") or len(slot_id) != 9:
            fail(f"input {name!r} id must be v + 8 characters, got {slot_id!r}")
        if runtime.get("var") != slot_id:
            fail(f"input {name!r} var must mirror id")
        if runtime.get("type") not in allowed_runtime_types(str(field.get("type"))):
            fail(
                f"input {name!r} uses sidecar/native type {runtime.get('type')!r} "
                "instead of a Case runtime type"
            )
        if runtime.get("elementId") != task.get("elementId"):
            fail(f"input {name!r} elementId does not match its task")

    for name, field in expected_outputs.items():
        runtime = runtime_outputs[name]
        variable = field.get("variable")
        if not isinstance(variable, str) or not variable:
            fail(f"sidecar output/inOut field {name!r} has no variable")
        expected = {
            "id": variable,
            "var": variable,
            "value": variable,
            "source": f"={name}",
            "target": f"={variable}",
            "elementId": task.get("elementId"),
        }
        for key, expected_value in expected.items():
            if runtime.get(key) != expected_value:
                fail(
                    f"output {name!r} {key}={runtime.get(key)!r}; "
                    f"expected {expected_value!r}"
                )
        if runtime.get("type") not in allowed_runtime_types(str(field.get("type"))):
            fail(f"output {name!r} does not use a Case runtime type")

    if "name" in data or "folderPath" in data:
        fail("QuickForm task must not have deployed-app name/folderPath bindings")

    registry_path = Path("tasks/registry-resolved.json")
    if registry_path.exists():
        registry = load_json(registry_path)
        task_name = task.get("displayName")
        if any(entry.get("task") == task_name for entry in iter_registry_entries(registry)):
            fail("QuickForm task must not have a registry-resolved.json entry")

    return task, sidecar


def collect_bpmn_text_from_archive(payload: bytes, label: str) -> list[str]:
    texts: list[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                child = archive.read(info)
                lower = info.filename.lower()
                if lower.endswith(".bpmn"):
                    texts.append(child.decode("utf-8", errors="replace"))
                elif lower.endswith((".zip", ".nupkg")):
                    texts.extend(
                        collect_bpmn_text_from_archive(child, f"{label}!{info.filename}")
                    )
    except zipfile.BadZipFile as exc:
        fail(f"cannot inspect packed archive {label}: {exc}")
    return texts


def verify_packed_runtime(solution_dir: Path, task: dict, sidecar: dict) -> None:
    uip = shutil.which("uip")
    if not uip:
        fail("uip CLI is not on PATH")

    with tempfile.TemporaryDirectory(prefix="quickform-runtime-io-") as output_dir:
        result = subprocess.run(
            [uip, "solution", "pack", str(solution_dir), output_dir, "--output", "json"],
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        if result.returncode != 0:
            fail(
                "uip solution pack failed: "
                + (result.stderr.strip() or result.stdout.strip() or "no output")
            )

        bpmn_texts: list[str] = []
        output_path = Path(output_dir)
        for path in output_path.rglob("*.bpmn"):
            bpmn_texts.append(path.read_text(encoding="utf-8", errors="replace"))
        for path in output_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".zip", ".nupkg"}:
                bpmn_texts.extend(collect_bpmn_text_from_archive(path.read_bytes(), str(path)))

    hitl_bpmn = [text for text in bpmn_texts if "HitlTaskArguments" in text]
    if not hitl_bpmn:
        fail("packed solution contains no BPMN HitlTaskArguments mapping")
    packed = "\n".join(hitl_bpmn)

    for field in sidecar.get("fields", []):
        if not isinstance(field, dict):
            continue
        direction = field.get("direction")
        field_id = field.get("id")
        if direction in {"input", "inOut"}:
            binding = field.get("binding")
            if field_id not in packed or binding not in packed:
                fail(
                    f"packed HitlTaskArguments is missing input {field_id!r} "
                    f"or binding {binding!r}"
                )
        if direction in {"output", "inOut"}:
            variable = field.get("variable")
            required_fragments = [
                f'name="{field_id}"',
                f'source="={field_id}"',
                f'target="={variable}"',
            ]
            missing = [fragment for fragment in required_fragments if fragment not in packed]
            if missing:
                fail(f"packed output {field_id!r} is missing {missing}")

    print(
        "OK: delegated QuickForm sidecar matches task runtime I/O and packed BPMN "
        f"for {task.get('displayName')!r}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("caseplan", type=Path)
    parser.add_argument("--solution", type=Path)
    parser.add_argument("--pack", action="store_true")
    args = parser.parse_args()

    if not args.caseplan.is_file():
        fail(f"caseplan not found: {args.caseplan}")
    task, sidecar = verify_caseplan(args.caseplan)
    if args.pack:
        if args.solution is None or not args.solution.is_dir():
            fail("--pack requires an existing --solution directory")
        verify_packed_runtime(args.solution, task, sidecar)
    else:
        print("OK: delegated QuickForm sidecar matches task runtime I/O")


if __name__ == "__main__":
    main()
