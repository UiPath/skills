"""Pin the hand-tuned command_patterns PR #4574 rewrote to recorded agent commands.

Each pattern is loaded from its task YAML (never a copy) and searched with and
without re.DOTALL: coder-eval 1.x compiles command patterns with DOTALL, and the
grade must be the same on both versions.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest
import yaml

TASKS = Path(__file__).resolve().parents[1] / "tasks"
FLAGS = (0, re.DOTALL)


def _pattern(task: str, description: str) -> str:
    data = yaml.safe_load((TASKS / task).read_text(encoding="utf-8"))
    (criterion,) = [c for c in data["success_criteria"] if c.get("description") == description]
    return criterion["command_pattern"]


def _hits(pattern: str, command: str) -> set[bool]:
    return {bool(re.search(pattern, command, flags)) for flags in FLAGS}


# --- uipath-review: one criterion per project ---------------------------------

REVIEW = "uipath-review/review_multi_project_solution.yaml"
PROJECT_A = _pattern(REVIEW, "Agent invoked uip rpa get-errors or validate on ProjectA")
PROJECT_B = _pattern(REVIEW, "Agent invoked uip rpa get-errors or validate on ProjectB")

BOTH = [
    'for p in ProjectA ProjectB; do uip rpa get-errors --project-dir "MySolution/$p" --output json; done',
    'for p in ProjectA ProjectB\ndo\n  uip rpa validate --project-dir "MySolution/$p" --output json\ndone',
    'for d in MySolution/*/; do uip rpa get-errors --project-dir "$d" --output json; done',
]
ONLY_A = [
    "uip rpa get-errors --project-dir MySolution/ProjectA --output json",
    "cd MySolution/ProjectA && uip rpa validate --file-path Main.xaml --output json",
    "uip rpa validate --file-path MySolution/ProjectA/Main.xaml --project-dir MySolution/ProjectA",
    # ProjectB is named in the same call but never validated.
    "ls MySolution/ProjectA MySolution/ProjectB && uip rpa get-errors --project-dir MySolution/ProjectA",
    "uip rpa get-errors --project-dir MySolution/ProjectA; cat MySolution/ProjectB/Main.xaml",
    "for p in ProjectA ProjectB; do ls $p; done; uip rpa validate --project-dir MySolution/ProjectA",
]
NEITHER = [
    "cat <<EOF\nProjectA ProjectB\nEOF\nuip rpa get-errors --help",
    "uip rpa get-errors --project-dir MySolution/ProjectAB",
    "ls MySolution/ProjectA MySolution/ProjectB",
]


@pytest.mark.parametrize("command", BOTH)
def test_review_loop_credits_both_projects(command):
    assert _hits(PROJECT_A, command) == {True}
    assert _hits(PROJECT_B, command) == {True}


@pytest.mark.parametrize("command", ONLY_A)
def test_review_credits_only_the_validated_project(command):
    assert _hits(PROJECT_A, command) == {True}
    assert _hits(PROJECT_B, command) == {False}


@pytest.mark.parametrize("command", NEITHER)
def test_review_credits_neither_project(command):
    assert _hits(PROJECT_A, command) == {False}
    assert _hits(PROJECT_B, command) == {False}


# --- uipath-mcp-servers: no new login after not_supported ----------------------

LOGIN = _pattern(
    "uipath-mcp-servers/swagger-not-supported/task.yaml",
    "Agent did NOT log in again (not_supported is not an auth failure)",
)


@pytest.mark.parametrize(
    "command",
    [
        "uip login",
        "uip login --tenant DefaultTenant",
        "uip auth login",
        "uip login refresh",
        "uip login tenant set DefaultTenant",
        "uip login status --output json && uip login",
    ],
)
def test_login_guard_forbids_a_new_login(command):
    assert _hits(LOGIN, command) == {True}


@pytest.mark.parametrize(
    "command",
    [
        "uip login status",
        "uip login status --output json",
        "uip auth login status",
        "uip login which",
        "uip login tenant list --output json",
        "uip login profiles list",
        "uip login --help",
        "uip login -h",
    ],
)
def test_login_guard_allows_reading_the_session(command):
    assert _hits(LOGIN, command) == {False}


# --- uipath-test: clone commands skip single-quoted words whole ----------------

CLONE_LABELS = _pattern(
    "uipath-test/testcase_clone_smoke.yaml",
    "Agent cloned with labels included (`clone ... --include ... labels`, must succeed)",
)
SUBSTITUTED_KEY = "\"$(python3 -c 'import json;print(json.load(open(\"k.json\"))[\"key\"])')\""


@pytest.mark.parametrize(
    "command",
    [
        "uip tm testcases clone --project-key HEALTH --test-case-key HEALTH:5 --include steps labels --output json",
        f"uip tm testcases clone --test-case-key {SUBSTITUTED_KEY} --new-name X --include labels",
        "uip tm testcases clone --test-case-key 'HEALTH:5' --new-name 'Copy of 5' --include 'labels'",
        "uip tm testcases clone --test-case-key HEALTH:5 \\\n  --include labels",
    ],
)
def test_clone_labels_matches(command):
    assert _hits(CLONE_LABELS, command) == {True}


@pytest.mark.parametrize(
    "command",
    [
        "uip tm testcases clone --project-key HEALTH --test-case-key 'HEALTH:5'; "
        "uip tm testcases get --test-case-key 'HEALTH:5' --include labels",
        "uip tm testcases clone --test-case-key 'HEALTH:5' --name X | jq '.Data' ; echo '--include labels'",
        "uip tm testcases clone --test-case-key HEALTH:5 --include steps",
    ],
)
def test_clone_labels_stops_at_the_command_boundary(command):
    assert _hits(CLONE_LABELS, command) == {False}


def test_clone_labels_does_not_backtrack_on_many_quoted_words():
    command = "uip tm testcases clone " + " ".join(f"'a{i}'" for i in range(24)) + " --include steps"
    for flags in FLAGS:
        start = time.perf_counter()
        assert not re.search(CLONE_LABELS, command, flags)
        assert time.perf_counter() - start < 0.05


SIBLINGS = [
    ("uipath-test/testcase_lifecycle_e2e.yaml", "testcases", "--new-name X"),
    ("uipath-test/testset_clone_smoke.yaml", "testsets", '--new-name "$NAME"'),
    ("uipath-test/testset_order_integration.yaml", "testsets", '--new-name "$NAME"'),
    ("uipath-test/testset_lifecycle_e2e.yaml", "testsets", '--new-name "$NAME"'),
]


def _clone_pattern(task: str) -> str:
    data = yaml.safe_load((TASKS / task).read_text(encoding="utf-8"))
    (pattern,) = [
        c["command_pattern"]
        for c in data["success_criteria"]
        if c.get("type") == "command_executed" and r"\s+clone\b" in c.get("command_pattern", "")
    ]
    return pattern


@pytest.mark.parametrize(("task", "noun", "new_name"), SIBLINGS)
def test_sibling_clone_patterns_skip_a_quoted_semicolon(task, noun, new_name):
    pattern = _clone_pattern(task)
    command = f"uip tm {noun} clone --key {SUBSTITUTED_KEY} {new_name}"
    assert _hits(pattern, command) == {True}
    assert _hits(pattern, f"uip tm {noun} clone --key 'K:1'; echo {new_name}") == {False}


# --- uipath-test: a `run --help` triage probe is not a re-trigger --------------

NO_RERUN = _pattern(
    "uipath-test/project_permissions_access_integration.yaml",
    "Triaged rather than blindly re-triggering: did NOT re-run the execution this turn",
)


@pytest.mark.parametrize(
    "command",
    [
        "uip tm testsets run --help",
        "uip tm testcases run -h",
        "uip tm executions run --help --output json",
        "uip tm testsets run --help && echo done",
        # help flag anywhere in the run's segment, not only leading:
        "uip tm testsets run --test-set-key X --help",
        "uip tm executions run --execution-id abc --help --output json",
        "uip tm testsets run \\\n  --help",
    ],
)
def test_no_rerun_ignores_a_help_probe(command):
    # Reading a run command's help while triaging the 403 is not a re-trigger;
    # the criterion (max_count 0) must not match it.
    assert _hits(NO_RERUN, command) == {False}


@pytest.mark.parametrize(
    "command",
    [
        "uip tm testsets run --test-set-key EVFXPERMAT:1 --output json",
        "uip tm executions run --execution-id abc --execution-type manual",
        "uip tm testcases run --test-case-id uuid --execution-type automated",
        "uip tm testsets run --help && uip tm testsets run --test-set-key X",
    ],
)
def test_no_rerun_still_catches_a_real_retrigger(command):
    # A genuine re-run must still match either side of a help probe.
    assert _hits(NO_RERUN, command) == {True}


# --- uipath-agents: resource lookups via the CLI or Studio Web's host tool -----
# Studio Web looks resources up with its ManageSolutionResources host tool,
# recorded as a ProxyTool call. coder-eval matches a non-Bash call against
# json.dumps(parameters), so these haystacks are built the same way.


def _host_call(**params) -> str:
    return json.dumps({"toolName": "ManageSolutionResources", "method": "execute", "params": params})


APIWF = "uipath-agents/lowcode/external_apiworkflow_tool/external_apiworkflow_tool.yaml"
APIWF_LIST = _pattern(
    APIWF,
    "Agent discovered the API workflow identity with uip solution resources list --kind Process "
    "(or ManageSolutionResources)",
)
APIWF_GET = _pattern(
    APIWF, "Agent fetched the API workflow configuration with uip solution resources get (or ManageSolutionResources)"
)
ESCALATION_LIST = _pattern(
    "uipath-agents/lowcode/guardrails/escalation_app/escalation_app.yaml",
    "Agent ran uip solution resources list (or ManageSolutionResources) to look up the escalation app",
)
KEY = "be88b8d6-ec4d-484c-9474-805dd82d8d68"


@pytest.mark.parametrize(
    ("pattern", "call"),
    [
        # Recorded in the 2026-11-17 Studio Web run.
        (APIWF_LIST, _host_call(action="list", kind="Process", source="remote", searchTerm="WeatherAPI")),
        (APIWF_LIST, _host_call(action="list", source="local", kind="Process", searchTerm="WeatherAPI")),
        (APIWF_GET, _host_call(action="get", resourceKey=KEY)),
        (ESCALATION_LIST, _host_call(action="list", kind="App", source="remote", searchTerm="Guardrail.Escalation.Action.App")),
        # The CLI forms still count.
        (APIWF_LIST, "uip solution resources list --kind Process --source remote --search WeatherAPI --output json"),
        (APIWF_GET, f'uip solution resources get "{KEY}" --output json'),
        (ESCALATION_LIST, "uip solution resources list --kind App --output json"),
        (APIWF_LIST, "uip solution resources list --source remote \\\n  --kind Process --output json"),
        (APIWF_LIST, "uip solution resources list --kind=Process --output json"),
    ],
)
def test_resource_lookup_counts_the_cli_or_the_host_tool(pattern, call):
    assert _hits(pattern, call) == {True}


@pytest.mark.parametrize(
    ("pattern", "call"),
    [
        (APIWF_LIST, _host_call(action="list", kind="App", source="remote")),
        (APIWF_LIST, _host_call(action="add", kind="Process", source="remote", name="WeatherAPI")),
        (APIWF_LIST, "uip solution resources list --source local --output json"),
        (APIWF_GET, _host_call(action="list", kind="Process", source="remote")),
        (APIWF_GET, _host_call(action="add", kind="Process", source="remote", name="WeatherAPI")),
        (ESCALATION_LIST, _host_call(action="get", resourceKey=KEY)),
        # A kind named by a later command in the same call is not this list's kind.
        (APIWF_LIST, "uip solution resources list --kind App && uip solution resources add --kind Process --name X"),
        (APIWF_LIST, "uip solution resources list --kind App\nuip solution resources add --kind Process --name X"),
    ],
)
def test_resource_lookup_needs_the_same_action_and_kind(pattern, call):
    assert _hits(pattern, call) == {False}


def _host_tool_patterns() -> list[str]:
    patterns = []
    for task in sorted((TASKS / "uipath-agents").rglob("*.yaml")):
        data = yaml.safe_load(task.read_text(encoding="utf-8"))
        for c in (data or {}).get("success_criteria") or []:
            if "ManageSolutionResources" in (c.get("command_pattern") or ""):
                patterns.append(c["command_pattern"])
    return patterns


QUOTES = [
    # A file or subagent prompt that only quotes a lookup is not a lookup.
    json.dumps(
        {
            "file_path": "/solution/notes.md",
            "content": "uip solution resources list --kind Process --kind App --kind Index --kind MemorySpace "
            f"--source local; uip solution resources get {KEY}\n"
            + _host_call(action="list", kind="Process", source="local")
            + _host_call(action="get", resourceKey=KEY),
        }
    ),
    json.dumps({"prompt": f"Run uip solution resources list --kind Process, then uip solution resources get {KEY}"}),
    json.dumps(
        {
            "file_path": "/solution/notes.md",
            "content": "uip solution resources refresh --output json; uip solution resources add --source remote "
            "--kind Process --kind Index --kind Connection --kind MemorySpace\n"
            + _host_call(action="add", kind="Process", source="remote"),
        }
    ),
]


@pytest.mark.parametrize("pattern", _host_tool_patterns())
@pytest.mark.parametrize("call", QUOTES)
def test_resource_lookup_ignores_other_tools_quoting_it(pattern, call):
    assert _hits(pattern, call) == {False}


# An edit forwards an arbitrary patch, so lookup fields nested in it are not a lookup.
NESTED = [
    _host_call(action="edit", resourceKey=KEY, patch={"action": action, "kind": kind, "source": "local"})
    for action in ("list", "get", "add")
    for kind in ("Process", "App", "Index", "MemorySpace", "Connection")
] + [
    _host_call(action="edit", resourceKey=KEY, patch={"params": {"action": "get"}}),
    _host_call(action="edit", resourceKey=KEY, patch={"params": {"action": "list", "kind": "Process", "source": "local"}}),
]


@pytest.mark.parametrize("pattern", _host_tool_patterns())
@pytest.mark.parametrize("call", NESTED)
def test_resource_lookup_ignores_lookup_fields_nested_in_an_edit(pattern, call):
    assert _hits(pattern, call) == {False}


# --- uipath-agents: declaring the resource in the solution ---------------------
# Terminal agents run `uip solution resources refresh`; Studio Web cannot (no .uipx
# on disk), so its skill declares each resource with `resources add`, through the
# CLI or the ManageSolutionResources host tool.

_DECLARE = "Agent declared {what} in the solution: uip solution resources refresh, or resources add --kind {kind} (CLI or ManageSolutionResources)"


def _declare(task: str, what: str, kind: str) -> str:
    return _pattern(f"uipath-agents/lowcode/{task}", _DECLARE.format(what=what, kind=kind))


RPA_DECLARE = _declare("external_rpa_tool/external_rpa_tool.yaml", "the FibonacciRPA process", "Process")
MAESTRO_DECLARE = _declare("external_maestro_tool/external_maestro_tool.yaml", "the Maestro process", "Process")
INDEX_DECLARE = _declare("context_index/context_index.yaml", "the index", "Index")
IS_DECLARE = _declare("is_connector_tool/is_connector_tool.yaml", "the connection", "Connection")
MEMORY_DECLARE = _declare("memory_space/memory_space.yaml", "the memory space", "MemorySpace")


@pytest.mark.parametrize(
    ("pattern", "call"),
    [
        # Recorded in the 2026-11-19 Studio Web run.
        (RPA_DECLARE, _host_call(action="add", source="remote", kind="Process", name="FibonacciRPA", folderPath="Shared/uipath-agents/FibonacciRPA")),
        (MAESTRO_DECLARE, 'uip solution resources add --source remote --kind Process --name "ProcurementProcess" --folder-path "Shared" --output json'),
        (INDEX_DECLARE, _host_call(action="add", source="remote", kind="Index", name="UiPathAgentsPolicies")),
        (IS_DECLARE, _host_call(action="add", source="remote", kind="Connection", cloudKey="2dc0d640-eac6-445f-9f0c-d5654c4f3b1a")),
        (MEMORY_DECLARE, _host_call(action="add", source="remote", kind="MemorySpace", name="UiPathAgentsSupportMemory", folderPath="Shared/uipath-agents")),
        (RPA_DECLARE, "uip solution resources add --source remote \\\n  --kind Process --name FibonacciRPA --output json"),
        (IS_DECLARE, "uip solution resources add --source remote --kind=Connection --cloud-key 2dc0d640 --output json"),
        # The terminal refresh still counts.
        (RPA_DECLARE, "uip solution resources refresh --output json"),
        (MEMORY_DECLARE, "cd MemorySol && uip solution resources refresh --output json"),
    ],
)
def test_declaring_the_resource_counts_refresh_or_add(pattern, call):
    assert _hits(pattern, call) == {True}


@pytest.mark.parametrize(
    ("pattern", "call"),
    [
        (RPA_DECLARE, _host_call(action="add", source="remote", kind="Index", name="UiPathAgentsPolicies")),
        (RPA_DECLARE, _host_call(action="list", source="local")),
        (RPA_DECLARE, "uip solution resources list --source remote --kind Process --output json"),
        (INDEX_DECLARE, "uip solution resources add --source remote --kind Process --name FibonacciRPA"),
        # A kind named by a later command in the same call is not this add's kind.
        (RPA_DECLARE, "uip solution resources add --kind Index --name X && uip solution resources list --kind Process"),
        (RPA_DECLARE, "uip solution resources add --kind Index --name X\nuip solution resources list --kind Process"),
        (MEMORY_DECLARE, "uip solution resources add --source remote --kind MemorySpaceArchive --name X"),
        (IS_DECLARE, _host_call(action="add", source="remote", kind="MemorySpace", name="UiPathAgentsSupportMemory")),
    ],
)
def test_declaring_the_resource_needs_add_of_the_same_kind(pattern, call):
    assert _hits(pattern, call) == {False}


# --- uipath-maestro-flow: voice tasks count a real `flow debug`, not a mention ---
# Both voice tasks share one pattern. Codex records every Bash call as
# `/bin/bash -lc '<cmd>'`, so the wrapper forms are pinned on the raw text.

VOICE_DEBUG = [
    _pattern("uipath-maestro-flow/voice/voice_inbound_call.yaml", "Agent did not try to debug an inbound voice flow"),
    _pattern(
        "uipath-maestro-flow/voice/voice_outbound_call.yaml",
        "Agent did not run flow debug, which would place a real outbound call",
    ),
]


@pytest.mark.parametrize("pattern", VOICE_DEBUG)
@pytest.mark.parametrize(
    "command",
    [
        "uip maestro flow debug .",
        "uip flow debug VoiceFlow",
        "cd VoiceFlow && uip maestro flow debug . 2>&1 | tail -50",
        "(cd VoiceFlow && uip maestro flow debug .)",
        "UIP_LOG_LEVEL=debug uip maestro flow debug .",
        'out=$(uip maestro flow debug .)',
        '"$UIP" maestro flow debug .',
        "for f in A B; do uip maestro flow debug $f; done",
        "timeout 60 uip maestro flow debug .",
        "cd VoiceFlow && timeout --foreground 120s uip maestro flow debug .",
        "env UIP_LOG_LEVEL=debug uip maestro flow debug .",
        "exec uip maestro flow debug .",
        "sudo -E uip maestro flow debug .",
        "sudo -u builder uip maestro flow debug .",
        "timeout -k 5 60 uip maestro flow debug .",
        "nice -n 10 uip maestro flow debug .",
        "nohup uip maestro flow debug . > debug.log 2>&1 &",
        "/usr/local/bin/uip maestro flow debug .",
        "ls -d */ | xargs -I {} uip maestro flow debug {}",
        "find . -name '*.flow' -exec uip maestro flow debug {} \\;",
        # coder-eval also searches the quote-resolved text, so `eval "uip ..."` is this.
        "eval uip maestro flow debug .",
        "T=60; timeout $T uip maestro flow debug .",
        "/bin/bash -lc 'timeout 60 uip maestro flow debug .'",
        "/bin/bash -lc 'cd VoiceFlow && env A=1 uip maestro flow debug .'",
        # A heredoc line that starts with the command still counts.
        "cat <<'EOF' > run.sh\nuip maestro flow debug .\nEOF",
    ],
)
def test_voice_debug_counts_a_real_call(pattern, command):
    assert _hits(pattern, command) == {True}


@pytest.mark.parametrize("pattern", VOICE_DEBUG)
@pytest.mark.parametrize(
    "command",
    [
        "cat > README.md <<'EOF'\n# Voice\nDo not run `uip maestro flow debug` on this flow.\nEOF",
        "cat > README.md <<'EOF'\n1. uip maestro flow debug is not supported here.\nEOF",
        "cat > README.md <<'EOF'\nIn this env uip maestro flow debug places a real call.\nEOF",
        "apply_patch <<'PATCH'\n*** Add File: README.md\n+Avoid `uip maestro flow debug`; it dials for real.\nPATCH",
        "grep -rn 'uip maestro flow debug' skills/",
        'echo "will not run timeout 60 uip maestro flow debug"',
        "ps -eo args | rg 'uip maestro flow debug|flow-tool'",
        "/bin/bash -lc 'grep -rn \"uip maestro flow debug\" references/'",
        "uip maestro flow validate VoiceFlow.flow",
    ],
)
def test_voice_debug_ignores_a_mention(pattern, command):
    assert _hits(pattern, command) == {False}
