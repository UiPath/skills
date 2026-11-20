#!/usr/bin/env python3
"""HTTP Request built-in tool on an inline agent — resource check.

The fixture `RatesSol/RatesFlow` is a JSON-authored Flow project that already
holds one inline low-code agent. The agent under test adds the built-in HTTP
Request tool to that inline agent: a GET pinned to one URL, with the query
parameters left to the model.

Validates the tool resource under `RatesSol/RatesFlow/<agent>/resources/`:
  1. Exactly one resource has type == "internal" and
     properties.toolType == "http-request".
  2. Its folder is named after its `id`, and that id is a UUID. Inline agents
     name resource folders by id, not by the resource name.
  3. inputSchema still declares the tool's six arguments.
  4. argumentProperties pins `$['method']` to a static "GET" and `$['url']` to
     the static URL from the prompt, and leaves `$['params']` to the model.
  5. Every `static` / `argument` entry carries a boolean `isSensitive`.
     `uip agent validate` does not check it, and an entry without it stops the
     agent from loading at run time.

The same shape comes out of both authoring routes: the resource written by
hand, and the one `uip maestro flow compile` writes for a builder-SDK
`httpRequest` tool.
"""

import json
import os
import sys
import uuid
from pathlib import Path

FLOW_PROJECT = Path(os.getcwd()) / "RatesSol" / "RatesFlow"
TOOL_TYPE = "http-request"
ARGUMENTS = {"url", "method", "headers", "params", "body", "timeout"}
EXPECTED_URL = "https://api.example.com/v1/rates"
PINNED_VARIANTS = {"static", "argument"}


def key(argument: str) -> str:
    return f"$['{argument}']"


def find_tool() -> tuple:
    if not FLOW_PROJECT.is_dir():
        sys.exit(f"FAIL: {FLOW_PROJECT} does not exist — the fixture Flow project is gone")
    found = []
    for path in sorted(FLOW_PROJECT.glob("*/resources/*/resource.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as e:
            sys.exit(f"FAIL: {path} is not valid JSON: {e}")
        if not isinstance(data, dict):
            continue
        properties = data.get("properties")
        if (
            data.get("type") == "internal"
            and isinstance(properties, dict)
            and properties.get("toolType") == TOOL_TYPE
        ):
            found.append((path, data))
    if not found:
        sys.exit(
            'FAIL: no resource with type "internal" and properties.toolType '
            f'"{TOOL_TYPE}" under {FLOW_PROJECT}/<agent>/resources/'
        )
    if len(found) > 1:
        names = [str(p.relative_to(FLOW_PROJECT)) for p, _ in found]
        sys.exit(f"FAIL: expected one HTTP Request tool resource, found {len(found)}: {names}")
    path, data = found[0]
    print(f"OK: found the HTTP Request tool at {path.relative_to(FLOW_PROJECT.parent)}")
    return path, data


def assert_folder(path: Path, resource: dict) -> None:
    rid = resource.get("id")
    try:
        uuid.UUID(str(rid))
    except ValueError:
        sys.exit(f"FAIL: resource id is not a UUID: {rid!r}")
    if path.parent.name.lower() != str(rid).lower():
        sys.exit(
            f"FAIL: resource folder {path.parent.name!r} must be named after the "
            f"resource id {rid!r} — inline agents name resource folders by id"
        )
    print(f"OK: resource folder is named after its id {rid}")


def assert_input_schema(resource: dict) -> None:
    schema = resource.get("inputSchema")
    properties = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(properties, dict) or not ARGUMENTS <= set(properties):
        got = sorted(properties) if isinstance(properties, dict) else schema
        sys.exit(
            f"FAIL: inputSchema.properties must keep the tool's arguments {sorted(ARGUMENTS)}, "
            f"got {got!r}"
        )
    print(f"OK: inputSchema declares {sorted(ARGUMENTS)}")


def static_value(pins: dict, argument: str):
    entry = pins.get(key(argument))
    if not isinstance(entry, dict) or entry.get("variant") != "static":
        sys.exit(
            f"FAIL: argumentProperties[{key(argument)!r}] must be a `static` entry so the "
            f"model cannot change the {argument}, got {entry!r}"
        )
    return entry.get("value")


def assert_pins(resource: dict) -> None:
    pins = resource.get("argumentProperties")
    if not isinstance(pins, dict):
        sys.exit(f"FAIL: argumentProperties must be an object, got {pins!r}")

    method = static_value(pins, "method")
    if str(method).strip().upper() != "GET":
        sys.exit(f"FAIL: argumentProperties[{key('method')!r}] must pin GET, got {method!r}")

    url = static_value(pins, "url")
    if str(url).strip().rstrip("/") != EXPECTED_URL:
        sys.exit(f"FAIL: argumentProperties[{key('url')!r}] must pin {EXPECTED_URL!r}, got {url!r}")
    print(f"OK: method is pinned to GET and url to {EXPECTED_URL}")

    if key("params") in pins:
        sys.exit(
            f"FAIL: argumentProperties[{key('params')!r}] is set — the query parameters "
            f"are the model's to fill, so `params` must have no entry (got {pins[key('params')]!r})"
        )
    print("OK: params is left to the model")

    for name, entry in pins.items():
        if not isinstance(entry, dict) or entry.get("variant") not in PINNED_VARIANTS:
            continue
        if not isinstance(entry.get("isSensitive"), bool):
            sys.exit(
                f"FAIL: argumentProperties[{name!r}] has no boolean `isSensitive` — "
                "`uip agent validate` accepts that, but the agent then fails to load at run time"
            )
    print("OK: every pinned entry carries isSensitive")


def main() -> None:
    path, resource = find_tool()
    assert_folder(path, resource)
    assert_input_schema(resource)
    assert_pins(resource)


if __name__ == "__main__":
    main()
