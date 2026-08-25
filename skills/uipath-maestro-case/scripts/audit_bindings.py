#!/usr/bin/env python3
"""Deterministic bindings-sidecar audit for a Maestro Case project (Step 12 Checks 7 + 11).

Executable form of the sidecar-parity and resourceKey checks. Prose checks get
transcribed into a plan and not executed; this one exits non-zero.

`bindings_v2.json` is a projection of `caseplan.json` `bindings[]` in a
DIFFERENT shape: the caseplan stores two entries per resource (one per
property), the sidecar stores one entry per resource with properties nested
under `value`. Dumping `bindings[]` verbatim is the common failure and it is
invisible to `uip maestro case validate`, which returns `Valid` either way.
`uip solution resources refresh` is the only consumer, so a wrong shape
surfaces at deploy or debug, long after a clean validate.

Checks
    1  sidecar entry SHAPE     one entry per resource: `key` + nested
                               `value.<prop>.defaultValue`
    2  grouped parity          distinct caseplan `resourceKey`s == sidecar `key`s
    3  resourceKey consistency `resourceKey == "<folderPath>.<name>"` from the
                               pair's own defaults — never a tenant identity

Scope is deliberately the two on-disk artifacts that exist at the Phase 3 gate.
Connection emission (`resources/*/connection/**`) is NOT checked here: those
files are created by `uip solution resources refresh`, which runs at Phase 5/6/7,
so asserting them at Phase 3 would fail every connector build. That chain is
covered by `scripts/check_connection_parity.py` before pack/publish.

Read-only, stdlib only. Exit 0 = clean, 1 = numbered findings, 2 = no caseplan
found (wrong path — not a pass), 3 = usage error.

Usage:
    audit_bindings.py <solutionDir> [--quiet]
"""

from __future__ import annotations

import json
import pathlib
import sys

INLINE_SIBLING_SENTINEL = "solution_folder"
PAIR_ATTRS = ("name", "folderpath")


def _load(path: pathlib.Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _abort(f"cannot read {path}: {exc}")
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        _abort(f"{path} is not valid JSON: {exc}")
    if not isinstance(doc, dict):
        _abort(f"{path} is not a JSON object (got {type(doc).__name__})")
    return doc


def _abort(detail: str):
    """Unreadable input is a finding, not a bare stderr line — Check 7 tells the
    agent to quote the verdict and repair numbered findings."""
    print("AUDIT FAIL: caseplan bindings[] and bindings_v2.json could not be read.")
    print(f"  1. {detail}")
    raise SystemExit(1)


def _bindings(plan) -> list[dict]:
    raw = plan.get("bindings")
    return [b for b in raw if isinstance(b, dict)] if isinstance(raw, list) else []


def _attr(binding: dict) -> str:
    """Lowercased propertyAttribute — a casing typo must not evade the checks."""
    return str(binding.get("propertyAttribute", "")).lower()


def _check_sidecar_shape(resources: list, project: str, out: list[str]) -> None:
    """Check 1 — one entry per resource: a `key` plus a non-empty nested `value`.

    Structural only. Asserting individual `value.<prop>.defaultValue` keys
    false-fires on product-authored sidecars, which legitimately omit
    `folderPath` and write the uppercase `ConnectionId` the CLI produces. The
    failure this exists to catch — caseplan `bindings[]` dumped verbatim, or
    invented field names — carries neither `key` nor `value`, so the structural
    test is sufficient.
    """
    malformed: dict[tuple, int] = {}
    for entry in resources:
        if not isinstance(entry, dict):
            malformed[("<not an object>",)] = malformed.get(("<not an object>",), 0) + 1
            continue
        value = entry.get("value")
        if not isinstance(entry.get("key"), str) or not entry["key"] \
                or not isinstance(value, dict) or not value:
            sig = tuple(sorted(str(k) for k in entry.keys()))
            malformed[sig] = malformed.get(sig, 0) + 1
    for sig, count in sorted(malformed.items(), key=lambda kv: -kv[1]):
        out.append(
            f"{project}: {count} of {len(resources)} bindings_v2 entries have keys "
            f"{list(sig)} instead of `key` + nested `value.<prop>.defaultValue`. "
            f"The sidecar uses a DIFFERENT format from caseplan `bindings[]` — one "
            f"entry per resource, grouped by resourceKey "
            f"(bindings-v2-sync.md § Regenerate). Dumping `bindings[]` verbatim is "
            f"the usual cause"
        )


def _check_resource_keys(plan, project: str, out: list[str]) -> None:
    """Check 3 (Step 12 Check 11) — resourceKey composed from the pair's own defaults."""
    pairs: dict[str, dict[str, str]] = {}
    for b in _bindings(plan):
        key = b.get("resourceKey")
        attr = _attr(b)
        # PAIR_ATTRS excludes connectionId / folderKey, so connection bindings
        # never enter a pair and need no separate exemption.
        if isinstance(key, str) and attr in PAIR_ATTRS:
            default = b.get("default")
            pairs.setdefault(key, {})[attr] = default if isinstance(default, str) else None
    for key, defaults in sorted(pairs.items()):
        name, folder = defaults.get("name"), defaults.get("folderpath")
        if "name" not in defaults or "folderpath" not in defaults:
            missing = "folderPath" if "folderpath" not in defaults else "name"
            out.append(
                f"{project}: resourceKey {key!r} has no {missing} binding — a pair's two "
                f"bindings must share one identical resourceKey (Check 11); a mismatched "
                f"pair splits into two half-keys like this one"
            )
            continue
        if name is None:
            continue
        if folder == INLINE_SIBLING_SENTINEL:
            out.append(
                f"{project}: binding {key!r} has folderPath default "
                f"{INLINE_SIBLING_SENTINEL!r} — it must be \"\" (the runtime folder); only "
                f"resourceKey carries the {INLINE_SIBLING_SENTINEL} prefix. This passes "
                f"validate and fails at invocation with 'folder not exist'"
            )
            continue
        if folder is None:
            # `default: null` means folder unspecified — a product-authored
            # shape whose resourceKey is the bare name. Nothing to compose.
            continue
        if folder:
            allowed = {f"{folder}.{name}"}
        else:
            # Empty folderPath is legal two ways and the caseplan alone cannot
            # tell them apart: the general formula gives ".<name>", an
            # inline-built agent/api-workflow sibling gives "solution_folder.<name>".
            allowed = {f".{name}", f"{INLINE_SIBLING_SENTINEL}.{name}"}
        if key not in allowed:
            out.append(
                f"{project}: binding resourceKey {key!r} is not self-consistent — "
                f"expected {' or '.join(sorted(repr(a) for a in allowed))} composed from "
                f"its own name/folderPath defaults. Copying a tenant identity (SDD "
                f"Resource Identity, registry entityKey) here validates clean and faults "
                f"at debug"
            )


def check(solution_dir, quiet: bool = False) -> int:
    solution_dir = pathlib.Path(solution_dir)
    caseplans = sorted(solution_dir.glob("*/caseplan.json"))
    if not caseplans:
        print(
            f"AUDIT SKIP: no */caseplan.json under {solution_dir} — wrong directory, or "
            f"not a case solution. Run from the directory CONTAINING <SolutionName>/."
        )
        return 2

    findings: list[str] = []
    for caseplan in caseplans:
        project_dir = caseplan.parent
        project = project_dir.name
        plan = _load(caseplan)

        sidecar_path = project_dir / "bindings_v2.json"
        if not sidecar_path.exists():
            findings.append(f"{project}: bindings_v2.json is absent — run the Step 9.4 sync")
            resources: list = []
        else:
            # NOT `or []` — a falsy non-list ({} / "" / 0) would be coerced to a
            # clean empty list before the type check could see it.
            resources = _load(sidecar_path).get("resources")
            if resources is None:
                resources = []
            elif not isinstance(resources, list):
                findings.append(f"{project}: bindings_v2.json `resources` is not an array")
                resources = []

        caseplan_keys = {
            b["resourceKey"] for b in _bindings(plan)
            if isinstance(b.get("resourceKey"), str) and b["resourceKey"]
        }
        sidecar_keys = {
            r["key"] for r in resources
            if isinstance(r, dict) and isinstance(r.get("key"), str) and r["key"]
        }

        if not quiet:
            print(f"  {project}:")
            print(f"    caseplan resourceKeys  {len(caseplan_keys)}")
            print(f"    bindings_v2 entries    {len(resources)}")

        _check_sidecar_shape(resources, project, findings)

        missing = sorted(caseplan_keys - sidecar_keys)
        if missing:
            findings.append(
                f"{project}: bindings_v2.json is missing resource key(s) {missing} — the "
                f"sidecar was not regenerated after the caseplan was written"
            )
        extra = sorted(sidecar_keys - caseplan_keys)
        if extra:
            findings.append(
                f"{project}: bindings_v2.json declares resource key(s) {extra} absent from "
                f"caseplan bindings[] — stale sidecar entries"
            )

        _check_resource_keys(plan, project, findings)

    if findings:
        print("AUDIT FAIL: caseplan bindings[] and bindings_v2.json disagree.")
        for i, f in enumerate(findings, 1):
            print(f"  {i}. {f}")
        return 1

    print("AUDIT OK: bindings_v2.json matches caseplan bindings[]")
    return 0


def main(argv) -> int:
    args = [a for a in argv[1:] if not a.startswith("-")]
    if len(args) != 1:
        print("usage: audit_bindings.py <solutionDir> [--quiet]", file=sys.stderr)
        return 3
    return check(args[0], quiet="--quiet" in argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
