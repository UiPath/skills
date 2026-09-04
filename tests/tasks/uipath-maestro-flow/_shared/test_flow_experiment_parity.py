"""`experiments/flow.yaml` must not drift from `experiments/nightly.yaml`.

flow.yaml exists for one reason: a system prompt stating the run is headless,
which the flow task prompts no longer carry themselves. Everything else — the
docker image, `env_passthrough_extra`, mounts, `checker_context`, `run_limits`,
`post_run` — is copied, because the experiment schema has no `extends`. A secret
added to nightly's passthrough list and not to flow's breaks flow runs with a
missing environment variable and no obvious cause.

This asserts every substantive line of nightly.yaml still appears in flow.yaml.
It does not assert the reverse: flow.yaml is allowed to add the headless
paragraph and its own id and description.

Regex, not PyYAML: CI installs only pytest, and a module-level `import yaml`
would error at collection and take the suite with it (see test_criterion_budgets).
"""

from __future__ import annotations

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_EXPERIMENTS = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "experiments"))
_NIGHTLY = os.path.join(_EXPERIMENTS, "nightly.yaml")
_FLOW = os.path.join(_EXPERIMENTS, "flow.yaml")

# Lines that legitimately differ: the identity of the config itself.
_EXEMPT_PREFIXES = ("experiment_id:", "description:")


def _substantive(path: str) -> list[str]:
    """Non-blank, non-comment lines, minus the config's own identity block."""
    out: list[str] = []
    in_description = False
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("description:"):
            # Folded scalar: skip its indented continuation lines too.
            in_description = stripped.endswith((">", "|"))
            continue
        if in_description:
            if line and not line[0].isspace():
                in_description = False
            else:
                continue
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(_EXEMPT_PREFIXES):
            continue
        out.append(line)
    return out


def test_flow_config_carries_every_nightly_setting():
    flow = set(_substantive(_FLOW))
    missing = [ln for ln in _substantive(_NIGHTLY) if ln not in flow]
    assert not missing, (
        "experiments/flow.yaml has drifted from nightly.yaml. Copy these lines over "
        "(flow.yaml is a snapshot of nightly's runtime plus a headless system prompt):\n  "
        + "\n  ".join(missing)
    )


def test_flow_config_states_the_run_is_headless():
    """The one thing flow.yaml exists to add. The task prompts no longer say it."""
    text = open(_FLOW, encoding="utf-8").read()
    assert "This run is headless." in text
    assert "No user is present" in text
