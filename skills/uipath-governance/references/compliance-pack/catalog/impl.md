# Catalog — Pack Discovery and Detail

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

## Discover available packs

```bash
uip gov compliance-packs catalog list --output json
```

Parse `Data.Packs[]` (PascalCase, like every other compliance-packs response). Each entry has:
`PackId`, `PackName`, `PackLongName`, `PackVersion`, `Description`, `Available` (bool), `PublishedAt`, `Summary`.

**`Available` decides whether a pack can be used at all.** The catalog lists standards that are announced but not yet shipped — they come back `Available: false` with `PublishedAt: null` and `Summary: null`. Running `catalog get` or any `state` command on one fails; there is no bundle behind it.

Treat it as a three-state field, because the response shape varies by service version:

| `Available` | Treat as | Why |
|---|---|---|
| `true` | Usable | Shipped, has a bundle. |
| `false` | Not usable | Announced only. Never offer to apply, check, or query it. |
| **absent** | Usable | Older services omit the field entirely. Requiring `Available == true` would reject every pack and break the whole flow. Only an explicit `false` blocks. |

- Present usable packs with `PackName`, `PackVersion`, and `Summary.ClauseCount` / `Summary.ControlCount` / `Summary.DeploymentPolicyCount`. When `Summary` is null, omit the counts rather than printing zeros.
- Mention `Available: false` entries, if at all, only as "announced, not yet available".

## Get full pack detail

```bash
# Create a unique session dir and persist the path to disk so it survives between tool calls.
# Every downstream plugin reads this file to find the shared session dir.
SESSION_TEMP=$(mktemp -d)
echo "$SESSION_TEMP" > "$HOME/.uipath-compliance-current-session"
uip gov compliance-packs catalog get <packId> --output json > "$SESSION_TEMP/catalog.json"
```

```powershell
# Windows PowerShell — env vars don't persist between tool calls; write the path to a file instead.
$tmpDir = Join-Path $env:TEMP ('compliance-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Force $tmpDir | Out-Null
$tmpDir | Set-Content "$env:TEMP\uipath-compliance-current-session.txt" -NoNewline
uip gov compliance-packs catalog get <packId> --output json | Set-Content "$tmpDir\catalog.json"
```

Save to `$SESSION_TEMP/catalog.json` (Bash) or `$tmpDir\catalog.json` (Windows). This file feeds all downstream plugins. Always run this step **before** `state coverage`, `partial-apply`, or `query` — those plugins resolve the session dir from the sentinel file.

Key fields in `Data`:

CLI output is **PascalCase**. Field names below are exactly as returned by `catalog get`.

| Field | Used by |
|---|---|
| `Data.PackId` | All state commands |
| `Data.DeploymentPolicies[].ProductIdentifier` | Coverage + apply: which products are covered |
| `Data.DeploymentPolicies[].ProductDisplayName` | User-facing product name |
| `Data.Clauses[].ClauseId` | Partial apply: clause filtering |
| `Data.Clauses[].ClauseName` | User-facing clause name |
| `Data.Clauses[].EditorialPolicies[].ProductIdentifier` | Maps clause to product |
| `Data.Clauses[].EditorialPolicies[].Controls[].DisplayName` | NLP matching + query display |
| `Data.Clauses[].EditorialPolicies[].Controls[].Impact` | `"High"` / `"Medium"` / `"Low"` |
| `Data.Clauses[].EditorialPolicies[].Controls[].RecommendedSetting` | What value will be configured |
| `Data.Clauses[].EditorialPolicies[].Controls[].ConfigLocation` | Where to find it in the UI |
| `Data.Clauses[].EditorialPolicies[].Contributions[].Key` | formData property key (dotted path) |
| `Data.Clauses[].EditorialPolicies[].Contributions[].Required` | Operator → synthesize-formdata.mjs |

## List currently configured standards

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state list tenant $TENANT_ID --output json
```

Parse `Data[]` — each entry has `packId`, `packVersion`, `active` (bool), `lastToggledAt`.

**Multiple standards can be active on one tenant simultaneously.** Enabling a second standard adds to the first, it does not replace it — so this array can legitimately hold several `active: true` entries, and every pack-scoped operation (coverage, disable, restore) applies to the one standard it names and leaves the others alone.

`state list` does NOT return a display name. Get `<packName>` by joining each `packId` to `catalog list` → `Data.Packs[].PackName`; run `catalog list` first if it has not been fetched this session. If the join finds no match (pack configured but no longer in the catalog), print the `packId` alone and say so — never invent a display name.

Present active packs to the user:

```
Compliance standards configured on <tenantName>:

  <packName> (<packId> v<packVersion>) — Active since <lastToggledAt>
  [repeat per active entry]

No other compliance standards are currently active.
```

If the array is empty: "No compliance standards are currently configured on this tenant."

## Pack ID lookup

**Resolve every standard name against `catalog list` — never hardcode a packId.** Match the user's wording case-insensitively against `Data.Packs[].PackName` and `PackLongName`, ignoring `ISO`/`IEC`/`ISO/IEC` prefixes and punctuation, so "27001", "ISO 27001" and "ISO/IEC 27001:2022" all hit the same entry.

**Then check `Available` before doing anything with the match.** A name resolving to a packId is NOT the same as that pack being usable — announced-but-unshipped standards are in the catalog with `Available: false`. Resolving one and passing it to `catalog get` or `state enable` produces a failure the user cannot act on. Check `Available` first, every time.

`PackLongName` is not reliably descriptive (ISO 27001's is literally "ISO 27001 compliance pack"), so common domain phrasings will NOT be found by name-matching alone. The alias table below carries them; it is a supplement to the catalog match, not a replacement for it.

| User says | Resolution |
|---|---|
| "ISO 42001" / "ISO/IEC 42001" / "AI Management System" | `iso-42001-2023` |
| "ISO 27001" / "ISO/IEC 27001" / "Information Security Management System" / "ISMS" | `iso-27001-2022` |
| A name matching a pack with an explicit `Available: false` (on cloud today: GDPR, HIPAA, SOC 2, EU AI Act — the set differs by environment, so read it from the response, never from this list) | Say that standard is announced but not yet available, name the ones that are, and stop. Do NOT run `catalog get` or any `state` command on it. |
| A standard name with no match at all | Tell the user that standard is not available, list the `Available: true` packs, and offer to proceed with one. |
| No standard named at all (e.g. "check my compliance posture") | Run `catalog list` and ask which standard. Never assume — more than one pack is available. |
| Two or more `Available: true` packs match the wording | Ask which one, listing the matches by `PackName`. |
