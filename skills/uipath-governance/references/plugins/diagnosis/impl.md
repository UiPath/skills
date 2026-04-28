# Diagnose · Governance Error Investigation + Remediation

Diagnose why an agent, process, or automation was blocked by a governance policy. Fetch all deployed policies on the tenant, correlate the error to the blocking property with confidence ranking, show a diff, and update on approval.

## When this plugin is invoked

Orchestrator detects diagnose mode from phrases like:
- "my agent failed with this governance error: ..."
- "why is model X blocked?"
- "I got a 403 forbidden by governance policy"
- Any error text containing `governance policy`, `forbidden`, or AOPS product keywords

## Shared primitives used

This capability delegates to:
- [../../auth-context.md](../../auth-context.md) — read `UIPATH_TENANT_ID`, `UIPATH_ACCESS_TOKEN`
- [../../policy-crud.md](../../policy-crud.md) — `deployment tenant get`, `policy get` (with full `data`), UPDATE recipe
- [../../property-labels.md](../../property-labels.md) — human labels + descriptions for every property shown in findings, diff, and patch record
- [../../compliance-impact.md](../../compliance-impact.md) — before/after posture delta against local compliance packs; runs between diff preview and the approval gate

## Input contract

```jsonc
{
  "mode": "diagnose",
  "errorText": "<raw error message or natural-language description>",
  "tenantIdentifier": "<from ~/.uipath/.auth UIPATH_TENANT_ID>"
}
```

## Recipe

### 1. Extract signal from the error

Parse `errorText` for structured hints:

| Signal | Example | Maps to |
|---|---|---|
| Model name | `gpt-4o-2024-11-20`, `claude-3`, `gemini-pro` | Provider toggle (`azure-openai-control-toggle`, etc.) |
| Region | `in EU`, `in US`, `in Japan` | `allowed-llm-regions.*` |
| Product context | `governance policy`, `AI Trust Layer` | `productIdentifier` |
| HTTP status | `403`, `forbidden` | Policy enforcement block |
| Feature | `PII masking`, `prompt injection`, `harmful content` | `*-execution-stage`, `*-container.*` |

Don't hardcode mappings. Use these as search hints when scanning actual policy data in Step 3. The property names are self-descriptive — correlate `gpt-4o` → `azure-openai-control-toggle` by reading field names.

If the error text is too vague: ask "Can you share the full error message or describe what you were trying to do?"

### 2. Fetch the tenant deployment map

Use the TENANT-GET recipe in [../../policy-crud.md](../../policy-crud.md#tenant-get-recipe):

```bash
uip gov aops-policy deployment tenant get "$UIPATH_TENANT_ID" --output json
```

Filter `Data.tenantPolicies[]` to entries where `policyIdentifier != null`. Present the landscape:

```
Deployed policies on tenant DefaultTenant:
  AITrustLayer (NoLicense)  → policy "iso-42001-ai-trust-layer" (d0a68808-...)
  Robot (Attended)           → (no custom policy)
  ...

Found 1 deployed custom policy. Fetching configuration...
```

If zero deployed policies: "No custom governance policies on this tenant. The error may be from org-level / global defaults — check the AOPS admin console."

### 3. Fetch full policy (metadata + formData) for each deployed policy (parallel)

Use the read-full-policy recipe from [../../policy-crud.md](../../policy-crud.md#read-full-policy-recipe):

```bash
uip gov aops-policy get <policyIdentifier> --output json
```

`Data.data` contains the full formData. Collect: `{ policyIdentifier → { productIdentifier, policyName, formData: Data.data } }`.

### 4. Correlate with confidence ranking

Scan each policy's `formData` for properties in a blocking state. Rank each finding by confidence:

| Tier | When | Example |
|---|---|---|
| **HIGH** | Direct text match between error and property path segment | `"in EU"` ↔ `allowed-llm-regions.europe` |
| **MEDIUM** | Domain-knowledge inference (one step of reasoning) | `gpt-4o` → Azure OpenAI → `azure-openai-control-toggle` |
| **LOW** | Property is blocking but unrelated to the error | `"in EU"` error + `anthropic-control-toggle: false` |

**Scoring rules (apply in order):**

1. **HIGH** — error contains a synonym/direct reference to a path segment:
   - `"EU"` / `"Europe"` → `allowed-llm-regions.europe` ✓
   - `"PII"` / `"personal data"` / `"masking"` → `pii-processing-mode`, `container.pii-*` ✓
   - Region names, feature names, enum values literally present in the error
   - **Healthcare PHI vocabulary promotes PII findings to HIGH.** Case-insensitive substring match for any of: `patient`, `patient name`, `medical record`, `MRN`, `PHI`, `health information`, `ePHI`, `diagnosis`, `diagnoses`, `prescription`, `medication`, `DOB`, `date of birth`, `SSN`, `social security`, `insurance number`, `subscriber id`, `provider id`, `NPI`, `clinical note`, `discharge summary`, `HIPAA`. Any of these in the error promotes `pii-processing-mode`, `pii-execution-stage`, `pii-entity-table`, and `container.pii-in-flight-*` findings from their baseline tier to HIGH. Typical mapping:
     - `"forbidden to process patient name in prompt"` → `container.pii-in-flight-agents`, `pii-processing-mode` (HIGH — "patient name" is a HIPAA-recognized identifier).
     - `"PHI cannot be sent to this model"` → `pii-execution-stage`, `azure-openai-control-toggle` + `anthropic-control-toggle` + `gemini-control-toggle` (HIGH — the blocked provider is the primary suspect if no provider name is present).
   - **Provider or feature name appears as a substring inside a model/identifier string, including as a prefix, a path segment, or after a namespace delimiter.** Examples:
     - `anthropic.claude-sonnet-4-5-20250929-v1:0` → `anthropic-control-toggle` (HIGH — the string literally starts with `anthropic.`)
     - `bedrock/anthropic/claude-3-opus` → `anthropic-control-toggle` (HIGH — contained verbatim)
     - `openai:gpt-4o-2024-11-20` → `azure-openai-control-toggle` (HIGH — `openai` is a substring)
     - `google/gemini-pro` → `gemini-control-toggle` (HIGH)
   - Match rule: do a case-insensitive substring check of each provider token (`anthropic`, `openai`, `gemini`, `bedrock`, `aws`, `azure`) against the full error text. A match promotes the corresponding `*-control-toggle` finding from MEDIUM to HIGH.

2. **MEDIUM** — requires product knowledge (one step of inference beyond a direct substring):
   - Model family name → provider, where the provider name is NOT a substring of the error. E.g., `"claude-3"` by itself (no `anthropic.` prefix) → Anthropic.
   - Concept → property family (`"log retention"` → `traces-ttl*`)
   - HTTP status + generic phrase → probable property family

3. **LOW** — property is `false` / restrictive but has no textual connection. Only include if user asked "show everything blocking."

4. **Tie-breaker** — within a tier, prefer findings from the product the error most clearly references.

**Presentation — HIGH first, always explain reasoning. Use [property-labels.md](../../property-labels.md) to render human labels alongside technical keys:**

```
Diagnosis — policy "iso-42001-ai-trust-layer" (AITrustLayer, tenant-level):

MOST LIKELY (1 finding):
  Europe (allowed-llm-regions.europe): Off
    ← Error says "in EU" — direct match on region path

POSSIBLY (1 finding):
  Open AI (azure-openai-control-toggle): Off
    ← gpt-4o-2024-11-20 is an Azure OpenAI model; provider is disabled
    Description: Disabling models will impact genAI features across products

UNLIKELY / UNRELATED (2 findings, hidden by default):
  Anthropic (anthropic-control-toggle): Off    — unrelated to the error
  Gemini   (gemini-control-toggle):    Off    — unrelated to the error
```

Format: `<Label> (<technical-key>): <human-value>`. Look up `<Label>` per the lookup convention in [property-labels.md](../../property-labels.md). For boolean values, render `true → On`, `false → Off`. For enums, look up the value as a label too (e.g., `"DetectionAndMasking"` → `PII Masking`). Include the `-description` line for the top finding when available — gives the user product context without forcing them to recall what the property does.

Only show UNLIKELY if the user asks for it or HIGH + MEDIUM are both empty.

If nothing matches: "I couldn't identify a property causing this error in deployed tenant-level policies. The block may come from a different policy layer (group/user/global) or non-AOPS governance."

### 4b. Run compliance impact — REQUIRED, not optional

> **Critical Rule #9 applies: no diff + approval prompt may be shown without the impact delta rendered inside it.** Even for a single-toggle fix. Users can't judge compliance side-effects without the numbers. If the impact run fails, halt and tell the user — do NOT proceed to Step 5 with an empty impact section.

For each proposed fix targeting a given `(licenseType, productIdentifier)`, invoke the impact primitive before rendering the diff — it needs to show up **inside** the approval prompt. Follow [../../compliance-impact.md](../../compliance-impact.md):

1. Extract all local packs in parallel (once per session — cache for the run).
2. Hydrate the BEFORE cache using `deployed-policy get` calls fanned out per pair.
3. Build the AFTER cache by cloning BEFORE and swapping the target policy's `data` for the patched formData (current formData + approved fixes).
4. Run `node assets/scripts/impact.mjs --target-product <productIdentifier> --json-out <path>`.

Cache the result — Step 5 displays it, Step 7's patch record stores a reference to the `impact.json`.

### 5. Diff preview + approval

By default, propose fixes only for **HIGH** and **MEDIUM** tiers. LOW is informational.

```
Proposed fix for policy "iso-42001-ai-trust-layer":

  [MOST LIKELY] Europe   (allowed-llm-regions.europe):    Off → On
  [POSSIBLY]    Open AI  (azure-openai-control-toggle):   Off → On

All other fields remain unchanged (78 fields).

Compliance impact:
  ISO 42001 (v1.0.0)       6/21 →  8/21  (+2)
     ✓ improves:   A.5 — Region governance for LLM traffic
     ✓ improves:   A.8 — Approved model providers
  SOC 2 Type 2 (v1.0.3)    9/17 →  9/17  (±0) unchanged
  ISO 27001 (v2.0.1)      (unaffected)

Apply this fix? (y / partial / n)
```

#### Prompt text — pick the exact string by impact outcome

Agents copy the prompt verbatim to the user, so the recipe and the rendered prompt must agree. Use one of these three literal strings:

| Impact outcome | Prompt to render (verbatim) | Approval token(s) |
|---|---|---|
| Pure improvement, unchanged, or non-mandatory regression | `Apply this fix? (y / partial / n)` | `y` (or `yes`) |
| Mandatory regression — default flips to `n` | `⚠ This change REGRESSES mandatory clause(s): <clauseId> — <name>. Type 'yes' in full to proceed (y is not sufficient) / partial / n` | `yes` only — reject a bare `y` and re-prompt |

Never render `(y / partial / n)` and then internally require `yes` — that's the bug. If the impact has a mandatory regression, render the second prompt. Otherwise render the first.

Three user options:
- `y` (or `yes`) — apply all proposed changes
- `partial` / `"just fix the region"` — apply a subset (user specifies)
- `n` — no changes

> **Tip surface when both tiers have findings:** "MOST LIKELY alone often unblocks. Say `just apply MOST LIKELY` for the minimal fix — you can re-run diagnosis if the error persists."

Wait for explicit approval. No side effects before then.

#### Partial selection loops back to Step 4b — required

If the user picks `partial` (or names specific changes to apply), the delta they just saw no longer reflects what's about to happen. **Re-run the impact primitive** with a narrowed AFTER cache containing only the selected change(s), re-display the new `Compliance impact:` block, and re-render the approval prompt. The yes-gate rule applies to the **narrowed** impact — if the partial selection still regresses a mandatory clause, the `Type 'yes' in full` prompt is what you show.

Pseudocode:

```
while True:
    impact = runImpact(targetProduct, proposedFormData)
    renderDiff(selectedChanges, impact)
    prompt = impact.totals.mandatoryRegressions > 0
             ? "⚠ ... Type 'yes' in full to proceed ..."
             : "Apply this fix? (y / partial / n)"
    answer = ask(prompt)
    if answer == "partial":
        selectedChanges = askWhichChanges()
        proposedFormData = liveFormData + selectedChanges
        continue       # back to runImpact with narrowed after-state
    break
```

Do NOT apply changes using a stale impact block. A partial fix that looks "+2 compliant, no regressions" in the full-proposal delta can easily be "0 net, 1 regression" once narrowed.

### 6. Apply the fix

Use the UPDATE recipe in [../../policy-crud.md](../../policy-crud.md#update-recipe):

1. Current formData is already cached (Step 3).
2. Apply approved changes onto the formData object.
3. Call `uip gov aops-policy update` with the patched formData.

Record both the approved changes AND any HIGH/MEDIUM findings the user declined — the patch record schema has a `notProposedOrDeclined[]` slot for this so future auditors see what was offered but rejected.

### 7. Write patch record

Write to `$HOME/uipath-governance/audit/patch-records/patch-record-<policyName>-<timestamp>.json`. See [patch-record.md](patch-record.md) for the schema, including `notProposedOrDeclined[]` (required on partial/declined approvals) and `priorAttempts[]` (required on retry chains). Each applied change carries its confidence tier and reasoning.

### 8. Report

Pick the variant by approval path:

#### 8a. Full-fix variant — user accepted all proposed changes (`y` / `yes`)

```
✓ Policy "iso-42001-ai-trust-layer" updated successfully.

Changes applied:
  [MOST LIKELY] Europe   (allowed-llm-regions.europe):   Off → On
  [POSSIBLY]    Open AI  (azure-openai-control-toggle):  Off → On

Compliance impact (realized): SOC 2 +0, ISO 42001 +2, ISO 27001 (unaffected)
Patch record: <path per patch-record.md>

The agent should now be able to use gpt-4o-2024-11-20 in EU.
If the error persists, check group-level or user-level policy overrides.
```

#### 8b. Partial-fix variant — user picked a subset

REQUIRED when approval path was `partial` or the user named specific changes. The report MUST include a `Residual / next steps:` block so the user knows:
1. whether the original error signal is now **fully addressed, partially addressed, or unaddressed**,
2. which other HIGH/MEDIUM findings remain untouched, and
3. a concrete next command they can run.

```
✓ Policy "soc2-type2-mandatory-AITrustLayer" updated successfully (partial fix).

Changes applied:
  [POSSIBLY]    Anthropic (anthropic-control-toggle):   Off → On

Compliance impact (realized): SOC 2 +1, ISO 42001 (unchanged), ISO 27001 (unaffected)
Patch record: <path per patch-record.md>

Residual / next steps:
  Original error partially addressed: provider is now enabled, but the 'in EU' block remains.
  Untouched findings:
    [MOST LIKELY] Europe (allowed-llm-regions.europe):  Off — NOT applied (declined)
  Suggested next command: re-run with "enable Europe region on this policy" or
                          say "apply MOST LIKELY" if you meant to include it.
```

The `notProposedOrDeclined[]` array in the patch record and the `Untouched findings:` block in the report must list the same items — they are two renderings of the same audit data.

#### 8c. Failed-update variant — update returned 4xx/5xx

Same header as 8a but `status: failed` and include the CLI `Message` / `Instructions` verbatim. If the failure was a retryable 5xx (template upgrade in progress, connection timeout), tell the user what to retry and when — see the UPDATE recipe error map in [../../policy-crud.md](../../policy-crud.md#update-recipe).

## Error map

| Situation | Action |
|---|---|
| `tenant get` fails (403/404) | Halt. Verify `UIPATH_TENANT_ID` in `~/.uipath/.auth`. |
| `policy get` fails for one policy | Skip that policy with a warning. Continue with others. |
| `update` returns 400 | Halt. Surface error — likely schema mismatch. |
| `update` returns 401/403 | Halt. User may lack update permission. |
| `update` returns 409 | Halt. Concurrent modification. Ask user to retry. |
| No deployed policies found | Tell user. Suggest checking org-level / global policies. |
| Error signal too vague | Ask user for the full error message. |

## Anti-Patterns

- **Never present the fix diff without the `Compliance impact:` block above the `Proceed?` prompt.** Critical Rule #9. The user needs to know whether unblocking one agent regresses a standard they're held to — "this change improves ISO 42001 +2 but regresses SOC 2 CC6.1" is information that only the impact walker can produce. Skipping this is forbidden even when the fix is a single toggle.
- **Never auto-apply LOW-confidence findings.** They are informational only.
- **Never rank findings without the HIGH / MEDIUM / LOW tiers.** Flat lists mislead the user about where to look first.
- **Never propose a fix without showing current formData context.** The user needs to see what they're changing away from, not just what they're changing to.
