"""Verify every project-scoped write stayed inside THIS run's own project.

The tenant is shared with concurrent runs, all of which title their project
`codereval-integ-resolve-<random-suffix>`. Matching that prefix alone would
accept a write aimed at a sibling run's project, so the prefix is not the
identity — the random suffix is.

This run's suffix comes from its FIRST `uip ixp projects create` in calls.log.
The wrapper logs invocations regardless of outcome, so the suffix is still
recoverable on a run whose create was rejected (e.g. a 403 tenant). Every
project-scoped write is then required to name a target carrying that suffix:

  create codereval-integ-resolve-d4f0a999 ...   -> suffix d4f0a999
  update-title codereval-integ-resolve-d4f0a999-9ae36e86-ixp   OK
  update-title vendor-invoices-5a097334-ixp                    VIOLATION
  create test-perm-check                                       VIOLATION

report.json is checked against the same suffix because `cleanup_project.py`
deletes whatever project it names — a wrong value there deletes someone else's
project in post_run.
"""
import json
import os
import re
import sys

TITLE_PREFIX = "codereval-integ-resolve-"

# Verbs that mutate a project or add one to the tenant. Read verbs (list, get,
# get-taxonomy) are deliberately absent: reading a shared tenant is how the
# agent discovers its own project, and the prompt only forbids writes.
WRITE_VERBS = re.compile(
    r"^uip\s+ixp\s+"
    r"(?:projects\s+(?:create|update-title|update-prompt|update-model|"
    r"import-taxonomy|publish|unpublish|tag|untag|rollback|delete)"
    r"|documents\s+(?:upload|delete)"
    r"|groups\s+(?:add|remove|update)"
    r"|fields\s+(?:add|remove|update))"
    r"\s+(?P<rest>.*)$"
)


def first_positional(rest):
    """First non-flag argument — the project the write is aimed at."""
    for token in rest.split():
        if not token.startswith("-"):
            return token
    return None


def main():
    if not os.path.exists("mocks/calls.log"):
        print("FAIL - mocks/calls.log missing; cannot verify project scope")
        return 1

    lines = [ln.strip() for ln in open("mocks/calls.log", encoding="utf-8")]
    writes = []
    for ln in lines:
        m = WRITE_VERBS.match(ln)
        if m:
            target = first_positional(m.group("rest"))
            if target:
                writes.append((ln, target))

    creates = [t for ln, t in writes if re.match(r"^uip\s+ixp\s+projects\s+create\b", ln)]
    if not creates:
        print("FAIL - no `uip ixp projects create` in calls.log; run never created a project")
        return 1

    own_title = creates[0]
    if not own_title.startswith(TITLE_PREFIX):
        print("FAIL - first create titled %r; expected the %s<suffix> convention"
              % (own_title, TITLE_PREFIX))
        return 1

    suffix = own_title[len(TITLE_PREFIX):]
    if not suffix:
        print("FAIL - first create titled %r carries no random suffix" % own_title)
        return 1
    print("This run's project suffix: %s" % suffix)

    violations = [ln for ln, target in writes if suffix not in target]
    for ln in violations:
        print("FAIL - write outside own project: %s" % ln)

    # cleanup_project.py acts on this value; a foreign name here deletes a
    # sibling run's project.
    if os.path.exists("report.json"):
        try:
            name = json.load(open("report.json", encoding="utf-8")).get("project_name", "")
        except (ValueError, OSError) as exc:
            print("FAIL - report.json unreadable (%s)" % exc)
            return 1
        if suffix not in str(name):
            print("FAIL - report.json project_name %r is not this run's project" % name)
            return 1
        print("PASS - report.json names this run's own project")

    if violations:
        print("FAIL - %d project-scoped write(s) left this run's project" % len(violations))
        return 1

    print("PASS - all %d project-scoped write(s) stayed inside this run's project" % len(writes))
    return 0


sys.exit(main())
