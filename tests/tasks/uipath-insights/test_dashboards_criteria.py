import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_investigate_criteria import FLAGS, _criteria, _hits

TASKS = ("dashboards/create_smoke.yaml", "dashboards/update_smoke.yaml")

CAPTURE = "Agent did not capture read stdout into the definition file"

GET = "uip insights dashboards get 7f3e9a2b-1c4d-4e5f-8a9b-0c1d2e3f4a5b"

CAPTURES = [
    f"{GET} > dashboard.json",
    f"{GET} --output json > dashboard.json",
    f"{GET} >> ./before.json",
    f"{GET} &> out/dash.json",
    f"{GET} >| dash.json",
    f"{GET} 1> dash.json",
    f"{GET} --output json 2>&1 > d.json",
    f'{GET} > "my dash.json"',
    f"{GET} > 'before.json'",
    f"{GET} | tee before.json",
    f"{GET} --output json | jq .Data > dashboard.json",
    f"{GET} | jq -r '.Data.Definition' > def.json",
    f"{GET} | jq '.Data | {{id: .Id}}' > def.json",
    f"{GET} | jq -c . > ./d.json",
    f"{GET} | jq --arg k v '.Data' > d.json",
    f"{GET} | jq --indent 2 .Data > d.json",
    f"{GET} | jq -S -r .Data >d.json",
    f"{GET} \\\n  --output json > dashboard.json",
    "uip insights dashboards get --process-key abc --output json > dash.json",
    f'bash -lc "{GET} > dashboard.json"',
    f"{GET} | jq \\\n  -r .Data > d.json",
]

NOT_CAPTURES = [
    f"{GET} --output-file before.json",
    f"{GET} --output json",
    f"{GET} 2>&1",
    f"{GET} 2>/dev/null",
    f"{GET} 2>err.txt",
    f"{GET} > /dev/null",
    f"{GET} | jq .Data.Saved",
    f"{GET} | jq '.Data.Count > 3'",
    f"{GET} --output-file 'a>b.json'",
    f"{GET} --output json | jq .Data.Saved\necho done > notes.md",
    f"{GET} --output-file before.json\njq '.Definition.Title = \"x\"' before.json > updated.json",
    f"{GET} | jq -r .Data.Id\ncat seed.json > copy.json",
    f"{GET} --output-file b.json && jq . b.json > c.json",
    f"{GET} | jq .Data.Saved\nls -la > listing.txt",
    f"{GET} | jq .Data;echo x > y.md",
]


def _capture_regex(task_file):
    matches = [crit for crit in _criteria(task_file) if crit["description"] == CAPTURE]
    assert len(matches) == 1, f"{task_file}: expected one {CAPTURE!r} criterion, found {len(matches)}"
    return re.compile(matches[0]["command_pattern"], FLAGS)


def test_create_and_update_share_one_capture_pattern():
    patterns = {task_file: _capture_regex(task_file).pattern for task_file in TASKS}
    assert len(set(patterns.values())) == 1, patterns


@pytest.mark.parametrize("command", CAPTURES)
@pytest.mark.parametrize("task_file", TASKS)
def test_a_stdout_capture_is_caught(task_file, command):
    assert _hits(_capture_regex(task_file), command), f"{task_file} misses the capture {command!r}"


@pytest.mark.parametrize("command", NOT_CAPTURES)
@pytest.mark.parametrize("task_file", TASKS)
def test_a_compliant_read_is_not_a_capture(task_file, command):
    assert not _hits(_capture_regex(task_file), command), f"{task_file} flags the compliant call {command!r}"
