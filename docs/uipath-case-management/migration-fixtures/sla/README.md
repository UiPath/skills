# SLA Golden Fixtures

Compatibility fixtures for the `sla` plugin direct-JSON-write migration. Assert that JSON emitted by the direct-write path is structurally equivalent to JSON produced by the `uip maestro case sla set` / `rules add` / `escalation add` CLI subcommands, and probe JSON-only gap-fill scenarios.

> **Temporary — developer verification only.** These fixtures live outside the skill on purpose: they exist to verify migration correctness during the CLI → JSON shift, and will be removed once every plugin has migrated. Runtime agents do not load them.

## Files

### CLI-parity golden

| File | Purpose |
|---|---|
| `input.sdd-fragment.md` | Minimal sdd fragment exercising the CLI-expressible subset of the SLA plugin (root default + 1 conditional rule + 1 escalation on default; stage default + 1 stage escalation on default) |
| `cli-output.json` | Constructed per the CLI source of truth at `cli/packages/case-tool/src/commands/sla.ts` (current source; see Current status below) |
| `json-write-output.json` | Hand-written to match the direct-JSON-write spec in [`plugins/sla/impl-json.md`](../../../skills/uipath-case-management/references/plugins/sla/impl-json.md) |
| `diff.sh` | Strips random `esc_xxxxxx` escalation IDs from both files, then diffs; passes if structurally equivalent |

### Gap-fill probes (JSON-only)

Each probe is a complete `caseplan.json` exercising one scenario that CLI cannot author. Used to empirically test validator/renderer acceptance of JSON-strategy output.

| File | Scenario |
|---|---|
| `gap-fill/conditional-escalation.json` | Escalation attached to a conditional `slaRules[]` entry (CLI always attaches to default) |
| `gap-fill/exception-stage-sla.json` | `slaRules[]` on a `case-management:ExceptionStage` (CLI's `requireStageForSla` rejects this) |
| `gap-fill/multi-recipient.json` | One `EscalationRule` with `recipients: [User, UserGroup]` (CLI emits one rule per recipient) |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation parity

Run `uip maestro case validate` on both `cli-output.json` and `json-write-output.json` — both must produce the **same** validator result (pass, or the same warning/error profile).

The fragment has no edges — the default trigger has no outgoing edge, so the validator is expected to report the stage as orphaned (`Stage Review has no incoming edges` / `Trigger has no outgoing edges`). Both outputs should exhibit the same failure profile.

## Running the gap-fill probes

For each file in `gap-fill/`, run `uip maestro case validate <file> --output json` and record the result in [`plugins/sla/impl-json.md § Compatibility`](../../../skills/uipath-case-management/references/plugins/sla/impl-json.md#compatibility). Expected outcome:

- `conditional-escalation.json` — pass (runtime supports per-rule escalation; FE renders it, per Studio Web-authored caseplan examples)
- `exception-stage-sla.json` — pass on validator (runtime accepts slaRules on any stage kind); visual render in Studio Web to be confirmed separately
- `multi-recipient.json` — pass (`EscalationRuleRecipient[]` type accepts ≥1 recipients)

If any probe fails validate, file a runtime / schema bug and flag the JSON-strategy gap-fill as unsupported until fixed.

## Regenerating `cli-output.json`

When the CLI binary version emits v17 schema:

```bash
WORK=$(mktemp -d)
cd "$WORK"
uip maestro case cases add --name "SlaProbe" --file caseplan.json --output json

uip maestro case stages add caseplan.json \
  --label "Review" \
  --description "Review stage" \
  --output json

REVIEW_ID=$(jq -r '.nodes[] | select(.data.label == "Review") | .id' caseplan.json)

uip maestro case sla set caseplan.json --count 5 --unit d --output json
uip maestro case sla rules add caseplan.json \
  --expression "=js:vars.priority === 'Urgent'" \
  --count 30 --unit min --output json
uip maestro case sla escalation add caseplan.json \
  --trigger-type at-risk --at-risk-percentage 80 \
  --recipient-scope User \
  --recipient-target "79570334-ed71-439e-b172-d9fc780fd61b" \
  --recipient-value "manager@corp.com" \
  --display-name "Notify Manager" \
  --output json

uip maestro case sla set caseplan.json --stage-id "$REVIEW_ID" --count 2 --unit d --output json
uip maestro case sla escalation add caseplan.json \
  --stage-id "$REVIEW_ID" \
  --trigger-type sla-breached \
  --recipient-scope UserGroup \
  --recipient-target "00000000-0000-0000-0000-000000000001" \
  --recipient-value "Order Mgmt" \
  --output json

cp caseplan.json <path-to-this-folder>/cli-output.json
# The captured file will have a different stage id than `Stage_aB3kL9`;
# update json-write-output.json to match (both ids must agree since diff.sh
# does not normalize stage ids — only escalation ids).
```

Then re-run `./diff.sh` to confirm the direct-JSON-write fixture still matches. If the diff fails, the CLI output shape changed — update `json-write-output.json` and [`plugins/sla/impl-json.md`](../../../skills/uipath-case-management/references/plugins/sla/impl-json.md) to reflect the new spec.

## Regenerating `json-write-output.json`

Follow the JSON Recipe in [`plugins/sla/impl-json.md`](../../../skills/uipath-case-management/references/plugins/sla/impl-json.md). Escalation IDs (`esc_xxxxxx`) are hand-picked to be distinct from the CLI fixture — they exercise the ID-stripping normalizer in `diff.sh`. The stage ID must match whatever is in `cli-output.json` (diff.sh does not normalize stage IDs).

## Current status

Constructed against the CLI source code at `cli/packages/case-tool/src/commands/sla.ts` as of 2026-04. Key observations:

- `root.version: "v17"`, `root.publishVersion: 2`, `root.data.intsvcActivityConfig: "v2"`, `root.data.uipath: { variables: { inputOutputs: [] }, bindings: [] }` — all populated by `cases add` per current source. When regenerating with an installed CLI binary still at 0.1.21 (which emits `v16` + `data: {}`), the fixture will need to be re-based to match the binary's actual output.
- CLI's `sla escalation add` emits `displayName: options.displayName` (possibly `undefined`, which JSON.stringify drops). Our fixture reflects this — the stage-level escalation rule has no `displayName` key because the equivalent CLI invocation omits `--display-name`.
- Both files use stable recipient UUIDs so the diff is deterministic.
