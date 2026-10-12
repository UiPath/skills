#!/usr/bin/env python3
"""Rebuild the `uip` shim's fixtures from a live coder-eval run.

    gh run download <run-id> -R UiPath/skills -D /tmp/run
    python3 _shared/build_fixtures.py /tmp/run [/tmp/run2 ...] [--out <dir>]

Input: one or more downloaded `run-coder-eval` artifacts of the compliance-pack
suite run LIVE (no shim) — every `output.txt` holds the `--output json`
responses an agent captured. `--out` defaults to ../mock_template/mocks/fixtures.
Run it whenever the gov tool's response shapes change.

The live suite only produces every needed state when run at once on the
shared tenant: pack never applied (cleanup), active right after an enable
(apply / org-scope), and active with drifted settings (a later enable on a
tenant whose policies were edited). A missing state is reported by name and
nothing is written.

Recorded bot identifiers (tenant / org / user ids, email, user name) are
read from the run's own `login status` and `tenant list` responses and
replaced with the fixed values in SYNTHETIC, so no real identifier is
written — and none lives in this script.

One fixture is derived, not recorded: `coverage-all-applied` is the
post-enable capture with every manual control set — the live tenant never
reaches every-clause-deployed, because manual settings need admin values.
"""

import argparse
import copy
import glob
import json
import os
import sys

PACK_ID = "iso-42001-2023"
# Products the ISO 42001 pack deploys; `template get` is recorded for these.
PACK_PRODUCTS = ["AITrustLayer", "Assistant", "Development", "Robot", "StudioWeb"]

SYNTHETIC = {
    "tenants": [
        "5f0c2a8e-3b1d-4e7a-9c64-2d8b7e1f4a90",  # the login tenant
        "b3e81f06-2c4d-4a97-8e15-6d9a0c7f2b43",
        "71d4c9a2-5e08-4b6f-93c1-a2f6e8d04b17",
        "e9a27b5c-4f13-4d80-b6a9-3c5e1f7d8a02",
    ],
    "org": "8e1d4b27-6a3f-4c90-b5e2-7f04c9a1d3b6",
    "user": "2c7e9f14-8b05-4d3a-a6e1-90f3b5d27c48",
    "email": "admin@codereval.local",
    "user_name": "admin",
}


def responses(run_dirs):
    """Every `{"Result": ...}` object in every output.txt, by Code, in file order."""
    dec = json.JSONDecoder()
    by_code = {}
    files = sorted(f for d in run_dirs for f in glob.glob(f"{d}/**/output.txt", recursive=True))
    for path in files:
        text = open(path, encoding="utf-8").read()
        i = 0
        while (j := text.find("{", i)) >= 0:
            try:
                obj, i = dec.raw_decode(text, j)
            except ValueError:
                i = j + 1
                continue
            if isinstance(obj, dict) and "Result" in obj:
                key = obj.get("Code") or "Failure:" + str(obj.get("Message", ""))
                by_code.setdefault(key, []).append(obj)
    return by_code


def template_dumps(run_dirs):
    """{product: dir} for `template list` / `template get` files left in the artifacts."""
    out = {}
    for d in run_dirs:
        for ft in sorted(glob.glob(f"{d}/**/products/*/form-template.json", recursive=True)):
            folder = os.path.dirname(ft)
            if os.path.exists(os.path.join(folder, "form-data.json")):
                out.setdefault(os.path.basename(folder), folder)
    return out


def scrubber(login, tenants):
    pairs = {}
    real_tenants = [t["TenantId"] for t in tenants]
    login_tenant = login["TenantId"]
    ordered = [login_tenant] + [t for t in real_tenants if t != login_tenant]
    if len(ordered) > len(SYNTHETIC["tenants"]):
        sys.exit(f"build_fixtures: {len(ordered)} tenants recorded, only "
                 f"{len(SYNTHETIC['tenants'])} synthetic ids — extend SYNTHETIC")
    pairs.update(zip(ordered, SYNTHETIC["tenants"]))
    pairs[login["OrganizationId"]] = SYNTHETIC["org"]
    pairs[login["UserId"]] = SYNTHETIC["user"]
    pairs[login["UserEmail"]] = SYNTHETIC["email"]
    pairs[json.dumps(login["UserName"])] = json.dumps(SYNTHETIC["user_name"])

    def scrub(obj):
        text = json.dumps(obj, ensure_ascii=False)
        for real, fake in pairs.items():
            text = text.replace(real, fake)
        return json.loads(text)

    return scrub


def pick(items, test, what):
    for obj in items:
        if test(obj):
            return obj
    raise LookupError(what)


def summary(cov):
    return cov["Data"]["Summary"]


def all_applied(active):
    cov = copy.deepcopy(active)
    data = cov["Data"]
    for clause in data["Clauses"]:
        for control in clause["Controls"]:
            if control["Status"] == "manual":
                control["Status"] = "deployed"
        clause["ManualConfigChecks"] = []
        clause["DeployedControlCount"] = sum(c["Status"] == "deployed" for c in clause["Controls"])
        assert clause["DeployedControlCount"] == clause["CheckableControlCount"], clause["ClauseId"]
        clause["Status"] = "fully-deployed"
    for policy in data["DeploymentPolicies"]:
        policy["Status"] = "in-place"
    s = data["Summary"]
    s.update(InPlaceCount=len(data["DeploymentPolicies"]), NeedsManualConfigCount=0,
             UnverifiableCount=0, NewCount=0, DriftedControlCount=0)
    s["ClauseSummary"] = {"FullyDeployedCount": len(data["Clauses"]),
                          "PartiallyDeployedCount": 0, "NotDeployedCount": 0}
    return cov


def build(run_dirs):
    """{fixture name: (json value, compact)} or exit naming what is missing."""
    r = responses(run_dirs)
    dumps = template_dumps(run_dirs)
    get = lambda code: r.get(code, [])  # noqa: E731
    out, missing = {}, []

    def need(name, fn):
        try:
            out[name] = fn()
        except (LookupError, KeyError, IndexError) as exc:
            missing.append(f"{name} ({exc})")

    cov = get("CompliancePacksStateCoverage")
    need("coverage-inactive", lambda: pick(cov, lambda c: summary(c)["ClauseSummary"]["FullyDeployedCount"] == 0
                                           and summary(c)["NewCount"] > 0
                                           and summary(c)["DriftedControlCount"] == 0, "pack-off capture"))
    need("coverage-active", lambda: pick(cov, lambda c: summary(c)["NewCount"] == 0
                                         and summary(c)["DriftedControlCount"] == 0
                                         and summary(c)["UnverifiableCount"] == 0
                                         and summary(c)["ClauseSummary"]["NotDeployedCount"] == 0, "post-enable capture"))
    need("coverage-drifted", lambda: copy.deepcopy(pick(cov, lambda c: summary(c)["DriftedControlCount"] > 0
                                                        and summary(c)["UnverifiableCount"] == 0, "drifted capture")))
    if "coverage-active" in out:
        # One set of live policy ids per product, shared by every active-pack fixture.
        pid = {p["ProductIdentifier"]: p["PolicyId"] for p in out["coverage-active"]["Data"]["DeploymentPolicies"]}
        if "coverage-drifted" in out:
            for p in out["coverage-drifted"]["Data"]["DeploymentPolicies"]:
                p["PolicyId"] = pid[p["ProductIdentifier"]]
        out["coverage-all-applied"] = all_applied(out["coverage-active"])

        def detail():
            d = copy.deepcopy(pick(get("CompliancePacksStateGet"), lambda o: o["Data"]["Active"], "active state get")["Data"])
            d["Policies"] = [{"PolicyType": "Aops", "ExternalPolicyId": v} for v in pid.values()]
            return d
        need("state-detail", detail)

    need("catalog-list", lambda: get("CompliancePacksCatalogList")[0])
    need("catalog-get-" + PACK_ID, lambda: pick(get("CompliancePacksCatalogGet"),
                                                lambda o: o["Data"].get("PackId") == PACK_ID, PACK_ID))
    need("login-status", lambda: get("LoginStatus")[0])
    need("tenant-list", lambda: get("TenantList")[0])
    need("error-404", lambda: pick([o for k, v in r.items() if k.startswith("Failure:HTTP 404: Received HTML") for o in v],
                                   lambda o: True, "empty-tenant 404"))

    # Last recording per product (inputs sorted by path) — any pre-write list will do.
    for obj in get("AopsPolicyList"):
        if obj["Data"]["Result"]:
            out["aops-list-" + obj["Data"]["Result"][0]["Product"]["Name"]] = obj
    for obj in get("AopsPolicyGet")[:1]:
        out["aops-get-" + obj["Data"]["Identifier"]] = obj
    need("aops-deployment-tenant", lambda: pick(get("AopsPolicyDeploymentTenantGet"),
                                                lambda o: all(p["PolicyIdentifier"] is None for p in o["Data"]["TenantPolicies"]),
                                                "unassigned tenant deployment"))

    def products():
        if not dumps:
            raise LookupError("template list dump")
        meta = {}
        for name in sorted(dumps):
            p = json.load(open(os.path.join(dumps[name], "form-template.json")))["product"]
            meta[p["name"]] = {"Name": p["name"], "Label": p["label"], "IsRestricted": p["isRestricted"],
                               "IsCloud": p["isCloud"], "IsRemote": p["isRemote"]}
        return meta
    need("aops-products", products)
    for product in PACK_PRODUCTS:
        def template(product=product):
            folder = dumps[product]
            return {"Template": json.load(open(os.path.join(folder, "form-template.json"))),
                    "FormData": json.load(open(os.path.join(folder, "form-data.json")))}
        need("aops-template-" + product, template)

    if missing:
        sys.exit("build_fixtures: not found in the run(s): " + "; ".join(missing))
    scrub = scrubber(out["login-status"]["Data"], out["tenant-list"]["Data"])
    return {name: scrub(value) for name, value in out.items()}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--out", default=os.path.join(here, "..", "mock_template", "mocks", "fixtures"))
    args = ap.parse_args()
    fixtures = build(args.run_dirs)
    os.makedirs(args.out, exist_ok=True)
    for name, value in sorted(fixtures.items()):
        with open(os.path.join(args.out, name + ".json"), "w", encoding="utf-8") as fh:
            if name.startswith("aops-template-"):
                json.dump(value, fh, ensure_ascii=False, separators=(",", ":"))  # large, machine-only
            else:
                json.dump(value, fh, indent=1, ensure_ascii=False)
    print(f"build_fixtures: wrote {len(fixtures)} fixtures to {os.path.normpath(args.out)}")


if __name__ == "__main__":
    main()
