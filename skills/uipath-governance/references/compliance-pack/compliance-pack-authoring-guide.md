# Custom Compliance Pack Authoring

Turn a compliance PDF into a deployable pack via a three-step server-side LLM pipeline. Each step returns a `sessionId` used by the next.

> **Sessions expire.** Complete `analyze → review → bundle` in one sitting. Do not pause between steps.

---

## When to use this flow

When the user wants to:
- Create a pack from their own compliance document (internal policy, custom standard, customer contract)
- Package non-prebuilt compliance requirements as a deployable UiPath governance pack

For prebuilt packs (ISO 42001, HIPAA, SOC 2, ISO 27001) — use `enable` directly from [`compliance-pack-commands.md`](./compliance-pack-commands.md).

---

## Step 1 — Analyze

Upload the compliance document. The server extracts text and detects clauses via LLM.

```bash
uip gov compliance-pack analyze \
  --file <PATH_TO_DOC> \
  [--description "<SHORT_DESCRIPTION>"] \
  --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--file <PATH>` | yes | Path to the compliance document (PDF or binary) |
| `--description <TEXT>` | no | Short description for the pack (shown in `list` output) |

**Output:**

```json
{
  "sessionId": "sess-abc123",
  "totalClauses": 44,
  "clauses": [
    {
      "clauseId": "uuid",
      "documentRef": "4.1",
      "clauseName": "Risk Assessment",
      "textPreview": "First 200 chars of clause text...",
      "pageStart": 3
    }
  ]
}
```

**Present to user:** `totalClauses` count. Ask if the extraction looks complete before proceeding to review.

---

## Step 2 — Review

Map extracted clauses to UiPath product controls, generate AOps policy definitions and Rego rules. Results are cached — re-running with the same clauses and products returns `cached: true`.

```bash
uip gov compliance-pack review <SESSION_ID> --output json
```

**Output:**

```json
{
  "sessionId": "sess-abc123",
  "cached": false,
  "supportedClauses": 28,
  "unsupportedClauses": 16,
  "productsConfigured": ["AITrustLayer", "Development"],
  "clauseSummary": [
    {
      "documentRef": "4.1",
      "clauseName": "Risk Assessment",
      "policyKind": "CustomPolicy",
      "products": ["AITrustLayer"],
      "controlCount": 3
    }
  ]
}
```

**Present to user:**
- `supportedClauses` / total — how many clauses mapped to UiPath controls
- `unsupportedClauses` — clauses that could not be mapped; these will be excluded from the pack
- `productsConfigured` — product surfaces covered

Ask for confirmation before bundling if `unsupportedClauses > 0` — clarify which requirements will be omitted.

---

## Step 3 — Bundle

Assemble the reviewed output into a compliance pack and save it. Returns the new `packId`.

```bash
uip gov compliance-pack bundle <SESSION_ID> --output json
```

**Output:**

```json
{
  "packId": "my-compliance-pack-1-0-0",
  "clauseCount": 28,
  "unsupportedCount": 16,
  "regoCount": 4
}
```

After bundle succeeds:
1. Show the `packId`, `clauseCount`, and `regoCount`.
2. Offer to enable immediately:

```bash
uip gov compliance-pack enable <PACK_ID> --output json
```

Run `enable` only after explicit confirmation. After enabling, confirm the pack is active with `list`.

---

## Full flow example

```bash
# Step 1: analyze
uip gov compliance-pack analyze \
  --file ~/Downloads/my-compliance-doc.pdf \
  --description "Internal AI Governance Policy v2" \
  --output json

# Step 2: review (use sessionId from step 1)
uip gov compliance-pack review sess-abc123 --output json

# Step 3: bundle (use sessionId from step 2)
uip gov compliance-pack bundle sess-abc123 --output json

# Enable the new pack (use packId from step 3)
uip gov compliance-pack enable 3f2504e0-... --output json
```

---

## Error handling

| Error | Action |
|-------|--------|
| `analyze` fails | Check that the file path is correct and the file is a valid PDF. Retry. |
| `review` → 0 `supportedClauses` | The document may not contain recognisable policy language. Ask the user to verify the document or provide a description. |
| `bundle` fails | Session may have expired. Restart from `analyze`. |
| `enable` → 4xx | Halt. Report error verbatim. Do NOT retry automatically. |
