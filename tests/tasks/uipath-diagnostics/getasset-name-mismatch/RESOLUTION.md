# Final Resolution

---

**Root Cause:** The `Get Credential` activity in `Main.xaml` references
`AssetName="myHiddenAset"` (typo — missing an "s"). The intended asset
in the `Remote Debugging` folder is named `myHiddenAsset`. Orchestrator
matches asset names exactly, so the lookup returned HTTP 404 / error
code 1002 and the job faulted.

**What went wrong:** The `GetAssetFailure` job (started
2026-05-10T14:32:11Z) faulted ~2 seconds after launch because the
`Get Credential` activity (`GetRobotCredential`) in `Main.xaml` could
not find an asset named `myHiddenAset` in its target folder.

**Why:** The workflow's `GetRobotCredential` activity sets
`AssetName="myHiddenAset"` and `FolderPath="Remote Debugging"`. When
the activity called Orchestrator, the response was HTTP 404 with the
message `"Could not find the asset 'myHiddenAset'. Error code: 1002"`.
Listing assets in the `Remote Debugging` folder shows an asset named
`myHiddenAsset` (Credential type, scope Global) — exactly one character
away from the value in the XAML. The misspelled name has no match;
Orchestrator does not fall back to fuzzy matching.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: GetAssetFailure — Faulted at 2026-05-10T14:32:13.420Z (ran for ~2.3 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: Remote Debugging (key `5a8b9c2d-1e3f-4a6b-8c9d-0e1f2a3b4c5d`)
- Final error: `Could not find the asset 'myHiddenAset'. Error code: 1002` → `Main.xaml` → `GetRobotCredential "Get Credential"` → `Sequence "Main Sequence"`

### System Activities (Root Cause)
- Activity: `GetRobotCredential` (DisplayName: "Get Credential")
- AssetName referenced (from `Main.xaml`): **`myHiddenAset`** (typo)
- FolderPath: `Remote Debugging`
- Error at 2026-05-10T14:32:13.371Z: `[Get Credential] Status code: 404 (Not Found). Orchestrator response: Could not find the asset 'myHiddenAset'. Error code: 1002`
- Asset list in `Remote Debugging` returned `myHiddenAsset` (Credential, Global scope) — NOT `myHiddenAset`. Exact-match lookup returned 404 because of the missing "s".

---

**Immediate fix:**

### System Activities (Root Cause)
1. Correct the typo in `Main.xaml`.
   - **Why:** The activity's `AssetName` must match the Orchestrator asset name exactly. `myHiddenAset` has no match; `myHiddenAsset` exists.
   - **Where:** `Main.xaml` → `<ui:GetRobotCredential ... AssetName="myHiddenAset" ...>` → change to `AssetName="myHiddenAsset"`. Save, rebuild, republish the process.
   - **Who:** RPA developer
   - **Source:** `system-activities/playbooks/get-asset-not-found.md` ("If the name does not match" branch)

Alternative: rename the Orchestrator asset from `myHiddenAsset` to `myHiddenAset` (Orchestrator UI → Remote Debugging folder → Assets → rename). Only do this if the typo'd name is the intentional convention.

---

**Preventive fix:**

1. **Studio** — Bind `AssetName` to a project constant rather than a string literal.
   - **Why:** A typo in a string literal is silent at design time. A constant centralizes the name and surfaces a compile-time error if the wrong constant is referenced.
   - **Where:** Define `MyHiddenAssetName = "myHiddenAsset"` as a project constant, then reference that constant from every Get Credential / Get Asset activity that needs it.
   - **Who:** RPA developer

2. **Orchestrator** — Configure an alert subscription for faulted jobs in the `Remote Debugging` folder so missing-asset failures surface immediately.
   - **Why:** The typo would have been caught the first time the job ran if alerts were configured.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + folder filter for `Remote Debugging`.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `AssetName` in workflow is misspelled (`myHiddenAset`); intended asset is `myHiddenAsset` | High | Confirmed | Yes | HTTP 404 / error code 1002 + exact-spelling near-miss in asset list | Fix `AssetName` in `Main.xaml`, rebuild, republish |

---

Would you like help applying the fix — updating `Main.xaml` to reference `myHiddenAsset` and republishing the package? I can also clean up the `.local/investigations/` folder if you no longer need it.
