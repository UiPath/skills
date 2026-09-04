#!/usr/bin/env python3
"""The coded-action-deploy scripts declare their own contract; this asserts the skill agrees.

The design is that determinism comes from the scripts and context from the skill. That only holds
if the two cannot drift: a SKILL.md table listing a script that no longer exists, or calling a
mutating script read-only, is worse than no table at all because an agent trusts it.

So the scripts are the source of truth (`--describe`) and this test makes the prose answer to them.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "uipath-ontology-coded-action-deploy"
SCRIPTS = SKILL_DIR / "scripts"
SKILL_MD = SKILL_DIR / "SKILL.md"
REQUIRED_KEYS = {"name", "purpose", "phase", "inputs", "outputs", "mutates", "exit_codes"}


def entry_points() -> list[Path]:
    """The scripts an agent invokes. A leading underscore means a shared module, not an entry point."""
    return sorted(p for p in SCRIPTS.glob("*.py") if not p.name.startswith("_"))


def describe(script: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(script), "--describe"], cwd=ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise AssertionError("%s --describe exited %d: %s" % (script.name, proc.returncode, proc.stderr))
    return json.loads(proc.stdout)


def table_rows() -> dict[str, dict]:
    """The Scripts table in SKILL.md, keyed by script filename."""
    rows = {}
    for line in SKILL_MD.read_text().splitlines():
        match = re.match(r"^\|\s*`([a-z_]+\.py)`\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$", line)
        if match:
            name, phase, what, mutates = match.groups()
            rows[name] = {"phase": phase, "what": what, "mutates": "yes" in mutates.lower()}
    return rows


class ScriptContractTests(unittest.TestCase):
    def test_every_entry_point_describes_itself(self):
        for script in entry_points():
            with self.subTest(script=script.name):
                payload = describe(script)
                missing = REQUIRED_KEYS - set(payload)
                self.assertFalse(missing, "%s: --describe omits %s" % (script.name, sorted(missing)))
                self.assertEqual(payload["name"], script.stem)
                self.assertIsInstance(payload["mutates"], bool)

    def test_describe_never_runs_the_action(self):
        """--describe is answered before argparse, so it must work on a script with required
        positionals -- and must not perform the action."""
        payload = describe(SCRIPTS / "deploy_release.py")   # requires a version argument
        self.assertEqual(payload["name"], "deploy_release")
        self.assertTrue(payload["mutates"])

    def test_the_skill_table_lists_exactly_the_entry_points(self):
        listed = set(table_rows())
        found = {p.name for p in entry_points()}
        self.assertEqual(listed, found, "SKILL.md's Scripts table and scripts/ disagree")

    def test_the_skill_table_agrees_on_what_mutates(self):
        rows = table_rows()
        for script in entry_points():
            with self.subTest(script=script.name):
                self.assertEqual(
                    rows[script.name]["mutates"], describe(script)["mutates"],
                    "%s: SKILL.md and --describe disagree about whether it mutates" % script.name,
                )

    def test_the_skill_table_agrees_on_the_phase(self):
        rows = table_rows()
        for script in entry_points():
            with self.subTest(script=script.name):
                self.assertEqual(
                    rows[script.name]["phase"], describe(script)["phase"].split(" - ")[0],
                    "%s: SKILL.md and --describe disagree about the phase" % script.name,
                )

    def test_no_stale_script_names_remain_in_the_docs(self):
        """The multi-verb scripts are gone; a doc still naming one would send an agent to a file
        that does not exist."""
        stale = ("solution_release.py", "solution_scaffold.py", "ttl_patch.py",
                 "scaffold_solution.py", "build_package.py", "next_version.py")
        hits = []
        # Not just markdown: one of these used to live in a docstring that gets written verbatim
        # into every generated jobs.map.json, so it shipped to users' disks.
        candidates = [f for pattern in ("*.md", "*.py", "*.json")
                      for f in SKILL_DIR.rglob(pattern)]
        for doc in sorted(candidates):
            for number, line in enumerate(doc.read_text().splitlines(), 1):
                for name in stale:
                    if name in line:
                        hits.append("%s:%d names %s" % (doc.relative_to(ROOT), number, name))
        self.assertFalse(hits, "docs name scripts that no longer exist:\n  " + "\n  ".join(hits))

    def test_no_removed_design_survives_in_the_prose(self):
        """Filenames were not the only thing a refactor invalidated.

        Each term below named a mechanism that was removed, and each was left behind in prose that
        still read as instruction: a patch phase that no longer runs, a scaffold that no longer
        writes an `.npmrc`, a `folder-id` subcommand that no longer exists, a template skeleton
        that is no longer shipped, a `functions/` layout that became `main.ts`. Every one of them
        would have been caught by one grep, so this is that grep.

        Each entry carries the phrasing that is still legitimate, because most of these words have
        a correct use: "nothing is patched" is the fact, "is patched into the TTL" is the stale
        claim.
        """
        removed = {
            "patched into": "the deploy patches no artifact; say so, or say nothing",
            "deploy-then-patch": "there is no patch phase",
            "PENDING_DEPLOY": "the concept is gone",
            "SPIKE-PENDING": "resolved: `uip solution deploy upgrade` does not exist",
            "folder-id ": "removed subcommand; `uip or folders get` returns Key and Id",
            "solution-skeleton": "no longer shipped",
            "template mode": "no longer exists",
            "/functions holds": "the staged layout is main.ts, not functions/",
            "writes each project's `.npmrc`": "nothing writes an .npmrc",
            "scaffold owns the project's `.npmrc`": "nothing writes an .npmrc",
        }
        allowed = ("Nothing is patched", "nothing to patch", "It patches nothing", "patches nothing")
        hits = []
        roots = [SKILL_DIR,
                 ROOT / "skills" / "uipath-ontology-authoring",
                 ROOT / "skills" / "uipath-ontology-modeler",
                 ROOT / "tools"]
        candidates = [f for root in roots for pattern in ("*.md", "*.py", "*.json")
                      for f in root.rglob(pattern)]
        for doc in sorted(set(candidates)):
            for number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
                if any(ok in line for ok in allowed):
                    continue
                for term, why in removed.items():
                    if term in line:
                        hits.append("%s:%d — %r (%s)" % (doc.relative_to(ROOT), number, term, why))
        self.assertFalse(hits, "prose describes a mechanism that was removed:\n  " + "\n  ".join(hits))

    def test_every_suite_in_this_area_actually_runs_tests(self):
        """A suite whose `unittest.main()` block is gone exits 0 having run nothing, which reads
        as a pass. That happened once during this refactor, when a regex removing the last test in
        a file took the entrypoint with it."""
        suites = [
            ROOT / "tests" / "scripts" / "test_entry_points.py",
            ROOT / "tests" / "scripts" / "test_coded_action_scripts.py",
            ROOT / "tests" / "coded_action_preflight" / "test_coded_action_preflight.py",
            ROOT / "tests" / "scripts" / "test_ontology_skill_structure.py",
        ]
        for suite in suites:
            with self.subTest(suite=suite.name):
                text = suite.read_text()
                self.assertIn('if __name__ == "__main__":', text,
                              "%s has no entrypoint; running it directly would exit 0 silently"
                              % suite.name)
                self.assertIn("unittest.main(", text, suite.name)
                self.assertGreater(text.count("def test_"), 0, suite.name)

    def test_shared_modules_are_not_entry_points(self):
        for module in sorted(SCRIPTS.glob("_*.py")):
            with self.subTest(module=module.name):
                self.assertNotIn('if __name__ == "__main__"', module.read_text())


    def test_every_argparse_option_is_declared_in_describe(self):
        """`--describe` is the contract, so a flag missing from it is an undocumented flag.

        Read statically from the argparse calls rather than by running the script, so a flag added
        behind a condition still counts. This caught `--force-version` on publish_package.py -- the
        one flag that overrides the version guard, and the one most worth having written down.
        """
        for script in entry_points():
            declared = describe(script)["inputs"].get("args", [])
            # 'deployment_name (optional)' declares 'deployment_name'; match on the first token.
            declared_names = {entry.split()[0] for entry in declared}
            tree = ast.parse(script.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "add_argument"):
                    continue
                for arg in node.args:
                    if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                        continue
                    with self.subTest(script=script.name, option=arg.value):
                        self.assertIn(
                            arg.value, declared_names,
                            "%s takes %r but --describe does not list it in inputs.args (%s)"
                            % (script.name, arg.value, sorted(declared_names)))

    def test_describe_declares_no_argument_the_script_does_not_take(self):
        """The other direction: a stale entry is as misleading as a missing one."""
        for script in entry_points():
            declared = {e.split()[0] for e in describe(script)["inputs"].get("args", [])}
            tree = ast.parse(script.read_text(encoding="utf-8"))
            actual = {
                arg.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
                for arg in node.args
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            }
            with self.subTest(script=script.name):
                self.assertEqual(
                    declared - actual, set(),
                    "%s --describe lists argument(s) argparse does not define" % script.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
