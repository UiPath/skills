"""Verify every project-scoped write targeted the seeded project.

The tenant is shared, so a write aimed anywhere else is a violation. seed.json's
run id identifies this run's project: the backend slugs the seeded title into the
ProjectName (`Codereval Name Resolution d4f0a999` -> `codereval-name-resolution-
d4f0a999-9ae36e86-ixp`), and the hex run id passes through untouched.
"""
import json
import sys

# Write verbs, per assets/uip-catalog-snapshot.json. Read verbs are excluded:
# reading a shared tenant is how the agent finds its project.
WRITE_VERBS = {
    "projects": {"create", "delete", "configure-model", "import-taxonomy", "publish",
                 "unpublish", "untag", "update-prompt", "update-title"},
    "documents": {"upload", "delete"},
    "groups": {"add", "delete", "rename", "update-prompts"},
    "fields": {"add", "change-type", "delete", "rename", "update-prompts"},
    "data-types": {"add", "delete", "rename", "update-instructions"},
    "labellings": {"confirm", "unconfirm", "mark-missing"},
    "deployments": {"create", "upgrade"},
}


def write_target(line):
    """The project a logged write targets, or None if the line is not a write.

    Every write verb takes the project as its first positional. For `projects
    create` that positional is a new title, so a scratch project fails too.
    """
    tokens = line.split()
    if tokens[:2] != ["uip", "ixp"] or len(tokens) < 5:
        return None
    if tokens[3] not in WRITE_VERBS.get(tokens[2], ()):
        return None
    return next((t for t in tokens[4:] if not t.startswith("-")), None)


def main():
    try:
        run_id = json.load(open("seed.json", encoding="utf-8")).get("uuid8", "")
        log = open("mocks/calls.log", encoding="utf-8").read().splitlines()
    except (ValueError, OSError) as exc:
        print("FAIL - cannot read seed.json / mocks/calls.log (%s)" % exc)
        return 1
    if not run_id:
        print("FAIL - seed.json carries no uuid8")
        return 1

    writes = [(ln.strip(), write_target(ln.strip())) for ln in log]
    writes = [(ln, target) for ln, target in writes if target]

    violations = [ln for ln, target in writes if run_id not in target]
    for ln in violations:
        print("FAIL - write outside the seeded project: %s" % ln)
    if violations:
        return 1

    print("PASS - all %d project-scoped write(s) targeted the seeded project" % len(writes))
    return 0


sys.exit(main())
