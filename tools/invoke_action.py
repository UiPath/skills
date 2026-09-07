#!/usr/bin/env python3
"""Invoke an ontology action and print its step trace. Dependency-free, standard library only.

`uip ont` has no invoke verb, so this is the supported way to run an action from the CLI side. It
exists because the invoke is the only step that proves a deployed action actually works, and a
hand-rolled curl cannot source its own bearer: `uip login status` reports identity but not a token.
`uip login refresh` does -- it "emit[s] a machine-readable session payload (access token, org/tenant
identity, expiration)" for exactly this kind of consumer -- so that is where the token comes from,
and it is never printed or written anywhere.

Nothing about the target is baked in: base URL, organisation and tenant all come from the logged-in
session, the same rule the skills apply everywhere else.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


UIP = os.environ.get("UIP_CLI", "uip")

# The ontology service's own gateway segment. `datafabric_` answers 404 for these routes.
SERVICE_SEGMENT = "ontology_"


def die(message: str) -> None:
    print(json.dumps({"ok": False, "error": message}, indent=2))
    raise SystemExit(1)


def uip_json(args: list[str]) -> dict:
    """Run a uip subcommand and return its parsed envelope, or die naming what failed."""
    try:
        proc = subprocess.run(
            [UIP, *args, "--output", "json"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        die("cannot run %r; set UIP_CLI to the CLI entry point" % UIP)
    if proc.returncode != 0 and not proc.stdout.strip():
        die("uip %s failed: %s" % (" ".join(args), (proc.stderr or "").strip()[:400]))
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        die("uip %s did not return JSON: %s" % (" ".join(args), proc.stdout.strip()[:400]))
    return {}


def session() -> tuple[str, str, str, str]:
    """(baseUrl, org, tenant, token) from the logged-in session and nowhere else."""
    status = uip_json(["login", "status"]).get("Data") or {}
    for field in ("BaseUrl", "Organization", "Tenant"):
        if not status.get(field):
            die("not logged in: uip login status reports no %s" % field)
    # refresh rather than status: status reports identity, refresh also returns a token and
    # guarantees it is still valid for the next few minutes.
    refreshed = uip_json(["login", "refresh"]).get("Data") or {}
    token = refreshed.get("AccessToken")
    if not token:
        die("uip login refresh returned no AccessToken; run `uip login` and retry")
    return status["BaseUrl"].rstrip("/"), status["Organization"], status["Tenant"], token


def parse_params(pairs: list[str], params_json: str | None) -> dict:
    if params_json:
        try:
            parsed = json.loads(params_json)
        except json.JSONDecodeError as exc:
            die("--params-json is not valid JSON: %s" % exc)
        if not isinstance(parsed, dict):
            die("--params-json must be a JSON object of parameter names to values")
        return parsed
    params: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            die("--param expects name=value, got %r" % pair)
        name, value = pair.split("=", 1)
        params[name] = value
    return params


def invoke(ontology: str, action: str, params: dict, folder_key: str | None) -> tuple[int, dict]:
    base, org, tenant, token = session()
    url = "%s/%s/%s/%s/api/ontology/%s/actions/%s/invoke" % (
        base, org, tenant, SERVICE_SEGMENT, ontology, action
    )
    body = json.dumps({"params": params}).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Authorization", "Bearer " + token)
    request.add_header("Content-Type", "application/json")
    # urllib's default User-Agent is rejected by the edge WAF with 403 "error code: 1010" before
    # the request ever reaches the service. Any ordinary agent string gets through.
    request.add_header("User-Agent", "uipath-ontology-skill/1.0")
    if folder_key:
        request.add_header("X-Uipath-Folderkey", folder_key)
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"detail": raw[:600]}
    except urllib.error.URLError as exc:
        die("could not reach %s: %s" % (url, exc.reason))
    return 0, {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ontology", help="ontology name (slug)")
    parser.add_argument("action", help="action name, as in the TTL and the func: marker")
    parser.add_argument("--param", action="append", default=[], metavar="NAME=VALUE",
                        help="one action parameter; repeat for several")
    parser.add_argument("--params-json", help="all parameters as one JSON object, instead of --param")
    parser.add_argument("--folder-key", help="only when the action needs a folder other than the "
                                             "ontology's own; normally omit it")
    args = parser.parse_args(argv)

    status, payload = invoke(
        args.ontology, args.action, parse_params(args.param, args.params_json), args.folder_key
    )
    steps = payload.get("steps") or []
    result = {
        "ok": status == 200 and not any(s.get("status") == "failed" for s in steps),
        "httpStatus": status,
        "action": payload.get("action", args.action),
        "outcome": payload.get("outcome"),
        "rowsAffected": payload.get("rowsAffected"),
        # `error` is the only diagnostic a failed invoke carries -- the step that failed says why,
        # e.g. "Data Fabric rejected the query: HTTP 400 ... recordId was not found". Dropping it
        # left a caller with "Executing write / failed" and nothing to act on.
        "steps": [
            {
                key: value
                for key, value in (
                    ("label", s.get("label")),
                    ("status", s.get("status")),
                    ("durationMs", s.get("durationMs")),
                    ("error", s.get("error")),
                )
                if value is not None
            }
            for s in steps
        ],
    }
    for extra in ("detail", "code", "module", "traceId"):
        if payload.get(extra) is not None:
            result[extra] = payload[extra]
    # rowsAffected 0 with no failed step is a converged no-op, and a success.
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
