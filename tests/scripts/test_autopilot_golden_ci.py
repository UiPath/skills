import base64
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".github/scripts/golden-sandbox-auth.sh"
WORKFLOW = yaml.safe_load((REPO / ".github/workflows/run-coder-eval.yml").read_text())
EXPERIMENT = yaml.safe_load((REPO / "tests/experiments/autopilot-golden.yaml").read_text())
GOLDEN = REPO / "tests/tasks/uipath-api-workflow/golden"


def jwt(subject):
    def part(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")
    return f"{part({'alg': 'RS256', 'typ': 'JWT'})}.{part({'sub': subject, 'exp': 4102444800})}.c2lnbmF0dXJlLXNpZ25hdHVyZQ"


def auth_text(access, refresh):
    return (f"UIPATH_ACCESS_TOKEN={access}\nUIPATH_REFRESH_TOKEN={refresh}\nUIPATH_URL=https://cloud.example.test\n"
            "UIPATH_ORGANIZATION_NAME=org\nUIPATH_ORGANIZATION_ID=00000000-0000-4000-8000-000000000001\n"
            "UIPATH_TENANT_NAME=tenant\nUIPATH_TENANT_ID=00000000-0000-4000-8000-000000000002\n")


def step(job, name):
    return next(s for s in WORKFLOW["jobs"][job]["steps"] if s.get("name") == name)


def mode(path):
    return stat.S_IMODE(os.lstat(path).st_mode)


class SandboxAuthTests(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home_auth = self.tmp / "home/.uipath/.auth"
        self.home_auth.parent.mkdir(parents=True)
        self.first = (jwt("first"), "first-refresh-" + "a" * 40)
        self.second = (jwt("second"), "second-refresh-" + "b" * 40)
        self.home_auth.write_text(auth_text(*self.first))
        self.mint = self.tmp / "mint.sh"
        self.mint.write_text(f"#!/usr/bin/env bash\nprintf '%s' '{auth_text(*self.second)}' > \"$AUTH_FILE\"\n")
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.github_env = self.tmp / "github_env"
        self.env = {**os.environ, "AUTH_FILE": str(self.home_auth), "TOKEN_KEEPER_DIR": str(self.tmp / "runner"),
                    "REFRESH_AUTH_SCRIPT": str(self.mint), "TOKEN_KEEPER_INTERVAL": "1",
                    "TOKEN_KEEPER_RETRY_DELAYS": "0", "GITHUB_ENV": str(self.github_env),
                    "PATH": f"{self.bin}:{os.environ['PATH']}"}
        for name in ("GITHUB_ACTIONS", "UIPATH_URL", "CLIENT_ID", "CLIENT_SECRET", "UIPATH_ORGANIZATION_ID"):
            self.env.pop(name, None)
        self.runner = self.tmp / "runner"

    def tearDown(self):
        subprocess.run(["bash", str(SCRIPT), "stop"], env=self.env, capture_output=True, timeout=30)
        subprocess.run(["rm", "-rf", str(self.tmp)], check=False)

    def run_script(self, command, **env):
        return subprocess.run(["bash", str(SCRIPT), command], env={**self.env, **env}, capture_output=True,
                              text=True, timeout=60)

    def stub_curl(self):
        log, self.argv = self.tmp / "revoked", self.tmp / "argv"
        (self.bin / "curl").write_text(
            "#!/usr/bin/env bash\n"
            f"printf '%s\\n' \"$@\" >> '{self.argv}'\n"
            "for arg in \"$@\"; do case \"$arg\" in\n"
            "  *openid-configuration) echo '{\"revocation_endpoint\": \"https://id.example.test/revoke\"}'; exit 0 ;;\n"
            f"  token@*) cat \"${{arg#token@}}\" >> '{log}'; echo >> '{log}' ;;\n"
            f"  client_secret@*) cat \"${{arg#client_secret@}}\" > '{self.tmp / 'secret'}' ;;\n"
            "esac; done\nprintf 200\n")
        (self.bin / "curl").chmod(0o755)
        return log

    def test_start_gives_containers_a_read_only_copy_without_the_refresh_token(self):
        result = self.run_script("start", TOKEN_KEEPER_INTERVAL="3000")
        self.assertEqual(result.returncode, 0, result.stderr)
        copy = self.runner / "sandbox-auth/.auth"
        self.assertIn(f"UIPATH_ACCESS_TOKEN={self.first[0]}", copy.read_text())
        self.assertNotIn("REFRESH", copy.read_text())
        self.assertNotIn(self.first[1], copy.read_text())
        self.assertEqual((mode(copy), mode(copy.parent)), (0o644, 0o755))
        home = self.runner / "sandbox-uipath"
        self.assertEqual(os.readlink(home / ".auth"), "/.uipath-auth/.auth")
        self.assertEqual(mode(home), 0o777)
        state = self.runner / "token-refresher"
        self.assertEqual((mode(state), mode(state / "minted"), mode(state / "refresh")), (0o700, 0o600, 0o600))
        self.assertEqual((state / "minted").read_text().split(), list(self.first))
        self.assertEqual((state / "refresh").read_text().split(), [self.first[1]])
        self.assertIn(f"UIPATH_SANDBOX_AUTH_DIR={copy.parent}", self.github_env.read_text())
        self.assertNotIn(self.first[0], result.stdout + result.stderr)

    def test_the_refresher_keeps_the_copy_fresh_and_lists_every_token(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        deadline = time.monotonic() + 10
        refreshed = self.runner / "token-refresher/refreshed"
        while not refreshed.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        copy = (self.runner / "sandbox-auth/.auth").read_text()
        self.assertIn(self.second[0], copy)
        self.assertNotIn(self.second[1], copy)
        minted = (self.runner / "token-refresher/minted").read_text().split()
        self.assertTrue(set(self.first) | set(self.second) <= set(minted))

    def test_stop_revokes_every_refresh_token_and_removes_the_copy(self):
        log = self.stub_curl()
        self.assertEqual(self.run_script("start").returncode, 0)
        time.sleep(2.5)
        result = self.run_script("stop", UIPATH_URL="https://cloud.example.test", CLIENT_ID="client",
                                 CLIENT_SECRET="secret-value")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Revoked 2 of 2 refresh token(s)", result.stdout)
        self.assertEqual(sorted(log.read_text().split()), sorted([self.first[1], self.second[1]]))
        self.assertEqual((self.tmp / "secret").read_text(), "secret-value")
        argv = self.argv.read_text()
        for secret in ("secret-value", self.first[1], self.second[1]):
            self.assertNotIn(secret, argv)
        state = self.runner / "token-refresher"
        self.assertFalse((state / "token").exists() or (state / "client_secret").exists())
        self.assertFalse((self.runner / "sandbox-auth/.auth").exists())
        self.assertNotIn(self.first[1], result.stdout + result.stderr)

    def test_stop_masks_every_token_the_run_minted_in_the_job_log(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        time.sleep(2.5)
        result = self.run_script("stop", GITHUB_ACTIONS="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        masked = {line[len("::add-mask::"):] for line in result.stdout.splitlines() if line.startswith("::add-mask::")}
        self.assertTrue(set(self.first) | set(self.second) <= masked)
        for line in result.stdout.splitlines() + result.stderr.splitlines():
            if not line.startswith("::add-mask::"):
                self.assertFalse(any(token in line for token in masked), line)

    def test_stop_without_credentials_warns_and_succeeds(self):
        self.assertEqual(self.run_script("start", TOKEN_KEEPER_INTERVAL="3000").returncode, 0)
        result = self.run_script("stop", UIPATH_URL="", CLIENT_ID="", CLIENT_SECRET="")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stay valid until they expire", result.stderr)

    def test_a_failing_mint_is_retried_reported_and_the_loop_goes_on(self):
        self.mint.write_text("#!/usr/bin/env bash\nexit 1\n")
        self.assertEqual(self.run_script("start", TOKEN_KEEPER_FAILED_WAIT="1").returncode, 0)
        deadline = time.monotonic() + 15
        failed = self.runner / "token-refresher/failed"
        while (not failed.exists() or len(failed.read_text().split()) < 2) and time.monotonic() < deadline:
            time.sleep(0.2)
        self.assertTrue((self.runner / "token-refresher/retried").exists())
        self.assertGreaterEqual(len(failed.read_text().split()), 2)
        self.assertIn("refresh failed", self.run_script("stop").stderr)

    def test_start_fails_when_the_host_login_has_no_access_token(self):
        self.home_auth.write_text("UIPATH_URL=https://cloud.example.test\n")
        self.assertNotEqual(self.run_script("start", TOKEN_KEEPER_INTERVAL="3000").returncode, 0)


class RedactionTests(unittest.TestCase):

    def redact(self, tree, **env):
        script = step("run-linux", "Redact secrets from the eval report")["run"].replace('"/tmp/runs"', repr(str(tree)))
        output = tree.parent / "github_output"
        output.write_text("")
        runner_temp = tree.parent / "runner"
        (runner_temp / "token-refresher").mkdir(parents=True, exist_ok=True)
        (runner_temp / "token-refresher/minted").write_text("opaque-refresh-token-0123456789\n")
        shim = tree.parent / "bin"
        shim.mkdir(exist_ok=True)
        if not (shim / "python").exists():
            (shim / "python").symlink_to(sys.executable)
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60,
                                env={**os.environ, "EXPERIMENT": "autopilot-golden", "GITHUB_OUTPUT": str(output),
                                     "RUNNER_TEMP": str(runner_temp), "HOME": str(tree.parent),
                                     "PATH": f"{shim}:{os.environ['PATH']}", **env})
        return result, output.read_text()

    def clean_up(self, tree):
        script = step("run-linux", "Clean up artifacts (remove .venv, node_modules and symlinks)")["run"]
        subprocess.run(["bash", "-c", script.replace("/tmp/runs", str(tree))], check=True, timeout=60)

    def test_every_file_is_scrubbed_and_the_step_reports_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "runs"
            (tree / "v/task/01/artifacts").mkdir(parents=True)
            token = jwt("leak")
            (tree / "v/task/01/task.log").write_text(f"Authorization: Bearer {token}\n")
            (tree / "v/task/01/artifacts/notes.txt").write_text("refresh opaque-refresh-token-0123456789 here")
            (tree / "v/task/01/artifacts/blob.bin").write_bytes(b"\x00\x01" + token.encode() + b"\xff")
            outside = Path(tmp) / "outside.txt"
            outside.write_text(token)
            (tree / "v/task/01/artifacts/link").symlink_to(outside)
            (tree / "v/task/01/artifacts/dir-link").symlink_to(Path(tmp), target_is_directory=True)
            self.clean_up(tree)
            result, output = self.redact(tree)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("clean=true", output)
            for path in ("v/task/01/task.log", "v/task/01/artifacts/notes.txt", "v/task/01/artifacts/blob.bin"):
                data = (tree / path).read_bytes()
                self.assertNotIn(token.encode(), data)
                self.assertNotIn(b"opaque-refresh-token-0123456789", data)
            self.assertFalse(os.path.lexists(tree / "v/task/01/artifacts/link"))
            self.assertFalse(os.path.lexists(tree / "v/task/01/artifacts/dir-link"))
            self.assertEqual(outside.read_text(), token)

    def test_a_symlink_left_in_the_tree_stops_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "runs"
            (tree / "artifacts").mkdir(parents=True)
            outside = Path(tmp) / "host-login"
            outside.write_text("UIPATH_REFRESH_TOKEN=not-in-any-list-0123456789\n")
            (tree / "artifacts/leak").symlink_to(outside)
            result, output = self.redact(tree)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("clean=true", output)
            self.assertIn("are not regular files", result.stdout)
            self.assertIn("not-in-any-list", outside.read_text())

    def test_a_special_file_stops_publication_and_cleanup_removes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "runs"
            (tree / "v/task/01/artifacts").mkdir(parents=True)
            pipe = tree / "v/task/01/artifacts/pipe\n::warning::x"
            os.mkfifo(pipe)
            result, output = self.redact(tree)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("clean=true", output)
            self.assertIn(repr(str(pipe)), result.stdout)
            self.assertNotIn("\n::warning::x", result.stdout)
            self.clean_up(tree)
            self.assertFalse(os.path.lexists(pipe))
            result, output = self.redact(tree)
            self.assertIn("clean=true", output)

    def test_a_file_that_cannot_be_scrubbed_stops_publication(self):
        if os.geteuid() == 0:
            self.skipTest("root writes read-only files")
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "runs"
            tree.mkdir()
            stuck = tree / "task.log"
            stuck.write_text(jwt("stuck"))
            stuck.chmod(0o444)
            result, output = self.redact(tree)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("clean=true", output)
            self.assertIn("nothing from this run is published", result.stdout)


class PublicationTests(unittest.TestCase):

    def test_the_public_artifact_holds_aggregates_only_for_three_days(self):
        upload = step("run-linux", "Upload the aggregate eval report")
        self.assertIn("inputs.experiment == 'autopilot-golden'", upload["if"])
        self.assertIn("steps.redact.outputs.clean == 'true'", upload["if"])
        paths = upload["with"]["path"].split()
        self.assertEqual(sorted(paths), ["/tmp/runs/*/variant.json", "/tmp/runs/experiment.json",
                                         "/tmp/runs/experiment.md"])
        self.assertLessEqual(int(upload["with"]["retention-days"]), 3)
        full = step("run-linux", "Upload eval report")
        self.assertIn("inputs.experiment != 'autopilot-golden'", full["if"])

    def test_transcripts_reach_the_private_store_only_after_clean_redaction(self):
        publish = step("run-linux", "Publish the run to evalboard")
        self.assertIn("steps.redact.outputs.clean == 'true'", publish["if"])

    def test_the_job_summary_holds_the_comparison_tables_only(self):
        script = step("run-linux", "Append the run report to the job summary")["run"]
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            runs.mkdir()
            (runs / "experiment.md").write_text("| Metric | autopilot |\n")
            (runs / "run.md").write_text("- error: FAIL: a message quoting workflow output\n")
            summary = Path(tmp) / "summary"
            for clean, expected in (("true", "| Metric | autopilot |\n"), ("", "")):
                summary.write_text("")
                subprocess.run(["bash", "-c", script.replace("/tmp/runs", str(runs))], check=True, timeout=30,
                               env={**os.environ, "EXPERIMENT": "autopilot-golden", "CLEAN": clean,
                                    "RUN_MD": str(runs / "run.md"), "GITHUB_STEP_SUMMARY": str(summary)})
                self.assertEqual(summary.read_text(), expected)


    def test_the_verdict_reads_only_the_task_results_coder_eval_writes(self):
        script = step("run-linux", "Plaintext summary + verdict")["run"]
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            (runs / "v/task/01/artifacts/x").mkdir(parents=True)
            (runs / "v/task/01/task.json").write_text(json.dumps({"task_id": "task", "final_status": "SUCCESS"}))
            (runs / "v/task/01/artifacts/x/task.json").write_text(
                json.dumps({"task_id": "planted", "final_status": "FAILURE"}))
            shim = Path(tmp) / "bin"
            shim.mkdir()
            (shim / "python").symlink_to(sys.executable)
            for experiment, listed in (("nightly", True), ("autopilot-golden", False)):
                result = subprocess.run(["bash", "-c", script.replace("/tmp/runs", str(runs))], capture_output=True,
                                        text=True, timeout=60,
                                        env={**os.environ, "EXPERIMENT": experiment, "PATH": f"{shim}:{os.environ['PATH']}",
                                             "GITHUB_STEP_SUMMARY": str(Path(tmp) / "summary")})
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("1/1 PASS (linux)", result.stdout)
                self.assertNotIn("planted", result.stdout)
                self.assertEqual("task: SUCCESS" in result.stdout, listed)
        windows = step("run-windows", "Plaintext summary + verdict")["run"]
        self.assertIn("glob('*/*/*/task.json')", windows)
        self.assertNotIn("rglob", windows)

    def test_the_runner_keeps_nothing_of_the_run(self):
        steps = WORKFLOW["jobs"]["run-linux"]["steps"]
        cleanup = steps[-1]
        self.assertEqual(cleanup["name"], "Remove the run from the runner")
        self.assertEqual(cleanup["if"], "always()")
        for path in ("/tmp/runs", 'gha-"${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"', "UIPATH_SANDBOX_AUTH_DIR",
                     "token-refresher", "$HOME/.uipath/.auth"):
            self.assertIn(path, cleanup["run"])
        names = [s.get("name") for s in steps]
        self.assertEqual(names.index("Remove the golden task containers") + 1, names.index("Stop the token refresher"))
        remove = step("run-linux", "Remove the golden task containers")
        self.assertIn("inputs.experiment == 'autopilot-golden'", remove["if"])
        self.assertIn("docker rm -f", remove["run"])


class RunScopeTests(unittest.TestCase):

    def split(self, globs):
        script = step("partition", "Resolve globs, split by tag, enforce large-run gate")["run"]
        if subprocess.run(["bash", "-c", "shopt -s globstar"], capture_output=True).returncode != 0:
            script = script.replace("shopt -s globstar nullglob", "shopt -s nullglob")
        with tempfile.TemporaryDirectory() as tmp:
            return subprocess.run(["bash", "-c", script], cwd=REPO, capture_output=True, text=True, timeout=60,
                                  env={**os.environ, "INPUT_GLOBS": globs, "CONFIRMED": "false",
                                       "EXPERIMENT": "autopilot-golden", "GITHUB_OUTPUT": str(Path(tmp) / "out")})

    def test_only_golden_scenarios_run_under_autopilot_golden(self):
        self.assertEqual(self.split("tasks/uipath-api-workflow/golden/**/*.yaml").returncode, 0)
        refused = self.split("tasks/uipath-api-workflow/golden/**/*.yaml tasks/uipath-api-workflow/connector/**/*.yaml")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("runs only the tasks under tests/tasks/uipath-api-workflow/golden/", refused.stdout)
        sneaky = self.split("tasks/uipath-api-workflow/golden/../connector/**/*.yaml")
        self.assertNotEqual(sneaky.returncode, 0)

    def test_containers_mount_the_token_only_copy_read_only(self):
        prepare = step("run-linux", "Prepare the coder-eval invocation")["run"]
        self.assertIn('sandbox.docker.extra_mounts=[$sandbox_home:/.uipath:rw,$sandbox_auth:/.uipath-auth:ro]', prepare)
        self.assertIn("DELEGATE_AUTH_TOKEN_FILE=/.uipath-auth/.auth:$sandbox_auth/.auth", prepare)
        self.assertIn("CONTAINER_AUTH=/.uipath-auth/.auth", SCRIPT.read_text())
        mint = step("run-linux", "Mint UiPath bot token (ROPC)")["run"]
        self.assertLess(mint.index('"autopilot-golden"'), mint.index("chmod -R o+rwX"))

    def test_parallelism_must_be_a_positive_whole_number(self):
        script = step("run-linux", "Prepare the coder-eval invocation")["run"]
        for value in ("0", "4 -v", "1;id", "-1"):
            with self.subTest(value=value):
                result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30,
                                        env={**os.environ, "TASK_PARALLELISM": value})
                self.assertEqual(result.returncode, 1)
                self.assertIn("parallelism must be a positive whole number", result.stdout)

    def test_containers_get_no_host_variable_beyond_an_explicit_allowlist(self):
        docker = EXPERIMENT["defaults"]["sandbox"]["docker"]
        self.assertEqual(docker["env_passthrough"], ["HOME", "UIPATH_CLI_DISABLE_VERSION_SYNC"])
        self.assertEqual(set(docker["env_passthrough_extra"]) - {"SKILLS_REPO_PATH"},
                         {name for name in docker["env_passthrough_extra"] if name.startswith("UIPATH_CLI_")})
        prepare = step("run-linux", "Prepare the coder-eval invocation")["run"]
        self.assertNotIn("sandbox.docker.env_passthrough=", prepare)

    def test_only_the_task_with_a_judge_gets_the_gateway_key(self):
        shared = EXPERIMENT["defaults"]["sandbox"]["docker"]["env_passthrough_extra"]
        self.assertFalse({"CODEX_API_KEY", "CODEX_BASE_URL"} & set(shared))
        for task in sorted(GOLDEN.glob("*/*.yaml")):
            data = yaml.safe_load(task.read_text())
            judged = any(c.get("type") == "llm_judge" for c in data.get("success_criteria", []))
            passed = set(((data.get("sandbox") or {}).get("docker") or {}).get("env_passthrough_extra", []))
            self.assertEqual("CODEX_API_KEY" in passed, judged, task.name)


if __name__ == "__main__":
    unittest.main()
