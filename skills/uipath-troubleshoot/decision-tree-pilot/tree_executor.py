#!/usr/bin/env python3
"""Zero-LLM deterministic decision-tree executor + replay harness (pilot).

Walks a decision tree (gather -> branch -> leaf / llm) against a coder-eval
test's fixtures/mocks/responses/manifest.json (the command->response oracle).
Proves the deterministic spine reaches the correct leaf with NO model calls.

Usage:
  python tree_executor.py <tree.json> <test_dir> [--folder-name NAME] [--state STATE]
"""
import argparse, json, os, re, sys

# ---- manifest oracle -------------------------------------------------------

def load_manifest(test_dir):
    mpath = os.path.join(test_dir, "fixtures", "mocks", "responses", "manifest.json")
    with open(mpath, encoding="utf-8") as f:
        m = json.load(f)
    return m, os.path.dirname(mpath)

def run_cmd(cmd, manifest, resp_dir):
    """First-match-wins, mirroring the mock runner. Returns (parsed, raw, exit)."""
    for rule in manifest.get("rules", []):
        m = rule.get("match")
        if m and (m in cmd or cmd in m):
            if rule.get("passthrough"):
                return None, "", 0
            raw = ""
            fp = os.path.join(resp_dir, rule["file"])
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    raw = f.read()
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None
            return parsed, raw, rule.get("exit_code", 0)
    d = manifest.get("unmocked_default", {})
    return None, d.get("response", "[]\n"), d.get("exit_code", 0)

# ---- jsonpath-lite ---------------------------------------------------------

def resolve_path(obj, path):
    """Supports $.A.B, $.A[0].B, $.A[?Field~=Value].B (substring filter)."""
    if path.startswith("$."):
        path = path[2:]
    cur = obj
    for seg in path.split("."):
        m = re.match(r"^([A-Za-z0-9_]+)(\[(.*)\])?$", seg)
        if not m:
            return None
        name, _, br = m.groups()
        if name:
            if not isinstance(cur, dict) or name not in cur:
                return None
            cur = cur[name]
        if br is not None:
            if br.startswith("?"):              # filter [?Field~=Value]
                fm = re.match(r"^\?([A-Za-z0-9_]+)~=(.+)$", br)
                if not fm or not isinstance(cur, list):
                    return None
                fld, val = fm.groups()
                cur = next((it for it in cur
                            if isinstance(it, dict) and val.lower() in str(it.get(fld, "")).lower()), None)
                if cur is None:
                    return None
            else:                                # index [n]
                idx = int(br)
                if not isinstance(cur, list) or idx >= len(cur):
                    return None
                cur = cur[idx]
    return cur

def predicate(op, value, observed):
    if observed is None:
        return False
    if op == "eq":
        return observed == value
    if op == "matches":
        return re.search(value, observed) is not None
    if op == "contains":
        return value in observed
    return False

# ---- executor --------------------------------------------------------------

def _norm_nodes(t):
    ns = t["nodes"]
    return ns if isinstance(ns, dict) else {n["id"]: n for n in ns}

def walk(tree, manifest, resp_dir, ctx, trees_dir):
    nodes = _norm_nodes(tree)
    nid = tree["entry"]
    current = "(entry)"
    raw_all = []
    trace = []
    propagation = []   # domains/playbooks the path passed THROUGH (cross-system propagation)
    visited = set()
    while True:
        # cross-file dispatch: a goto/route ending in .json loads another tree and continues (carrying ctx)
        if isinstance(nid, str) and nid.endswith(".json"):
            tpath = os.path.join(trees_dir, nid)
            if not os.path.exists(tpath):
                trace.append(("dispatch->MISSING", nid)); return {"outcome": "dispatch_unbuilt", "tree": nid, "propagation_domains": propagation}, trace
            t = json.load(open(tpath, encoding="utf-8"))
            trace.append(("dispatch->tree", nid))
            current = nid; nodes = _norm_nodes(t); nid = t["entry"]
        if (current, nid) in visited:
            trace.append(("CYCLE", current, nid)); return {"outcome": "cycle", "node": nid}, trace
        visited.add((current, nid))
        node = nodes[nid]
        kind = node["kind"]
        if kind == "gather":
            cmd = node["cmd"].format(**ctx)
            parsed, raw, code = run_cmd(cmd, manifest, resp_dir)
            raw_all.append(raw)
            trace.append(("gather", nid, cmd, "exit=%d" % code))
            missed = False
            for var, spec in node.get("bind", {}).items():
                if "path" in spec:
                    val = resolve_path(parsed, spec["path"].format(**ctx)) if parsed is not None else None
                elif "regex" in spec:
                    mm = re.search(spec["regex"], "\n".join(raw_all))
                    val = mm.group(0) if mm else None
                else:
                    val = None
                if val is None:
                    missed = True
                    trace.append(("bind-miss", var))
                else:
                    ctx[var] = val
                    trace.append(("bind", var, val))
            if missed and node.get("on_missing"):
                nid = node["on_missing"]; continue
            nid = node["next"]
        elif kind == "branch":
            if node.get("propagation_ref"):
                propagation.append({"domain": node.get("domain"), "ref": node["propagation_ref"]})
                trace.append(("propagation", nid, node.get("domain"), node["propagation_ref"]))
            # support both schema formats: "children" (field-based) and "cases" (node.on-based)
            children = node.get("children") or node.get("cases") or []
            goto = node.get("default")
            for case in children:
                w = case["when"]
                field = w.get("field", node.get("on"))
                observed = ctx.get(field)
                if predicate(w["op"], w["value"], observed):
                    goto = case.get("goto"); break
            trace.append(("branch", nid, node.get("on"), ctx.get(node.get("on"))))
            nid = goto
        elif kind == "leaf":
            trace.append(("leaf", nid))
            return {"outcome": "leaf", "node": nid,
                    "root_cause": {"cause": node["cause"], "resolution_ref": node.get("playbook") or node.get("resolution_ref"),
                                   "confidence": node.get("confidence")},
                    "propagation_domains": propagation}, trace
        elif kind == "llm":
            trace.append(("llm", nid, node.get("mode")))
            return {"outcome": "llm_fallback", "node": nid, "mode": node.get("mode"),
                    "reason": node.get("reason")}, trace
        else:
            return {"outcome": "error", "node": nid, "msg": "unknown kind %s" % kind}, trace

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree"); ap.add_argument("test_dir")
    ap.add_argument("--folder-name", default="Shared")
    ap.add_argument("--state", default="Faulted")
    ap.add_argument("--job-key", default=None, help="resolved entity key (the LLM/prompt identity-resolution input)")
    a = ap.parse_args()
    with open(a.tree, encoding="utf-8") as f:
        tree = json.load(f)
    manifest, resp_dir = load_manifest(a.test_dir)
    ctx = {"folder_name": a.folder_name, "state": a.state}
    if a.job_key:
        ctx["job_key"] = a.job_key
    trees_dir = os.path.dirname(os.path.abspath(a.tree))
    result, trace = walk(tree, manifest, resp_dir, ctx, trees_dir)
    print("=== TRACE (zero LLM) ===")
    for t in trace:
        print("  " + " | ".join(str(x) for x in t))
    print("=== OUTCOME ===")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
