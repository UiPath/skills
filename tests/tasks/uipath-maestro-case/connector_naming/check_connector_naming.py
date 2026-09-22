#!/usr/bin/env python3
"""Assert connector field-name fidelity in a built caseplan.json.

The authority is the LIVE connector contract, fetched with `uip maestro case
spec` at grade time: `.Data.Inputs.*[].Name` for request fields,
`.Data.Outputs.ResponseFields[].Name` for response fields, and
`.Data.Filter.Fields[].Name` for filterable fields. Expectations are NOT
hardcoded here — a connector version bump changes the contract, and a frozen
golden would go stale silently (the failure mode the cm_golden fixture header
warns about).

Each authority `Name` is a dotted LEAF PATH. A property map's keys are the
ordered distinct segments under that map's accumulated dotted prefix — top level
being the first segments — reached through `properties` / `items` / `$ref`.
Array markers (`[*]`) are part of the key. Names are compared BYTE-FOR-BYTE at
every depth; `norm()` only pairs a written key with its authority segment so the
mismatch can be reported, and never accepts one as correct.

Checks, in order:
  1. inputs[].body keys           -> Inputs.*[].Name          (written -> authority)
  2. payload output properties    -> ResponseFields[].Name    (set equality, Error excluded)
  3. definitions keys             -> the $ref value targeting each one
  4. trigger filter field names   -> Filter.Fields[].Name     (structured tree and/or
                                                                compiled expression)
  5. connection / folder bindings -> root bindings[]          (resolve, complete, not copied)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

CASEPLAN = "ConnectorNaming/ConnectorNaming/caseplan.json"
ERROR_OUTPUT_NAMES = {"error"}
ENVELOPE_BODY_KEYS = {"parameters", "filters", "queryParams"}
ERROR_ENVELOPE = ["code", "message", "detail", "category", "status", "element"]
# The exact request fields fixtures/sdd.md declares, keyed by connectorKey (NOT by the
# node's free-text displayName, which an agent can rename). A count floor was gameable
# twice over: renaming the node disarmed it, and five unrelated-but-contract-valid
# fields satisfied it while the message itself was never populated.
REQUIRED_INPUT_FIELDS = {
    "uipath-salesforce-slack": ["send_as", "channel", "messageToSend", "link_names", "image"],
}
FAILURES: list[str] = []
INFRA: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def infra(msg: str) -> None:
    """Tenant/auth problem, not a build defect. Still non-zero — a run that could not
    fetch the contract proves nothing — but exit 2 so triage can tell the two apart."""
    INFRA.append(msg)


def ci(obj, *keys):
    """Case-insensitive nested get — the caseplan is camelCase, the spec PascalCase."""
    for key in keys:
        if not isinstance(obj, dict):
            return None
        for actual in obj:
            if actual.lower() == key.lower():
                obj = obj[actual]
                break
        else:
            return None
    return obj


def norm(name: str) -> str:
    """Compare ignoring case and underscores — used only to PAIR a written key
    with its authority segment, never to accept one as correct."""
    return re.sub(r"[_\s]", "", name or "").lower()


def spec(kind: str, type_id: str, connection_id: str) -> dict:
    try:
        return _spec(kind, type_id, connection_id)
    except subprocess.TimeoutExpired:
        infra(f"case spec --type {kind} {type_id} timed out — naming was NOT graded")
        return {}
    except (FileNotFoundError, OSError) as exc:
        infra(f"could not run `uip` ({exc}) — naming was NOT graded")
        return {}


def _spec(kind: str, type_id: str, connection_id: str) -> dict:
    out = subprocess.run(
        ["uip", "maestro", "case", "spec", "--type", kind,
         "--activity-type-id", type_id, "--connection-id", connection_id,
         # NOT --skip-case-shape: check_shape needs the CLI's own caseShape to compare
         # the composed body's structure against. The response schema does not depend
         # on --input-details, so the un-populated shape is the right reference.
         "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        infra(f"case spec --type {kind} {type_id} returned non-JSON — cannot fetch the "
              f"contract, so naming was NOT graded (tenant/auth issue, not a build defect)")
        return {}
    if payload.get("Result") not in (None, "Success"):
        # e.g. `Connection "…" not found or inaccessible` — observed transiently on a
        # connection that resolved fine minutes later. Not a build defect.
        infra(f"case spec --type {kind} {type_id} failed: {payload.get('Message')} — "
              f"naming was NOT graded")
        return {}
    return payload.get("Data") or {}


def authority_names(data: dict, section: str) -> list[str]:
    if section == "outputs":
        entries = ci(data, "Outputs", "ResponseFields") or []
    elif section == "filter":
        entries = ci(data, "Filter", "Fields") or []
    else:
        entries = []
        for sink_value in (ci(data, "Inputs") or {}).values():
            if isinstance(sink_value, list):
                entries.extend(sink_value)
    return [ci(e, "Name") for e in entries if isinstance(e, dict) and ci(e, "Name")]


def top_level(names: list[str]) -> list[str]:
    out: list[str] = []
    for n in names:
        seg = n.split(".")[0]
        if seg not in out:
            out.append(seg)
    return out


def connector_nodes(plan: dict):
    """Yield (displayName, connectorKey, block) for every connector task."""
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") in ("execute-connector-activity", "wait-for-connector"):
                block = node.get("data") or {}
                ck = next((c.get("value") for c in (block.get("context") or [])
                           if c.get("name") == "connectorKey"), None)
                yield node.get("displayName"), ck, block
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
    yield from walk(plan)


def check_inputs(label: str, block: dict, auth: list[str], connector_key: str = "") -> None:
    """Written -> authority only. An authority name with no written key is an
    unused optional parameter, not a mismatch. An input set that is entirely
    empty is a build that never populated the request, not a clean pass."""
    # an [*] marker never appears in an input body — the planner translated the field to a
    # real JSON array under the parent name, so pair with the marker stripped
    def strip(n: str) -> str:
        return n.replace("[*]", "")

    # authority segments keyed by their accumulated dotted prefix, so nested request
    # fields are graded too: Slack declares 37 BodyFields, 18 of them dotted and
    # snake_case at depth (`attachment.image_url`). Top-level-only grading let a build
    # write `attachment: {imageUrl}` and pass.
    by_prefix: dict[str, dict[str, str]] = {}
    for full in auth:
        parts = [strip(x) for x in full.split(".")]
        for depth in range(len(parts)):
            by_prefix.setdefault(".".join(parts[:depth]), {})[norm(parts[depth])] = parts[depth]

    written_count = 0
    seen_fields: set[str] = set()
    seen_fields_raw: set[str] = set()

    def walk(body: dict, prefix: str) -> None:
        nonlocal written_count
        known = by_prefix.get(prefix)
        if known is None:
            return
        for written, value in body.items():
            # structural envelope keys a trigger input body carries, not contract fields:
            # `parameters` holds eventParameters, `filters` holds the filter tree
            if not prefix and written in ENVELOPE_BODY_KEYS:
                # recurse into the envelope: eventParameters ARE contract fields
                if isinstance(value, dict):
                    walk(value, prefix)
                continue
            written_count += 1
            if not prefix:
                seen_fields.add(norm(written))
                seen_fields_raw.add(written)
            want = known.get(norm(written))
            if want is None:
                fail(f"{label}: input key {written!r}"
                     f"{' under ' + prefix if prefix else ''} matches no field in the "
                     f"connector contract")
                continue
            if written != want:
                fail(f"{label}: input key {written!r}"
                     f"{' under ' + prefix if prefix else ''} should be {want!r} "
                     f"(byte-exact contract name)")
            child = prefix + ("." if prefix else "") + want
            if isinstance(value, dict):
                walk(value, child)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        walk(item, child)

    for entry in block.get("inputs") or []:
        body = entry.get("body")
        if isinstance(body, dict):
            walk(body, "")

    required = REQUIRED_INPUT_FIELDS.get(connector_key or "", [])
    if required:
        missing = [f for f in required if norm(f) not in seen_fields]
        if missing:
            fail(f"{label}: request fields declared by the SDD are absent from the built "
                 f"body: {missing} (written: {sorted(seen_fields_raw)[:10]})")
    elif auth and written_count == 0:
        fail(f"{label}: no request field was written at all — the connector declares "
             f"{len(top_level(auth))} input field(s); an empty request cannot be graded")


def check_outputs(label: str, block: dict, auth: list[str]) -> None:
    expected = top_level(auth)
    graded_any = False
    for entry in block.get("outputs") or []:
        name = str(entry.get("name") or "")
        props = ci(entry.get("body") or {}, "properties")
        if not isinstance(props, dict) or not props:
            continue
        # dedup suffixes the id (`error2`), not the name — but match tolerantly so a
        # future plugin that dedups the name cannot smuggle the envelope into the
        # payload-schema path, where it would fail the whole set on a false premise.
        if name.lower().rstrip("0123456789") in ERROR_OUTPUT_NAMES:
            # fixed platform envelope: ResponseFields never describes it, and the disk
            # form is lower-cased. Grade it rather than skipping — leaving it PascalCase
            # is the regression a positional "never re-case inside properties" rule invites.
            if sorted(k.lower() for k in props) == sorted(ERROR_ENVELOPE) and \
               any(k[:1].isupper() for k in props):
                fail(f"{label}: Error output keys are the platform envelope and must be "
                     f"lower-cased; got {sorted(props)}")
            continue
        graded_any = True
        written = list(props.keys())
        if set(written) != set(expected):
            missing = [e for e in expected if e not in written]
            extra = [w for w in written if w not in expected]
            fail(f"{label}: output {name!r} property names do not match the contract; "
                 f"missing={missing[:8]} unexpected={extra[:8]}")
        for k, v in props.items():
            if not isinstance(v, dict) or not (ci(v, "type") or ci(v, "$ref") or ci(v, "items")):
                fail(f"{label}: property {k!r} carries no type/$ref/items — a bare key is a husk, "
                     f"not a spliced schema")
                break
        for full in [a for a in auth if "." in a]:
            segs = full.split(".")
            cur, ok, miscased = props, True, None
            for seg in segs:
                if not isinstance(cur, dict):
                    ok = False; break
                hit = [kk for kk in cur if norm(kk) == norm(seg)]
                if not hit:
                    ok = False; break
                # norm() PAIRS the written key with its authority segment; it must never
                # ACCEPT one. Nested names are contract too — `Attachments[*].MIMEType`
                # lowered to `mimeType` resolves structurally and is still wrong.
                if hit[0] != seg and miscased is None:
                    miscased = (hit[0], seg)
                nxt = cur[hit[0]]
                for _ in range(3):
                    if not isinstance(nxt, dict): break
                    if ci(nxt, "properties"): nxt = ci(nxt, "properties"); break
                    if ci(nxt, "items"): nxt = ci(nxt, "items"); continue
                    r = ci(nxt, "$ref")
                    if isinstance(r, str):
                        tgt = r.split("/")[-1]
                        alld = {}
                        def collect(o):
                            if isinstance(o, dict):
                                for kk, vv in o.items():
                                    if kk.lower() == "definitions" and isinstance(vv, dict): alld.update(vv)
                                    collect(vv)
                            elif isinstance(o, list):
                                for x in o: collect(x)
                        collect(entry)
                        cand = [vv for kk, vv in alld.items() if norm(kk) == norm(tgt)]
                        if cand: nxt = ci(cand[0], "properties") or cand[0]; break
                    break
                cur = nxt
            if not ok:
                fail(f"{label}: nested contract path {full!r} does not resolve through "
                     f"properties/items/$ref — the nested names were not spliced")
                break
            if miscased:
                got, want = miscased
                fail(f"{label}: nested contract path {full!r} resolves, but the written key "
                     f"is {got!r} where the contract says {want!r} — nested field names are "
                     f"contract, not casing")
                break
    if expected and not graded_any:
        fail(f"{label}: no response schema was written at all — the connector declares "
             f"{len(expected)} response propert(ies); an absent schema cannot be graded")


def schema_shape(node) -> tuple[int, int, int, int, int]:
    """(property maps, property keys, definitions entries, $refs, total keys) under node.

    `total keys` is what catches annotation stripping: dropping every nested `type` /
    `title` / `format` leaves the map and definition counts identical, so without it a
    schema whose nested properties carry no type at all passes."""
    maps = keys = defs = refs = total = 0
    def walk(o):
        nonlocal maps, keys, defs, refs, total
        if isinstance(o, dict):
            total += len(o)
            for k, v in o.items():
                lk = k.lower()
                if lk == "properties" and isinstance(v, dict):
                    maps += 1
                    keys += len(v)
                elif lk == "definitions" and isinstance(v, dict):
                    defs += len(v)
                elif lk == "$ref":
                    refs += 1
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(node)
    return maps, keys, defs, refs, total


def check_shape(label: str, block: dict, cli_outputs: list) -> None:
    """A payload body is COMPOSED, not copied (the split write). Name checks alone
    cannot see a dropped subtree or a stripped annotation: delete a whole definition
    and the top-level count, the definitions count and the $ref set can all still
    line up. Compare the written body's structure against the CLI's own."""
    want_by_name = {}
    for o in cli_outputs or []:
        nm = str(ci(o, "Name") or "")
        body = ci(o, "Body")
        if isinstance(body, dict) and nm.lower().rstrip("0123456789") not in ERROR_OUTPUT_NAMES:
            want_by_name[norm(nm)] = schema_shape(body)
    for entry in block.get("outputs") or []:
        nm = str(entry.get("name") or "")
        if nm.lower().rstrip("0123456789") in ERROR_OUTPUT_NAMES:
            continue
        body = entry.get("body")
        want = want_by_name.get(norm(nm))
        if not isinstance(body, dict) or want is None:
            continue
        got = schema_shape(body)
        if got != want:
            names = ("property maps", "property keys", "definitions entries", "$refs",
                     "total keys")
            diff = ", ".join(f"{n}: wrote {g}, spec has {w}"
                             for n, g, w in zip(names, got, want) if g != w)
            fail(f"{label}: output {nm!r} schema does not match the CLI's structure "
                 f"({diff}) — the composed body lost or invented content")


def check_definitions(label: str, block: dict, auth: list[str]) -> None:
    raw = json.dumps(block)
    refs = set(re.findall(r'"\$ref"\s*:\s*"#/definitions/([^"]+)"', raw))
    defs: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.lower() == "definitions" and isinstance(v, dict):
                    defs.update(v.keys())
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(block)
    dangling = sorted(r for r in refs if r not in defs)
    if dangling:
        fail(f"{label}: {len(dangling)} $ref target(s) resolve to no definitions key "
             f"(the definitions keys were renamed): {dangling[:6]}")

    # Internal consistency is not enough: renaming a key AND the $ref that targets it
    # keeps refs == defs while inventing names the connector never declared (and
    # rewriting a $ref VALUE breaks the skill's own keys-only rule). Anchor the names
    # against the contract — every definitions key must be a real dotted path prefix.
    prefixes = set()
    for full in auth:
        parts = full.split(".")
        for depth in range(1, len(parts)):
            prefixes.add(norm("".join(parts[:depth])))
            prefixes.add(norm(parts[depth - 1]))
    if prefixes:
        invented = sorted(d for d in defs if norm(d) not in prefixes)
        if invented:
            fail(f"{label}: {len(invented)} definitions key(s) correspond to no path in the "
                 f"connector contract — the names were invented, not derived: {invented[:6]}")


def check_filter(label: str, block: dict, auth: list[str]) -> None:
    """Filter field names are a third sink where a rename silently matches nothing.

    They live in TWO places and neither is guaranteed present: a compiled
    JMESPath `expression`, and — the form these triggers actually emit — the
    `fieldName` entries of the structured filter tree, which reaches disk inside
    an escaped `=jsonString:` blob. Grade whichever exists; grade nothing only
    when the node genuinely carries no filter."""
    if not auth:
        return
    raw = json.dumps(block)

    # Structured tree, including the escaped copy inside `=jsonString:`.
    by_norm = {norm(a): a for a in auth}
    field_names = re.findall(r'\\?"fieldName\\?"\s*:\s*\\?"([^"\\]+)', raw)
    for got in set(field_names):
        want = by_norm.get(norm(got))
        if want and got != want:
            fail(f"{label}: filter references field {got!r}; the contract field is {want!r}")

    exprs = re.findall(r'"(?:expression|filterExpression)"\s*:\s*"([^"]+)"', raw)
    if not exprs:
        return
    blob = " ".join(exprs)
    blob = re.sub(r"'[^']*'|`[^`]*`", " ", blob)  # values are not field references
    for token in set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*(?:\[\*\])?(?:\.[A-Za-z0-9_]+)*", blob)):
        want = by_norm.get(norm(token))
        if want and token != want:
            fail(f"{label}: compiled filter references {token!r}; the contract field is {want!r}")


BINDING_FIELDS = {"id", "name", "type", "resource", "resourceKey", "default", "propertyAttribute"}


def check_bindings(label: str, block: dict, root_bindings: list) -> None:
    """A connector node points at two root bindings — the connection and the
    folder — and copies neither onto itself. A dangling or malformed binding
    renders as a broken node in Studio Web while `validate` stays green."""
    by_id = {b.get("id"): b for b in root_bindings if isinstance(b, dict)}
    ctx = {c.get("name"): c.get("value") for c in (block.get("context") or [])}

    if block.get("bindings") != []:
        fail(f"{label}: data.bindings must be [] — root bindings are never copied onto the task "
             f"(got {block.get('bindings')!r})")

    conn_id = ctx.get("resourceKey")
    for ctx_name, attr in (("connection", "ConnectionId"), ("folderKey", "folderKey")):
        ref = ctx.get(ctx_name)
        if ref is None:
            if ctx_name == "folderKey":
                continue  # omitted when the connection has no folder
            fail(f"{label}: context[{ctx_name}] is missing")
            continue
        m = re.fullmatch(r"=bindings\.(\w+)", str(ref))
        if not m:
            fail(f"{label}: context[{ctx_name}] should be '=bindings.<id>', got {ref!r}")
            continue
        binding = by_id.get(m.group(1))
        if binding is None:
            fail(f"{label}: context[{ctx_name}] points at binding {m.group(1)!r}, "
                 f"which is not in the root bindings[]")
            continue
        missing = BINDING_FIELDS - set(binding)
        if missing:
            fail(f"{label}: binding {m.group(1)!r} is missing required field(s) {sorted(missing)} "
                 f"— Studio Web fails to render the node")
        if binding.get("propertyAttribute") != attr:
            fail(f"{label}: binding for context[{ctx_name}] has propertyAttribute "
                 f"{binding.get('propertyAttribute')!r}, expected {attr!r}")
        if conn_id and binding.get("resourceKey") != conn_id:
            fail(f"{label}: binding {m.group(1)!r} resourceKey is {binding.get('resourceKey')!r}, "
                 f"expected the node's connection id {conn_id!r}")
        if not binding.get("default"):
            fail(f"{label}: binding {m.group(1)!r} has an empty default")


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else CASEPLAN
    if not os.path.exists(path):
        print(f"FAIL: {path} not found")
        return 1
    plan = json.load(open(path))
    root_bindings = plan.get("bindings") or []

    seen = 0
    for label, connector_key, block in connector_nodes(plan):
        # connection id is context[name="resourceKey"]; the activity type id is
        # buried in the metadata config blob as uiPathActivityTypeId
        ctx = {c.get("name"): c.get("value") for c in (block.get("context") or [])}
        conn = ctx.get("resourceKey") or block.get("connectionId")
        found = re.findall(r'"uiPathActivityTypeId"\s*:\s*\\?"?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
                           json.dumps(block))
        type_id = block.get("typeId") or (found[0] if found else None)
        if not type_id or not conn:
            fail(f"{label}: cannot locate typeId/connectionId on the node to fetch its contract")
            continue
        kind = "trigger" if block.get("serviceType") == "Intsvc.WaitForEvent" else "activity"
        data = spec(kind, str(type_id), str(conn))
        if not data:
            continue
        seen += 1
        check_inputs(label, block, authority_names(data, "inputs"), connector_key or "")
        check_outputs(label, block, authority_names(data, "outputs"))
        check_definitions(label, block, authority_names(data, "outputs"))
        check_shape(label, block, ci(data, "CaseShape", "Outputs") or [])
        check_filter(label, block, authority_names(data, "filter"))
        check_bindings(label, block, root_bindings)

    if seen < 2:
        fail(f"expected 2 connector tasks with resolvable contracts, graded {seen}")

    for f in INFRA:
        print("INFRA:", f)
    for f in FAILURES:
        print("FAIL:", f)
    if INFRA and not FAILURES:
        print("INFRA: the live contract could not be fetched; naming was NOT graded.")
        return 2
    if FAILURES:
        return 1
    print(f"PASS: connector field names match the live contract on {seen} connector task(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
