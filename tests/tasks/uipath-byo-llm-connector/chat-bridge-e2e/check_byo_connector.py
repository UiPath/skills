#!/usr/bin/env python3
"""Grade a BYO LLM custom connector built for the OpenAiChatCompletions flavor.

Static checks (both modes): the flavor's resource path, the template tag, the
x-api-key header, no secret defaults, no credentials in query/path parameters.

Hook checks (--hooks): run the connector's own preRequest/postRequest hooks for
POST /v1/chat/completions in a Node vm against an OpenAI chat body and Acme
Inference API answers (see fixtures/acme-inference-api.md), and assert the
translation both ways. Exit 0 only when every check passes.

Usage: check_byo_connector.py <connector_root> [--hooks]
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

FLAVOR_PATH = "/v1/chat/completions"
FLAVOR_TAG = "aigateway-openai-chat-completions"
VENDOR_PATH = "/v2/generate"
CREDENTIAL_HINTS = ("key", "token", "secret", "password", "authorization", "credential")

NODE_RUNNER = r"""
const fs = require('fs');
const vm = require('vm');
const [hookFile, varsFile] = process.argv.slice(2);
const vars = JSON.parse(fs.readFileSync(varsFile, 'utf8'));
let result;
const allowed = new Set(['crypto', 'url', 'querystring', 'buffer', 'util', 'zlib']);
const context = vm.createContext({
  ...vars, btoa, atob, JSON, Math, Date,
  require: (m) => { if (!allowed.has(m)) throw new Error('module not available: ' + m); return require(m); },
  done: (out = {}) => { if (result === undefined) result = out; },
});
vm.runInContext('(function () {\n' + fs.readFileSync(hookFile, 'utf8') + '\n})();', context, { timeout: 5000 });
if (result === undefined) { console.error('done() was not called'); process.exit(3); }
process.stdout.write(JSON.stringify(result));
"""

OPENAI_REQUEST = {
    "model": "acme-large",
    "messages": [
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": [{"type": "text", "text": "Hi"}]},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "How are you?"},
    ],
    "max_tokens": 64,
    "temperature": 0.3,
}
EXPECTED_TURNS = [
    {"speaker": "human", "text": "Hi"},
    {"speaker": "model", "text": "Hello"},
    {"speaker": "human", "text": "How are you?"},
]


def vendor_answer(stop: str) -> dict:
    return {
        "request_id": "req-0001",
        "model": "acme-large",
        "result": {"text": "Fine, thanks.", "stop": stop},
        "metering": {"input_tokens": 12, "output_tokens": 4},
    }


class Report:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        self.results.append((name, bool(ok), detail))
        return bool(ok)

    def finish(self) -> int:
        failed = [r for r in self.results if not r[1]]
        for name, ok, detail in self.results:
            print(f"{'PASS' if ok else 'FAIL'}  {name}{'  -- ' + detail if detail and not ok else ''}")
        print(f"{len(self.results) - len(failed)}/{len(self.results)} checks passed")
        return 0 if not failed else 1


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def as_obj(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def flavor_resource(element: dict):
    for res in element.get("resources") or []:
        if res.get("path") == FLAVOR_PATH and str(res.get("method", "")).upper() == "POST":
            return res
    return None


def hook_source(root: Path, resource: dict, element: dict, phase: str):
    hooks = [h for h in (resource.get("hooks") or []) if h.get("type") == phase]
    for h in hooks:
        if h.get("ref"):
            f = root / "app" / "element" / "hooks" / h["ref"]
            if f.exists():
                return f.read_text(encoding="utf-8")
        if isinstance(h.get("body"), str) and h["body"].strip():
            return h["body"]
    for h in element.get("hooks") or []:
        if h.get("type") == phase:
            if h.get("ref"):
                f = root / "app" / "element" / "hooks" / h["ref"]
                if f.exists():
                    return f.read_text(encoding="utf-8")
            if isinstance(h.get("body"), str) and h["body"].strip():
                return h["body"]
    return None


def run_hook(source: str, variables: dict, workdir: Path):
    hook = workdir / "hook.js"
    hook.write_text(source, encoding="utf-8")
    vars_file = workdir / "vars.json"
    vars_file.write_text(json.dumps(variables), encoding="utf-8")
    runner = workdir / "runner.js"
    runner.write_text(NODE_RUNNER, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(runner), str(hook), str(vars_file)],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["hook failed"]
    return json.loads(proc.stdout or "{}"), None


def static_checks(report: Report, root: Path, element: dict, metadata: dict) -> dict | None:
    resource = flavor_resource(element)
    report.check(f"POST {FLAVOR_PATH} resource exists", resource is not None,
                 "the gateway calls this exact path for OpenAiChatCompletions")
    tags = str(metadata.get("tags") or "")
    report.check(f"element-metadata tags include {FLAVOR_TAG}", FLAVOR_TAG in tags, f"tags={tags!r}")

    params = list(element.get("parameters") or []) + list((resource or {}).get("parameters") or [])
    header_ok = any(
        str(p.get("vendorName", "")).lower() == "x-api-key" and p.get("vendorType") == "header" for p in params
    )
    sources = [hook_source(root, resource, element, "preRequest")] if resource else []
    header_ok = header_ok or any(s and "x-api-key" in s.lower() for s in sources)
    report.check("API key is sent in the x-api-key header", header_ok)

    leaked = [
        p.get("vendorName") or p.get("name")
        for p in params
        if p.get("vendorType") in ("query", "path")
        and any(h in f"{p.get('vendorName', '')} {p.get('name', '')}".lower() for h in CREDENTIAL_HINTS)
    ]
    report.check("no credential parameter in the query string or path", not leaked, f"found {leaked}")

    secret_defaults = [
        c.get("key")
        for c in element.get("configuration") or []
        if (c.get("encrypt") or c.get("type") == "PASSWORD") and str(c.get("defaultValue") or "").strip()
    ]
    report.check("no secret config entry has a default value", not secret_defaults, f"found {secret_defaults}")
    return resource


def hook_checks(report: Report, root: Path, element: dict, resource: dict) -> None:
    pre = hook_source(root, resource, element, "preRequest")
    post = hook_source(root, resource, element, "postRequest")
    report.check("preRequest hook registered on the flavor resource", pre is not None)
    report.check("postRequest hook registered on the flavor resource", post is not None)
    for name, src in (("preRequest", pre), ("postRequest", post)):
        if src is not None:
            report.check(f"{name} hook has no console.log", "console.log" not in src)

    configuration = {"base.url": "https://inference.acme.example.com", "custom.api.key": "<TEST_KEY>"}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        if pre is not None:
            out, err = run_hook(pre, {
                "request_body_map": OPENAI_REQUEST, "request_body": json.dumps(OPENAI_REQUEST),
                "request_path_variables": {}, "request_parameters": {}, "request_headers": {},
                "request_vendor_headers": {}, "request_vendor_path": resource.get("vendorPath", ""),
                "configuration": configuration,
            }, work)
            if report.check("preRequest hook runs and calls done()", err is None, " ".join(err or [])):
                body = as_obj(out.get("request_vendor_body")) or {}
                vendor_path = str(out.get("request_vendor_path") or resource.get("vendorPath") or "")
                report.check(f"request goes to {VENDOR_PATH}", vendor_path.rstrip("/").endswith(VENDOR_PATH), vendor_path)
                report.check("model is forwarded", body.get("model") == "acme-large", str(body.get("model")))
                report.check("system prompt becomes instructions", body.get("instructions") == "Be brief.",
                             str(body.get("instructions")))
                report.check("messages become human/model turns (text parts flattened)",
                             body.get("turns") == EXPECTED_TURNS, json.dumps(body.get("turns")))
                report.check("max_tokens becomes limits.max_new_tokens",
                             (body.get("limits") or {}).get("max_new_tokens") == 64, json.dumps(body.get("limits")))
                report.check("temperature becomes sampling.temperature",
                             (body.get("sampling") or {}).get("temperature") == 0.3, json.dumps(body.get("sampling")))

        if post is not None:
            for stop, finish in (("complete", "stop"), ("token_limit", "length")):
                out, err = run_hook(post, {
                    "response_iserror": False, "response_status_code": 200, "response_headers": {},
                    "response_body": vendor_answer(stop), "configuration": configuration,
                    "request_body_map": OPENAI_REQUEST,
                }, work)
                if not report.check(f"postRequest hook runs ({stop})", err is None, " ".join(err or [])):
                    continue
                body = as_obj(out.get("response_body")) or {}
                choices = body.get("choices") or []
                choice = choices[0] if choices else {}
                message = choice.get("message") or {}
                if stop == "complete":
                    report.check("answer is a chat.completion object", body.get("object") == "chat.completion",
                                 str(body.get("object")))
                    report.check("exactly one choice", len(choices) == 1, str(len(choices)))
                    report.check("assistant message carries the vendor text",
                                 message.get("role") == "assistant" and message.get("content") == "Fine, thanks.",
                                 json.dumps(message))
                    usage = body.get("usage") or {}
                    report.check("usage is mapped",
                                 usage.get("prompt_tokens") == 12 and usage.get("completion_tokens") == 4
                                 and usage.get("total_tokens") == 16, json.dumps(usage))
                report.check(f"stop={stop} maps to finish_reason={finish}", choice.get("finish_reason") == finish,
                             str(choice.get("finish_reason")))

            error_body = {"error": {"code": "unauthorized", "message": "bad key"}}
            out, err = run_hook(post, {
                "response_iserror": True, "response_status_code": 401, "response_headers": {},
                "response_body": error_body, "configuration": configuration, "request_body_map": OPENAI_REQUEST,
            }, work)
            if report.check("postRequest hook runs on a vendor error", err is None, " ".join(err or [])):
                passed_through = "response_body" not in out or as_obj(out.get("response_body")) == error_body
                status_kept = out.get("response_status_code") in (None, 401)
                report.check("vendor error passes through with its status", passed_through and status_kept,
                             json.dumps(out)[:200])


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    root = Path(args[0])
    report = Report()
    element_path = root / "app" / "element" / "element.json"
    metadata_path = root / "app" / "element" / "element-metadata.json"
    if not report.check("connector files exist", element_path.exists() and metadata_path.exists(), str(root)):
        return report.finish()
    element = load_json(element_path)
    metadata = load_json(metadata_path)
    resource = static_checks(report, root, element, metadata)
    if "--hooks" in sys.argv and resource is not None:
        hook_checks(report, root, element, resource)
    return report.finish()


if __name__ == "__main__":
    sys.exit(main())
