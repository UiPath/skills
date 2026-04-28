# Patch Record

Audit artifact written when the diagnosis mode updates a deployed policy. Captures what changed, why, and who approved it.

## Schema

```jsonc
{
  "fileKind": "compliance-patch-record",
  "schemaVersion": "1.0.0",

  "timestamp": "2026-04-17T14:30:00Z",
  "patchedBy": "nishank.siddharth@uipath.com",
  "organization": "procodeapps",
  "tenant": {
    "identifier": "<guid>",
    "name": "DefaultTenant"
  },

  "trigger": {
    "kind": "governance-error",
    "errorText": "User is forbidden by governance policy to use: gpt-4o-2024-11-20 in EU",
    "source": "user-reported"
  },

  "policy": {
    "identifier": "<guid>",
    "name": "iso-42001-ai-trust-layer",
    "productIdentifier": "AITrustLayer",
    "licenseTypeIdentifier": "NoLicense"
  },

  "changes": [
    {
      "path": "allowed-llm-regions.europe",
      "label": "Europe",
      "from": false,
      "to": true,
      "confidence": "HIGH",
      "reason": "Error text 'in EU' directly matches region path"
    },
    {
      "path": "azure-openai-control-toggle",
      "label": "Open AI",
      "labelDescription": "Disabling models will impact genAI features across products.",
      "from": false,
      "to": true,
      "confidence": "MEDIUM",
      "reason": "gpt-4o-2024-11-20 is an Azure OpenAI model; provider was disabled"
    }
  ],

  "approval": "user-confirmed",      // "user-confirmed" | "user-partial" | "user-declined" | "auto-halted"

  "notProposedOrDeclined": [          // optional — populate on "partial" or "n" approvals, or when a finding was presented but excluded from the final selection
    {
      "path": "allowed-llm-regions.europe",
      "label": "Europe",
      "confidence": "HIGH",
      "current": false,                // current live value, since it was NOT changed
      "reason": "user selected partial; declined the region fix"
    }
  ],

  "priorAttempts": [                  // optional — present when this record is a retry-success or final outcome after one or more failures
    {
      "path": "/home/user/uipath-governance/audit/patch-records/patch-record-iso-42001-ai-trust-layer-20260423T144501Z.json",
      "timestamp": "2026-04-23T14:45:01Z",
      "status": "failed",
      "errorMessage": "Template upgrade in progress",
      "errorInstructions": "A template upgrade may be in progress for this policy. Retry in ~60s."
    }
  ],

  "impactJsonPath": "<absolute path to impact.json from Step 4b>",  // carried across partial re-prompts; final value reflects the last impact run before approval
  "status": "success"                 // "success" | "failed" | "halted"
}
```

## Write rules

1. Write after the `update` call — on success AND failure. Failure records get `"status": "failed"` and an `"error"` field containing the CLI's `Message` + `Instructions` verbatim.
2. **Default path:** `$HOME/uipath-governance/audit/patch-records/patch-record-<policyName>-<timestamp>.json`.
   - Persistent (survives reboots and temp-dir cleanups).
   - Located under `~/uipath-governance/`, a directory owned by this skill — **not** under `~/.uipath/` (that's owned by the UiPath CLI and we don't pollute it). Keeps audit artifacts separate from CLI state and never inside a git repo, which satisfies rule 4 automatically.
   - Mirror the directory convention for deploy records: `$HOME/uipath-governance/audit/deploy-records/`. Create both directories on first write.
3. **Never write to the current working directory by default.** CWD might be a git repo, and patch/deploy records contain tenant + principal identifiers. Previous versions of this doc suggested `./…` — that rule is superseded. Honor an explicit user override (`--record-out <dir>`) if given.
4. **Never commit to git.** The default path above is outside any repo; if the user overrides to a path inside one, warn them loudly before writing.
5. **Resolve `label` (and optional `labelDescription`)** for every change via [../../property-labels.md](../../property-labels.md). If no label exists, omit the field — the `path` is always authoritative. Storing the label snapshot makes the patch record readable even years later when the i18n bundle has drifted.

## Retry chains

When an update fails with a retryable 5xx (template upgrade in progress, transient timeout) and a later retry succeeds, keep **each attempt's record** — don't overwrite. The final successful record's `priorAttempts[]` array lists every prior record's absolute path, in chronological order. Auditors can follow the chain to reconstruct what the CLI said at each step.

Rules:
- Each attempt writes its own patch-record file with its own timestamp.
- Failure records have `status: "failed"` and `priorAttempts[]` empty on the first attempt.
- The second attempt's record includes the first in `priorAttempts[]`; the third includes both; etc.
- Only the **final** record (success or final-failure halt) is the canonical record to cite in reports. Intermediate failure records are linked via `priorAttempts[]`, not presented to the user as primary output.
- Do not delete intermediate failure records after success — they're audit evidence that the CLI hit a transient problem.

## The `notProposedOrDeclined[]` rationale

A patch record that only lists applied changes creates a subtle lie: a future auditor reads "we fixed the Anthropic toggle" and doesn't know we also identified a region block as MOST LIKELY but the user declined to fix it. That matters for incident review — the user made an explicit, informed choice, and the record must preserve that choice.

Populate the array whenever HIGH/MEDIUM findings existed but were excluded from the final apply:
- `partial` approval → fields NOT selected go here.
- `n` approval → every HIGH/MEDIUM finding goes here, `status: "halted"`.
- `y` with impact-driven reduction → same rules.

LOW findings are informational and do NOT need to appear in `notProposedOrDeclined[]` — they weren't proposed in the first place.

## Relationship to deploy records

Deploy records (`compliance-deploy-record`) capture pack application. Patch records capture post-deployment fixes. Together they form the full audit trail:
- Deploy record says: "these policies were created from this pack"
- Patch record says: "this policy was later modified because of this error"

An auditor reads both to understand the current policy state vs. the original compliance baseline.
