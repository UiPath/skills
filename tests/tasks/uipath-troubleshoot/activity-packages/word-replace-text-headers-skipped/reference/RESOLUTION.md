# Final Resolution

---

**Root Cause:** The project pins an **older `UiPath.Word.Activities`
([1.6.0])** that scans only the **primary body text**. The `Replace Text`
activity replaced `[CompanyName]` in the body but never touched the same
placeholder in the document's **header/footer**, because header/footer story
ranges are outside the version's scanned range. The job completes
**Successfully** (the body replacement worked, so no error), leaving the
header placeholder intact.

**What went wrong:** The `BrandedLetterFill` job (2026-06-15T09:22) ran green
(State=Successful, no error logs). The trace shows
`[Replace Text] Executed. Replaced 1 occurrence(s) of '[CompanyName]' in the
document body.` — body only. The header copy of the placeholder was never
visited.

**Why:** A Word document stores headers, footers, and floating text boxes in
separate story ranges from the main body. Older `UiPath.Word.Activities`
builds only iterate the body range, so placeholders in those other ranges
are silently skipped. Current versions natively replace inside headers,
footers, and text shapes. This is a package-version limitation, not a
template or Search-value defect — the body match proves the Search string
and template are correct.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: BrandedLetterFill -- **Successful** at 2026-06-15T09:22:07Z; no faulted jobs in the folder; `or jobs logs --level Error` is empty
- Folder: Branded Docs (key `b2c3d4e5-f6a7-4193-8809-3c4d5e6f7081`), machine MOCK-ROBOT-08
- Trace: `Replaced 1 occurrence(s) of '[CompanyName]' in the document body` — the replacement was scoped to the body.

### Project source (Root Cause)
- `Main.xaml`: `Replace Text` (`WordReplaceText`) searches `[CompanyName]` — the same token that survives in the header.
- `project.json` pins `"UiPath.Word.Activities": "[1.6.0]"` — an older version that scans only body text. The body match + header miss + old version pin together identify the cause.

---

**Immediate fix:**

The Search value and template are correct; the package version is the gap.

### Fix path A -- update the package (preferred)
- Open `Manage Packages` in Studio and update `UiPath.Word.Activities` to
  the latest version, rebuild, and re-publish. Newer versions natively
  replace inside headers, footers, and text shapes, so `[CompanyName]` in
  the header will be matched.

### Fix path B -- if the package cannot be upgraded
- Address the header/footer story range explicitly (target the header range
  rather than relying on the body-only scan), or do the substitution in code
  over the document XML, which covers all story ranges.
- **Source:** `word-activities/playbooks/replace-text-headers-textboxes-skipped.md`

> The job being **Successful is misleading** — the body replacement
> succeeded, so no error fires even though the header was skipped. Validate
> the output document's header/footer/text boxes, not just the body or the
> green job state.

---

**Preventive fix:**

1. **Keep `UiPath.Word.Activities` current** when documents have placeholders
   in headers, footers, or text boxes — body-only scanning is a legacy
   limitation removed in newer versions.
   - **Who:** RPA developer.

2. **Assert non-body content** — after the replace, verify the
   header/footer/text-box placeholders are gone so a silent skip becomes a
   visible failure.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An older UiPath.Word.Activities (1.6.0) scans only the body, so the [CompanyName] placeholder in the header/footer is skipped | Medium | Confirmed | Yes | Job Successful + no errors + log "Replaced 1 occurrence in the document body" + body replaced/header not + project.json pins [1.6.0] | Update UiPath.Word.Activities to a version that covers headers/footers/text shapes |

---

Would you like the `UiPath.Word.Activities` version range that adds
header/footer/text-box support, or help addressing the header range in code
if you cannot upgrade?
