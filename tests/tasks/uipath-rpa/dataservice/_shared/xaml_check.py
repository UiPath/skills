"""XAML assertions for DataService coder_eval tests.

Two assertion tiers:
- **Smoke** (existing): activity presence + x:TypeArguments + no-stray guard.
- **Integration**: per-activity property walks — RecordState fields, SimpleFilter
  entries, attribute matching, anti-pattern guards.

Helpers are namespace-tolerant: they match elements by local name and look up
attributes through a known namespace map (uda:, udd:, x:). Deep textual checks
(e.g. `x:Int32` type literals, FailedRecords typing, VB expressions) belong in
YAML `file_contains` criteria, not here — those are too brittle to walk.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from typing import Iterable

UDA_NS = "clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
UDD_NS = "clr-namespace:UiPath.DataService.Activities.Design;assembly=UiPath.DataService.Activities.Core"
X_NS = "http://schemas.microsoft.com/winfx/2006/xaml"

# Attribute lookup uses a flat map of "prefix:name" -> ClarkName for x: only;
# everything else we match by local name to stay namespace-tolerant.
_X_ATTRS = {
    "x:TypeArguments": f"{{{X_NS}}}TypeArguments",
    "x:Key": f"{{{X_NS}}}Key",
    "x:Name": f"{{{X_NS}}}Name",
}


def _load(xaml_path: str) -> ET.Element:
    try:
        return ET.parse(xaml_path).getroot()
    except FileNotFoundError:
        print(f"FAIL: {xaml_path} does not exist", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as exc:
        print(f"FAIL: {xaml_path} is not well-formed XML: {exc}", file=sys.stderr)
        sys.exit(1)


def _local(el: ET.Element) -> str:
    return el.tag.split("}", 1)[1] if "}" in el.tag else el.tag


def _local_attr(el: ET.Element, name: str) -> str | None:
    """Return attribute value by local name, regardless of namespace prefix."""
    if name in _X_ATTRS:
        v = el.get(_X_ATTRS[name])
        if v is not None:
            return v
    # Try raw (no namespace) first
    if el.get(name) is not None:
        return el.get(name)
    # Fall back to scanning Clark-name attrs for matching local part
    for k, v in el.attrib.items():
        local = k.split("}", 1)[1] if "}" in k else k
        if local == name:
            return v
    return None


def _uda_activities(root: ET.Element) -> list[ET.Element]:
    return [el for el in root.iter() if el.tag.startswith(f"{{{UDA_NS}}}")]


def _find_local(scope: ET.Element, local_name: str) -> list[ET.Element]:
    """All descendants whose local-name matches."""
    return [el for el in scope.iter() if _local(el) == local_name]


def _type_arg_local_name(type_arg_value: str | None) -> str | None:
    """Return the local type name from an x:TypeArguments value (`alias:Type` → `Type`).

    XAML lets authors pick any xmlns alias for the project's entity namespace
    (`local:`, `e:`, `a:`, etc.). The local type name is what carries semantic
    meaning; matching on the alias prefix is brittle and rejects valid XAML.
    """
    if type_arg_value is None:
        return None
    return type_arg_value.split(":", 1)[1] if ":" in type_arg_value else type_arg_value


def _type_args_match(actual: str | None, expected: str) -> bool:
    """Compare x:TypeArguments values by local name only.

    `expected` may be passed as a bare type name (`CodingAgentsEvalEntity`) or
    with an arbitrary prefix (`local:CodingAgentsEvalEntity`). Either way only
    the local part after the last `:` is compared against `actual`.
    """
    return _type_arg_local_name(actual) == _type_arg_local_name(expected)


# ---------------------------------------------------------------------------
# Smoke-tier helpers (kept for S1/S2/S3)
# ---------------------------------------------------------------------------


def assert_activities_present(
    xaml_path: str, expected: list[str], entity_type: str
) -> None:
    """Each `expected` activity must appear at least once with TypeArguments matching `entity_type` by local name.

    The xmlns alias the agent picks for the entity namespace (`local:`, `e:`,
    `a:`, etc.) is irrelevant — only the local type name is compared.
    """
    root = _load(xaml_path)
    found = _uda_activities(root)

    missing: list[str] = []
    wrong_type: list[tuple[str, str]] = []

    for name in expected:
        matches = [el for el in found if _local(el) == name]
        if not matches:
            missing.append(name)
            continue
        type_args = [_local_attr(el, "x:TypeArguments") for el in matches]
        if not any(_type_args_match(t, entity_type) for t in type_args):
            wrong_type.append((name, ", ".join(filter(None, type_args)) or "<none>"))

    if missing:
        print(f"FAIL: missing uda activities: {', '.join(missing)}", file=sys.stderr)
    if wrong_type:
        for name, observed in wrong_type:
            print(
                f"FAIL: {name} expected TypeArguments local-name {entity_type!r}, got {observed!r}",
                file=sys.stderr,
            )
    if missing or wrong_type:
        sys.exit(1)


def assert_no_unexpected_uda(xaml_path: str, allowed: list[str]) -> None:
    """No uda:* activity outside the `allowed` set is present."""
    root = _load(xaml_path)
    allowed_set = set(allowed)
    stray = sorted({_local(el) for el in _uda_activities(root)} - allowed_set)
    if stray:
        print(
            f"FAIL: unexpected uda activities in XAML: {', '.join(stray)}",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Integration-tier helpers
# ---------------------------------------------------------------------------


def load(xaml_path: str) -> ET.Element:
    """Public loader for per-scenario scripts that want the parsed tree."""
    return _load(xaml_path)


def get_activity(root: ET.Element, name: str, type_arg: str | None = None) -> ET.Element:
    """Return the unique uda:<name> activity. Exits if 0 or >1 match.

    `type_arg` may be passed bare (`CodingAgentsEvalEntity`) or with any prefix
    (`local:CodingAgentsEvalEntity`, `e:CodingAgentsEvalEntity`, ...). Matching
    is by local type name so callers don't depend on the xmlns alias the agent
    picked.
    """
    matches = [el for el in _uda_activities(root) if _local(el) == name]
    if type_arg is not None:
        matches = [
            el for el in matches
            if _type_args_match(_local_attr(el, "x:TypeArguments"), type_arg)
        ]
    if not matches:
        print(
            f"FAIL: no uda:{name} activity"
            + (
                f" with x:TypeArguments local-name "
                f"{_type_arg_local_name(type_arg)!r}"
                if type_arg
                else ""
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    if len(matches) > 1:
        print(
            f"FAIL: expected exactly one uda:{name}, found {len(matches)}",
            file=sys.stderr,
        )
        sys.exit(1)
    return matches[0]


def get_activities(
    root: ET.Element, name: str, type_arg: str | None = None
) -> list[ET.Element]:
    matches = [el for el in _uda_activities(root) if _local(el) == name]
    if type_arg is not None:
        matches = [
            el for el in matches
            if _type_args_match(_local_attr(el, "x:TypeArguments"), type_arg)
        ]
    return matches


def assert_attr(el: ET.Element, name: str, expected: str) -> None:
    """Attribute (by local name) must equal `expected`."""
    actual = _local_attr(el, name)
    if actual != expected:
        print(
            f"FAIL: {_local(el)}.{name} expected {expected!r}, got {actual!r}",
            file=sys.stderr,
        )
        sys.exit(1)


def assert_attr_or_default(el: ET.Element, name: str, default: str) -> None:
    """Attribute must be absent (implicit default) or equal `default` (explicit default).

    Use for baseline properties whose default value matches the expected
    config — e.g. `ScopeValue="Tenant"` on activities where Tenant is the
    XAML default. The agent legitimately omits the attribute and the runtime
    still gets the desired value.
    """
    actual = _local_attr(el, name)
    if actual is None:
        return
    if actual != default:
        print(
            f"FAIL: {_local(el)}.{name} expected absent or {default!r}, got {actual!r}",
            file=sys.stderr,
        )
        sys.exit(1)


def assert_attr_absent(el: ET.Element, name: str) -> None:
    """Attribute (by local name) must not be present on the element."""
    actual = _local_attr(el, name)
    if actual is not None:
        print(
            f"FAIL: {_local(el)}.{name} must be absent (anti-pattern); got {actual!r}",
            file=sys.stderr,
        )
        sys.exit(1)


def assert_child_absent(activity: ET.Element, local_name: str) -> None:
    """No descendant of `activity` may have the given local name."""
    hits = _find_local(activity, local_name)
    if hits:
        print(
            f"FAIL: {_local(activity)} must not contain <{local_name}>; found {len(hits)}",
            file=sys.stderr,
        )
        sys.exit(1)


# RecordState helpers --------------------------------------------------------


def collect_dynamic_entity_fields(activity: ET.Element) -> list[ET.Element]:
    return _find_local(activity, "DynamicEntityField")


def assert_record_state_fields(
    activity: ET.Element,
    required: Iterable[str],
    optional: Iterable[str] = (),
    forbidden: Iterable[str] = (),
) -> None:
    """RecordState must contain exactly the named fields with correct IsRequired flags.

    `forbidden` fields must NOT appear in RecordState (anti-pattern guard for
    file fields, untouched fields, etc.).
    """
    fields = collect_dynamic_entity_fields(activity)
    by_name = {}
    for f in fields:
        n = _local_attr(f, "FieldName")
        if n:
            by_name[n] = f

    errors: list[str] = []
    expected_present = set(required) | set(optional)
    missing = expected_present - by_name.keys()
    if missing:
        errors.append(f"missing DynamicEntityField entries: {sorted(missing)}")

    for name in required:
        f = by_name.get(name)
        if f is not None and _local_attr(f, "IsRequired") != "True":
            errors.append(
                f"{name}: IsRequired expected 'True', got {_local_attr(f, 'IsRequired')!r}"
            )
    for name in optional:
        f = by_name.get(name)
        if f is not None and _local_attr(f, "IsRequired") not in ("False", None):
            errors.append(
                f"{name}: IsRequired expected 'False'/absent, got {_local_attr(f, 'IsRequired')!r}"
            )

    forbidden_present = set(forbidden) & by_name.keys()
    if forbidden_present:
        errors.append(
            f"forbidden fields present in RecordState: {sorted(forbidden_present)}"
        )

    if errors:
        for e in errors:
            print(f"FAIL: {_local(activity)} RecordState — {e}", file=sys.stderr)
        sys.exit(1)


def assert_input_entity_anti_pattern(activity: ET.Element) -> None:
    """`InputEntity` (the bad property) must be absent; `InputEntityInFieldView` must be present.

    We distinguish the two by checking the attribute on the activity itself.
    The good property is `InputEntityInFieldView`; the anti-pattern is the bare
    `InputEntity` attribute.
    """
    # Check direct attributes first
    has_in_field_view = (
        _local_attr(activity, "InputEntityInFieldView") is not None
        or any(_local(c) == f"{_local(activity)}.InputEntityInFieldView" for c in activity)
    )
    has_bad_input_entity = (
        _local_attr(activity, "InputEntity") is not None
        or any(_local(c) == f"{_local(activity)}.InputEntity" for c in activity)
    )

    if has_bad_input_entity:
        print(
            f"FAIL: {_local(activity)} uses anti-pattern InputEntity property (Studio desync risk)",
            file=sys.stderr,
        )
        sys.exit(1)
    if not has_in_field_view:
        print(
            f"FAIL: {_local(activity)} missing InputEntityInFieldView property",
            file=sys.stderr,
        )
        sys.exit(1)


# Filter helpers (QueryEntityRecords) ---------------------------------------


def collect_simple_filters(activity: ET.Element) -> list[dict]:
    """Return list of {field, operator, value_index} for every SimpleFilter descendant."""
    out = []
    for f in _find_local(activity, "SimpleFilter"):
        out.append(
            {
                "field": _local_attr(f, "FieldName"),
                "operator": _local_attr(f, "Operator"),
                "value_index": _local_attr(f, "ValueIndex"),
            }
        )
    return out


def assert_simple_filters_contain(
    activity: ET.Element, expected: list[tuple[str, str]]
) -> None:
    """Each (field, operator) pair must appear at least once in the activity's SimpleFilters.

    Operators are matched as XAML-escaped strings — pass `&gt;` not `>`.
    """
    observed = collect_simple_filters(activity)
    obs_pairs = {(f["field"], f["operator"]) for f in observed}
    missing = [pair for pair in expected if pair not in obs_pairs]
    if missing:
        print(
            f"FAIL: {_local(activity)} missing SimpleFilter pairs: {missing}; "
            f"observed: {sorted(obs_pairs)}",
            file=sys.stderr,
        )
        sys.exit(1)


def assert_group_filter_operator(activity: ET.Element, expected: str) -> None:
    """At least one GroupFilter under `activity` has Operator=`expected` (AND/OR)."""
    groups = _find_local(activity, "GroupFilter")
    ops = [_local_attr(g, "Operator") for g in groups]
    if expected not in ops:
        print(
            f"FAIL: {_local(activity)} missing GroupFilter Operator={expected!r}; "
            f"observed: {ops}",
            file=sys.stderr,
        )
        sys.exit(1)
