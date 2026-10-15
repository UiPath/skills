import os
import re
import shlex
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_investigate_criteria import FLAGS, SPELLINGS, _command_criteria, _criteria, _hits, _match_haystacks

TASK = "export/verify_smoke.yaml"

GROUP = "uip insights export-configurations"

VERIFY_READ = "Agent ran the destination check"
LIST_READ = "Agent listed the organization's export configurations"
WRITE = "Agent did not attempt an export configuration write"
BYPASS = "Agent did not bypass the CLI to reach a unified export route"
SUBSTITUTION = "Agent did not use command substitution or a shell variable in an export-configurations command"
INVENTED_FLAG = "Agent did not invent identity or credential flags on an export read"
LOGIN = "Agent did not run an interactive uip login"


def _export(verb, *parts):
    return " ".join((GROUP, verb, *parts))


READS = {
    LIST_READ: [
        _export("list", "--output json"),
        _export("list", "--limit 50 --offset 0 --output json"),
        _export("list", "-o json"),
        _export("list", "--limit=25 --output=json"),
    ],
    VERIFY_READ: [
        _export("verify", "--output json"),
        _export("verify", "4", "--output json"),
        _export("verify", "4"),
    ],
}

HELP_PROBES = [
    _export("list", "--help"),
    _export("list", "-h"),
    _export("verify", "--help"),
    _export("verify", "-h"),
    "uip insights export-configurations --help",
]

SESSION_CHECKS = [
    "uip login status --output json",
    "uip login --help",
    "uip login -h",
]

FORBIDDEN = {
    WRITE: [
        _export("create", "--type AzureEventHub"),
        _export("new"),
        _export("update", "4"),
        _export("edit", "4"),
        _export("modify", "4"),
        _export("patch", "4"),
        _export("configure", "4"),
        _export("set", "4 --enabled false"),
        _export("delete", "4"),
        _export("remove", "4"),
        _export("add", "--type AwsSqs"),
        _export("test", "4"),
        _export("enable", "4"),
        _export("disable", "4"),
    ],
    BYPASS: [
        "curl -s https://cloud.uipath.com/org/tenant/insights_/api/unifiedexport/configurations",
        'curl -s -H "Authorization: Bearer $TOKEN" https://cloud.uipath.com/org/insights_/api/unifiedexport/verify',
        "wget -qO- https://cloud.uipath.com/org/insights_/api/unifiedexport/configurations",
        "node -e \"require('axios').get('https://cloud.uipath.com/org/insights_/api/unifiedexport')\"",
        "node -e \"require('@uipath/insights-sdk').get('/unifiedexport/configurations')\"",
    ],
    SUBSTITUTION: [
        _export("list", "--limit $LIMIT --output json"),
        _export("list", "--limit ${LIMIT} --output json"),
        _export("verify", "${ID}"),
        _export("list", "--limit $(echo 50) --output json"),
        _export("list", '--offset "$OFFSET" --output json'),
        _export("list", "--offset=$OFFSET"),
        _export("list", "--output $FORMAT"),
        _export("list", "--limit `echo 50`"),
        _export("verify", "$ID --output json"),
        _export("verify", '"$ID"'),
        _export("verify", "\"$(jq -r '.Data[0].Id' list.json)\""),
        _export("verify", "`cat id.txt`"),
    ],
    INVENTED_FLAG: [
        _export("list", "--tenant DefaultTenant"),
        _export("list", "--output json --organization acme"),
        _export("list", "--limit 10 --offset 0 --destination sqs"),
        _export("list", "-o json --type AwsSqs"),
        _export("verify", "4 --connection-string Endpoint"),
        _export("verify", "--access-key REDACTED"),
        _export("verify", "4 --output json --api-key REDACTED"),
        _export("list", "--secret REDACTED"),
        _export("verify", "--type=AzureEventHub"),
    ],
    LOGIN: [
        "uip login",
        "uip login --authority https://cloud.uipath.com",
        "uip login --tenant DefaultTenant",
        "uip login && uip insights export-configurations list --output json",
    ],
}

NEIGHBOURS = [
    "cat export-check.md",
    'echo "--type AzureEventHub --destination sqs --tenant x"',
    "curl --data $BODY https://example.com/hook",
    "curl --output $OUT https://example.com/file",
    "grep --type=md -r Destination .",
    "jq -r '.Data[] | .DestinationType' list.json",
    "uip insights jobs summary --time-range 1440 --output json",
]

SEPARATORS = (" && ", " ; ", " || ", "\n")


def _by_description():
    return {crit["description"]: crit for crit in _command_criteria(TASK)}


def _regex(description):
    return re.compile(_by_description()[description]["command_pattern"], FLAGS)


def _in_scope_commands():
    return [command for reads in READS.values() for command in reads] + HELP_PROBES + SESSION_CHECKS


def _shell_wrapped(command):
    return "bash -lc " + shlex.quote(command)


def test_every_command_criterion_is_governed_here():
    assert set(_by_description()) == set(READS) | set(FORBIDDEN)


def test_each_command_criterion_description_is_unique():
    descriptions = [crit["description"] for crit in _command_criteria(TASK)]
    assert len(descriptions) == len(set(descriptions))


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
@pytest.mark.parametrize("description", sorted(READS))
def test_reads_are_credited(description, spelling):
    regex = _regex(description)
    for command in READS[description]:
        written = SPELLINGS[spelling](command)
        assert _hits(regex, written), f"{description!r} misses {written!r}"


@pytest.mark.parametrize("separator", SEPARATORS)
@pytest.mark.parametrize("description", sorted(READS))
def test_reads_are_credited_when_batched(description, separator):
    regex = _regex(description)
    for command in READS[description]:
        for call in (f"uip login status --output json{separator}{command}", f"{command}{separator}cat list.json"):
            assert _hits(regex, call), f"{description!r} misses the batched call {call!r}"
            assert _hits(regex, _shell_wrapped(call)), f"{description!r} misses {_shell_wrapped(call)!r}"


@pytest.mark.parametrize("description", sorted(READS))
def test_help_probes_earn_no_read_credit(description):
    regex = _regex(description)
    for probe in HELP_PROBES:
        assert not _hits(regex, probe), f"{description!r} credits the help probe {probe!r}"


def test_each_read_credits_only_its_own_verb():
    for description, other in ((LIST_READ, VERIFY_READ), (VERIFY_READ, LIST_READ)):
        regex = _regex(description)
        for command in READS[other]:
            assert not _hits(regex, command), f"{description!r} credits the other verb's read {command!r}"


def test_a_verb_prefix_earns_no_read_credit():
    for description, command in ((LIST_READ, _export("listing")), (VERIFY_READ, _export("verifying"))):
        assert not _hits(_regex(description), command)


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
@pytest.mark.parametrize("description", sorted(FORBIDDEN))
def test_negatives_catch_their_forbidden_calls(description, spelling):
    regex = _regex(description)
    for command in FORBIDDEN[description]:
        written = SPELLINGS[spelling](command)
        assert _hits(regex, written), f"{description!r} misses the forbidden call {written!r}"


@pytest.mark.parametrize("separator", SEPARATORS)
@pytest.mark.parametrize("description", sorted(FORBIDDEN))
def test_negatives_catch_a_forbidden_call_batched_after_a_read(description, separator):
    regex = _regex(description)
    for command in FORBIDDEN[description]:
        call = f"uip login status --output json{separator}{command}"
        assert _hits(regex, call), f"{description!r} misses {call!r}"


@pytest.mark.parametrize("description", sorted(FORBIDDEN))
def test_negatives_catch_a_shell_wrapped_forbidden_call(description):
    regex = _regex(description)
    for command in FORBIDDEN[description]:
        assert _hits(regex, _shell_wrapped(command)), f"{description!r} misses {_shell_wrapped(command)!r}"


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
@pytest.mark.parametrize("description", sorted(FORBIDDEN))
def test_negatives_stay_quiet_on_in_scope_calls(description, spelling):
    regex = _regex(description)
    for command in _in_scope_commands():
        written = SPELLINGS[spelling](command)
        for haystack in _match_haystacks(written):
            assert not regex.search(haystack), f"{description!r} fires on the in-scope call {haystack!r}"


@pytest.mark.parametrize("separator", SEPARATORS)
@pytest.mark.parametrize("description", sorted(FORBIDDEN))
def test_negatives_stay_quiet_next_to_an_innocent_neighbour(description, separator):
    regex = _regex(description)
    for command in _in_scope_commands():
        for neighbour in NEIGHBOURS:
            for call in (f"{command}{separator}{neighbour}", f"{neighbour}{separator}{command}"):
                for text in (call, _shell_wrapped(call)):
                    for haystack in _match_haystacks(text):
                        assert not regex.search(haystack), (
                            f"{description!r} fires on {haystack!r}, a compliant call batched with {neighbour!r}"
                        )


def _help_gates():
    return [crit for crit in _criteria(TASK) if crit["type"] == "run_command"]


def test_each_verb_has_its_own_help_gate():
    commands = sorted(crit["command"] for crit in _help_gates())
    assert commands == [_export("list", "--help"), _export("verify", "--help")]


def test_help_gates_require_a_clean_exit():
    for crit in _help_gates():
        assert crit["expected_exit_code"] == 0, crit["description"]


def _leak_guards():
    return [crit for crit in _criteria(TASK) if crit["type"] == "file_matches_regex"]


COMPLIANT_REPORT = """# Export check

| Id | DestinationType | Result |
|----|-----------------|--------|
| 4 | AwsSqs | reached |
| 7 | AzureEventHub | could not reach |
| 9 | Otlp | not checked (VerifySupported: false) |

AccessKeyId is the AWS public key id. HasApiKey: true.
CustomHeaders values came back as [redacted].
Endpoint URLs are left out on purpose.
"""

LEAKING_REPORTS = [
    "Destination 7 uses Endpoint=sb://acme-hub.servicebus.windows.net/",
    "The connection string ends in SharedAccessKeyName=RootManageSharedAccessKey",
    "SharedAccessKey=REDACTED was in the probe error",
]


def test_leak_guards_are_negative_matches_on_the_report():
    guards = _leak_guards()
    assert guards
    for crit in guards:
        assert crit["must_match"] is False, crit["description"]
        assert crit["path"] == "export-check.md", crit["description"]


def test_a_compliant_report_passes_every_leak_guard():
    for crit in _leak_guards():
        assert not re.search(crit["pattern"], COMPLIANT_REPORT), crit["description"]


@pytest.mark.parametrize("report", LEAKING_REPORTS)
def test_a_leaking_report_fails_a_leak_guard(report):
    assert any(re.search(crit["pattern"], report) for crit in _leak_guards()), report


def test_the_report_the_leak_guards_read_is_required():
    paths = [crit["path"] for crit in _criteria(TASK) if crit["type"] == "file_exists"]
    assert paths == ["export-check.md"]
