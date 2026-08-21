#!/usr/bin/env python3
"""pre_run: check the CLI can folder-deploy, then snapshot the tenant's IXP projects.

The capability check exists so environment drift is not mistaken for a skill
regression. `uip ixp deployments create` rides the CLI's `dev` dist-tag; if the
image's tag moves and the verb disappears, the primary gate would fail with the
agent looking at fault. Failing here instead names the real cause.

The snapshot is what lets check_handoff.py tell this run's projects from
pre-existing ones — see ixp_projects.py for why the grader discovers them rather
than asking the agent to report what it built.

No error handling on purpose: a traceback and non-zero exit are the right outcome
for both checks. Continuing without a snapshot would let a pre-existing project
read as one the agent created, and a false pass on the redirect is worse than a
failed run.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ixp_projects import (  # noqa: E402
    SNAPSHOT,
    list_project_names,
    run_uip,
    run_uip_json,
    write_snapshot,
)

# Substrings that would mean a published extractor already covers the fixture
# domain (see documents/README.md). Matched case-insensitively against every
# registry node's display name and type.
DOMAIN_MARKERS = ("vehicle", "registration-cert", "registration_cert", "v5c", "keeper", "vrc-")


def require_deployments_create() -> None:
    """Exit 0 from the subcommand's own --help means the verb exists.

    Checked this way rather than grepping the parent help text, where unrelated
    prose containing "create" would slip past: a real subcommand's --help exits 0,
    an unknown one exits 3.
    """
    completed = run_uip(["ixp", "deployments", "create", "--help"])
    if completed.returncode != 0:
        raise RuntimeError(
            "this `uip` has no `ixp deployments create` — the task cannot pass. "
            "The verb landed in UiPath/cli#3575 and rides the `dev` tool dist-tag; "
            "check the image's CLI_VERSION rather than the skill. "
            f"`uip ixp deployments create --help` exited {completed.returncode}."
        )
    print("OK: `uip ixp deployments create` is available")


def require_domain_uncovered() -> None:
    """Fail if a published extractor already covers the fixture domain.

    The scenario only measures the redirect when nothing on the tenant matches
    the supplied documents. If something does, reusing it is the correct agent
    action and the handoff never fires — the test would go red for a reason that
    has nothing to do with the behaviour under test. That happened once already
    with invoice fixtures (GH run 32484423417), so it is asserted rather than
    assumed.
    """
    run_uip(["maestro", "flow", "registry", "pull", "--force"])
    payload = run_uip_json(
        ["maestro", "flow", "registry", "search", "uipath.ixp", "--output", "json"]
    )
    nodes = payload["Data"]
    covered = [
        node["NodeType"]
        for node in nodes
        if any(
            marker in f"{node.get('DisplayName', '')} {node['NodeType']}".lower()
            for marker in DOMAIN_MARKERS
        )
    ]
    if covered:
        raise RuntimeError(
            "the fixture domain is already covered by published extractor(s) "
            f"{covered} — the agent can correctly reuse one, so this task cannot "
            "measure the handoff. Change the fixture domain (documents/README.md) "
            "or point the run at a tenant without it."
        )
    print(f"OK: none of the {len(nodes)} published IxP node(s) cover the fixture domain")


def main() -> int:
    require_deployments_create()
    require_domain_uncovered()
    project_names = list_project_names()
    write_snapshot(project_names)
    print(f"Snapshotted {len(project_names)} pre-existing IXP project(s) to {SNAPSHOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
