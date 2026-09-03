# Mixed-result retrain mock (improve-loop regression)

Overlay for `../../smoke/selective_prompt_rollback.yaml`. List it **second** in
`template_sources`, after `../mock_template`, so `mocks/uip` here wins the PATH
shadow while the base template's `mocks/curl` and seeded `calls.log` /
`calls.jsonl` remain.

## Why it exists

Workflow step P7 of the Improve Prompts Guide — update instructions, wait out the
retrain, re-read metrics, compare, and roll back **only** the fields that
regressed — cannot be reached on a static fixture: the branch only exists once the
same field has two different scores, so the mock has to move between reads.

The e2e caps at one iteration by design, and `../e2e/check_full_lifecycle.py`
states outright that F1 direction is never graded there.

## State machine

Advanced by `fields update-prompts`; state lives in `.iter1` / `.iter2` marker
files beside the script.

| State | Version | Vendor Name F1 | Invoice Date F1 |
|-------|---------|----------------|-----------------|
| (no marker) | 15 | **0.34** | **0.88** |
| `.iter1` | 16 | **0.71** (+0.37) | **0.62** (−0.26) |
| `.iter2` | 17 | 0.71 | 0.86 |

The mixed result is the whole point. Vendor Name improved and must be **kept**;
Invoice Date dropped past the guide's **>0.1** regression threshold and must be
rolled back to its prior instruction. An agent that reverts the whole iteration
throws away a real gain; one that reverts nothing keeps a real loss. Both are
common.

`.iter2` exists so a correct run converges. Without it, the post-rollback read
would still show 0.62 and an agent that verifies its own fix would roll back
again — failing a task it had already passed.

### State advances per iteration, not per call

`fields update-prompts` promotes the state only when a `get-metrics` has happened
since the last promotion — tracked in a third marker, `.read`, set by
`get-metrics` and consumed by the next update.

This matters because **nothing in the skill requires both fields in one
`--updates` call.** An agent may legitimately send one call per field; advancing
on every call would carry it straight past `.iter1` to `.iter2`, where the mixed
result never appears. Gating on the read also models the real thing more closely:
a retrain is triggered by a batch of changes, and the new scores only become
observable on the next read.

`../check_selective_rollback.py` matches this. It splits the run at the LAST
comparison read and judges the iteration on the union of the calls before it, so
one-call-per-field and one-batched-call are graded identically.

## The baseline instruction that must be restored

`Invoice Date` starts as:

> The issue date of the invoice, printed in the header block near the invoice number.

The task's criteria quote `printed in the header block` from it, so a rollback
that paraphrases rather than restores does not pass. `Vendor Name` starts as the
deliberately threadbare `The vendor.` — that is why it scores 0.34.

## Deliberate limitation: get-taxonomy is not stateful

`projects get-taxonomy` always serves the **baseline** instructions; it does not
echo back the agent's writes. Reproducing an arbitrary `--updates` payload in
`/bin/sh` is not worth the complexity, and the alternative — canned "updated"
text the agent never wrote — would be a fiction that reads like a bug.

The consequence is that the prior instruction stays readable after the write, so
this fixture does not force the agent to have snapshotted it. The task grades
that separately: Critical Rule 4's taxonomy snapshot under
`/tmp/ixp/<project-name>/taxonomies/` is asserted as its own criterion, which is
the behavior the guide actually teaches.

Ordering — baseline read, update, compare read, selective rollback — is checked by
`../check_selective_rollback.py`, not by regex; `file_matches_regex` cannot
express sequence.

Fixture values are hard-coded into the task's criteria. Change a score or an
instruction here and update the task.
