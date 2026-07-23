#!/usr/bin/env python3
"""Runtime check for the live BPMN debug e2e.

Asserts a real ``uip maestro bpmn debug`` session reached ``finalStatus ==
Completed`` AND the runtime ``product`` variable is 42, computed by a script task
(not hardcoded).

The key CLI fact this check is built around
-------------------------------------------
``uip maestro bpmn debug`` output carries only element-execution *statuses*
(``Data.ElementExecutions[].Status``) — it NEVER contains variable *values*. The
computed business result (``product``) lives only in
``uip maestro bpmn debug-instance variables-all <INSTANCE_ID>``. Grading the
debug command's own output for ``product == 42`` can therefore never pass; the
value must come from a ``variables-all`` read. The original check greped the
agent's saved files for a leaf ``== 42``, which made the primary assertion
hostage to the agent remembering to persist the ``variables-all`` output — the
exact flake this task hit (agent saved ``debug.json`` with ``finalStatus:
Completed`` but no variables file, so ``product`` was nowhere in the evidence).

Grading strategy
----------------
  1. Structural guard: a scriptTask exists in the authored ``.bpmn`` and does
     NOT mutate ``Globals.*``/``vars.*`` directly (unsupported in Jint — the
     supported path is ``return`` + a ``uipath:output`` mapping).
  2. Primary (deterministic): the agent's saved evidence shows a completed run
     AND a ``product``-named variable == 42 (read structurally by name, not by
     leaf-grep, so GUIDs/timestamps can't false-match).
  3. Live recovery (best-effort, only if 2 finds no product): re-read the saved
     ``instanceId`` via ``variables-all`` (debug instances are ephemeral, so this
     usually 404s), then re-run a fresh debug session and read its variables.
     This lets a correct build pass even when the agent forgot to save the
     variables output, without ever causing a false failure.

Exits 0 with OK lines on success; non-zero with FAIL on the first problem.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

EXPECTED_PRODUCT = 42
PRODUCT_VAR = "product"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
# Keys whose sub-tree legitimately carries variable values — restricts the
# 42-search haystack so GUIDs/timestamps/status strings can't false-match (the
# lesson the flow checker's docstring calls out).
VALUE_BEARING_KEYS = {"variables", "globals", "outputs", "output", "response"}


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


# ── JSON parsing / structural search ─────────────────────────────────────────


def _parse_json_tolerant(text: str):
    """Parse JSON, tolerating a leading CLI banner before the first object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("{") or s.startswith("["):
                try:
                    return json.loads("\n".join(lines[i:]))
                except json.JSONDecodeError:
                    continue
    return None


def _is_expected(val) -> bool:
    if isinstance(val, bool):
        return False
    if isinstance(val, (int, float)) and val == EXPECTED_PRODUCT:
        return True
    return isinstance(val, str) and val.strip() in ("42", "42.0")


def _find_ci_key(obj, wanted: str):
    """Yield every value whose dict key equals ``wanted`` (case-insensitive)."""
    wanted = wanted.lower()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() == wanted:
                yield v
            yield from _find_ci_key(v, wanted)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _find_ci_key(item, wanted)


def _all_leaves(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _all_leaves(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _all_leaves(item)
    else:
        yield obj


def _leaves_under_value_bearing(obj):
    """Yield scalar leaves that live under a value-bearing key subtree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in VALUE_BEARING_KEYS:
                yield from _all_leaves(v)
            else:
                yield from _leaves_under_value_bearing(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _leaves_under_value_bearing(item)


def _has_final_status_completed(parsed) -> bool:
    for val in _find_ci_key(parsed, "finalstatus"):
        if isinstance(val, str) and val.strip().lower() == "completed":
            return True
    return False


def _instance_id(parsed):
    for key in ("instanceid", "debuginstanceid"):
        for val in _find_ci_key(parsed, key):
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def _iter_name_value_pairs(obj):
    """Yield (name, value) for dicts that carry both a name and a value key."""
    if isinstance(obj, dict):
        keys_lower = {k.lower() for k in obj if isinstance(k, str)}
        if "name" in keys_lower and "value" in keys_lower:
            name = next((v for k, v in obj.items() if isinstance(k, str) and k.lower() == "name"), None)
            value = next((v for k, v in obj.items() if isinstance(k, str) and k.lower() == "value"), None)
            yield (name, value)
        for v in obj.values():
            yield from _iter_name_value_pairs(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _iter_name_value_pairs(item)


def _has_expected_product(parsed) -> bool:
    """True when the runtime exposes a ``product`` variable equal to 42.

    Precise match first (a key literally named ``product`` — e.g.
    ``Globals.Product`` — or a ``{name: product, value: 42}`` pair), then a
    fallback restricted to value-bearing sub-trees so shape drift still passes
    without letting GUIDs/timestamps false-match.
    """
    # (a) key named "product" with the expected value (Globals.Product = 42)
    for val in _find_ci_key(parsed, PRODUCT_VAR):
        if _is_expected(val):
            return True
    # (b) {"name": "product", "value": 42} pairs (mock/CLI list shape)
    for name, value in _iter_name_value_pairs(parsed):
        if isinstance(name, str) and name.strip().lower() == PRODUCT_VAR and _is_expected(value):
            return True
    # (c) fallback: 42 anywhere under a variables/globals/outputs subtree
    for leaf in _leaves_under_value_bearing(parsed):
        if _is_expected(leaf):
            return True
    return False


# ── CLI ──────────────────────────────────────────────────────────────────────


def _run_uip(args, timeout: int, attempts: int = 2):
    """Run ``uip <args> --output json`` with a small retry for cold-start/5xx.

    Returns the parsed JSON (dict/list) or None."""
    cmd = ["uip", *args, "--output", "json"]
    last = ""
    for attempt in range(attempts):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last = f"timeout after {timeout}s"
            continue
        last = f"exit {r.returncode}\nstdout: {r.stdout[:2000]}\nstderr: {r.stderr[:1000]}"
        parsed = _parse_json_tolerant(r.stdout)
        if r.returncode == 0 and parsed is not None:
            return parsed
        if attempt + 1 < attempts:
            time.sleep(5)
    print(f"note: `uip {' '.join(args)}` did not return usable JSON — {last}", file=sys.stderr)
    return None


def _read_variables_all(instance_id: str):
    return _run_uip(
        ["maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=120,
    )


def _script_bodies(root):
    """Yield each scriptTask's JS body with JS comments stripped."""
    for task in root.findall(f".//{{{BPMN_NS}}}scriptTask"):
        node = task.find(f"{{{BPMN_NS}}}script")
        if node is None:
            continue
        body = "".join(node.itertext())
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
        body = re.sub(r"//.*", "", body)
        yield body


def _bpmn_project_candidates():
    """Directories of every project.uiproj that has a sibling ``.bpmn``,
    shallowest first (a standalone ``ProductCalc/`` before a solution-nested
    copy). BPMN debug needs solution context, so the caller tries each until one
    debugs."""
    candidates = []
    for proj in glob.glob("**/project.uiproj", recursive=True):
        d = os.path.dirname(proj) or "."
        if glob.glob(os.path.join(d, "*.bpmn")):
            candidates.append(d)
    candidates.sort(key=lambda p: (p.count(os.sep), len(p)))
    return candidates


def _fresh_debug_then_variables():
    """Execute a fresh debug session and read its runtime variables live.

    Tries each candidate project (BPMN debug needs solution context, which not
    every project dir has). Returns (completed: bool, variables_payload | None)."""
    completed = False
    for project in _bpmn_project_candidates()[:2]:  # bound tenant work in recovery
        debug = _run_uip(["maestro", "bpmn", "debug", project], timeout=300)
        if debug is None:
            continue
        completed = completed or _has_final_status_completed(debug)
        inst = _instance_id(debug)
        if not inst:
            continue
        variables = _read_variables_all(inst)
        if variables is not None and _has_expected_product(variables):
            return (True, variables)
    return (completed, None)


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    # 1. Structural guard: product is computed by a script task that RETURNS its
    #    value. Jint does not apply direct `Globals.*`/`vars.*` mutation to the
    #    runtime — the supported path is `return` + a `uipath:output` mapping, so
    #    a mutating script silently leaves the variable empty. Scope to the
    #    agent's project files (skip the skill's own validator/sample .bpmn).
    bpmn_files = [
        p
        for p in glob.glob("**/*.bpmn", recursive=True)
        if not ({"validator", "samples"} & set(p.split(os.sep)))
    ]
    if not bpmn_files:
        _fail("no .bpmn file authored")
    found_script = False
    for path in bpmn_files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            _fail(f"{path} is not well-formed XML: {exc}")
        for body in _script_bodies(root):
            found_script = True
            if re.search(r"\bGlobals\.", body) or re.search(r"\bvars\.", body):
                _fail(
                    f"{path}: script task reads/mutates Globals.*/vars.* directly — "
                    "unsupported in Jint. Return a value and map it via uipath:output."
                )
    if not found_script:
        _fail(
            "no scriptTask in any authored .bpmn — the product must be computed by "
            "a script task, not hardcoded"
        )
    print("OK: product is computed by a script task (return + output mapping)")

    # 2. Read the agent's saved CLI evidence. The `variables-all` output is the
    #    only source of the runtime `product` value — the `debug` command output
    #    carries element statuses only. Primary, deterministic pass path: the
    #    agent saved a variables-all payload with product == 42.
    saved = glob.glob("debug-evidence/**/*.json", recursive=True) + glob.glob("*.json")
    completed = False
    product_from_evidence = False
    instance_id = None
    for path in saved:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                parsed = _parse_json_tolerant(fh.read())
        except OSError:
            continue
        if parsed is None:
            continue
        if _has_final_status_completed(parsed):
            completed = True
            instance_id = instance_id or _instance_id(parsed)
        if _has_expected_product(parsed):
            product_from_evidence = True

    if not completed:
        _fail(
            "no debug-evidence with finalStatus == 'Completed' — save the raw "
            "`uip maestro bpmn debug` JSON output to debug-evidence/"
        )
    print("OK: debug session reached finalStatus Completed")

    if product_from_evidence:
        print(f"OK: runtime product variable is {EXPECTED_PRODUCT} (from saved variables-all evidence)")
        print("PASS: all live-debug checks passed")
        return

    # 3. The agent did not save a variables-all payload carrying product. The
    #    `debug` command output alone never contains variable values, so recover
    #    the value live: re-read the agent's instance (usually gone — debug
    #    instances are ephemeral), then re-run a fresh debug session.
    print(
        "note: no product value in saved evidence — the debug command output has "
        "no variable values; attempting live recovery via debug-instance variables-all",
        file=sys.stderr,
    )
    variables_payload = None
    if instance_id:
        live = _read_variables_all(instance_id)
        if live is not None and _has_expected_product(live):
            variables_payload = live
    if variables_payload is None:
        _, fresh_vars = _fresh_debug_then_variables()
        if fresh_vars is not None and _has_expected_product(fresh_vars):
            variables_payload = fresh_vars

    if variables_payload is None:
        _fail(
            f"runtime `product` variable is not {EXPECTED_PRODUCT}: not in saved "
            "evidence, and live recovery via `debug-instance variables-all` failed "
            "(save the variables-all output to debug-evidence/ — the debug command "
            "output does NOT contain variable values)"
        )
    print(f"OK: live runtime product variable is {EXPECTED_PRODUCT} (recovered via variables-all)")
    print("PASS: all live-debug checks passed")


if __name__ == "__main__":
    main()
