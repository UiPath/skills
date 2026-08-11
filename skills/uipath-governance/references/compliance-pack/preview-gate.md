# Compliance Standards — Preview Gate & Disclaimer

Compliance Standards (ISO 42001 and any future standard) is a **preview feature**, available only to
organizations enrolled in the UiPath preview program. This applies to **every** compliance-pack flow —
catalog, coverage, full-apply, partial-apply, disable, query, state list, diagnose. This file is the
single source of truth for both behaviors below; other plugins link here rather than restating them.

## 1. Preview disclaimer (on success)

Append this disclaimer as a footer to **user-facing display output** for any compliance-standard
response — chat replies, the posture plan (`posture_plan.txt`), catalog/query answers, apply/disable
receipts, and standard-list output:

```
ⓘ Compliance Standards is a preview feature, available to organizations enrolled in the UiPath
  preview program. Capabilities and behavior may change before general availability.
```

- Include it **once per response**, as a footer under the actual result — not after every table.
- **Do NOT** write it into internal session/JSON files the flow persists for the checker or itself
  (`coverage.json`, `report.json`, catalog cache). Those hold raw API data only. The disclaimer is
  display text, not data.

## 2. 403 → preview not enabled (stop the flow)

If **any** `uip gov compliance-packs …` call (`catalog get`, `state coverage|get|list|enable|disable`)
returns **HTTP 403 / Forbidden**, the organization is not enrolled in the preview. **Stop immediately:**
do not retry, and run no further compliance commands. Present exactly this, then end the flow:

```
Compliance Standards isn't enabled for your organization yet.

It's currently a preview feature, and access requires enrolling in the UiPath preview program.
To request access, contact your UiPath account team or organization administrator, then re-run
this request.
```

### 403 is NOT 401

A **403 (Forbidden)** means authenticated-but-not-entitled → the preview gate above.
A **401 (Unauthorized)** means not logged in → a normal auth failure; handle it per the flow's usual
auth handling (`uip login`), NOT with the preview message. Never conflate the two — do not tell a
logged-out user to "enroll in preview," and do not tell an unenrolled user to "log in again."
