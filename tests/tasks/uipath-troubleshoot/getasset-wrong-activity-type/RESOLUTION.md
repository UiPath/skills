# Final Resolution

---

**Root Cause:** The `Get Credential` activity (`GetRobotCredential`)
in `Main.xaml` targets `AssetName="ApiBaseUrl"` in the `Remote
Debugging` folder. The asset exists at that location but its
Orchestrator `ValueType` is `Text`, not `Credential`. The `Get
Credential` activity only works on assets of type `Credential`, so
Orchestrator rejects the runtime call with HTTP 400 / "Activity does
not work with assets of type 'Text'. Invalid asset type." and the
job faults.

**What went wrong:** The `AssetWrongActivityType` job (started
2026-05-13T08:14:33Z) faulted ~1 second after launch because the
`Get Credential` activity called Orchestrator with a `Text` asset
that it cannot read.

**Why:** The workflow's `GetRobotCredential` activity expects to read
a `Credential`-typed asset (which returns a username + SecureString
password). When it sent the request for `ApiBaseUrl`, Orchestrator
inspected the asset's actual type (`Text`) and rejected the call as
incompatible. This is a **design-time bug**: either the developer
chose the wrong activity in Studio (should have used `Get Orchestrator
Asset` for a Text asset), or the asset's type was changed in
Orchestrator after the workflow was published. The asset list in the
`Remote Debugging` folder confirms the mismatch: `ApiBaseUrl` is
present with `ValueType: "Text"`.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AssetWrongActivityType — Faulted at 2026-05-13T08:14:34.512Z (ran for ~1.1 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: Remote Debugging (key `8f6c5d4e-3a2b-4c9d-7e6f-1a2b3c4d5e6f`) — folder exists
- Asset list: `ApiBaseUrl` is present in the folder with `ValueType: "Text"` (NOT `Credential`)

### System Activities (Root Cause)
- Activity (from `Main.xaml`): `GetRobotCredential` (DisplayName: "Get Credential") — expects assets of type `Credential`
- AssetName (from `Main.xaml`): `ApiBaseUrl`
- FolderPath (from `Main.xaml`): `Remote Debugging` (correct — folder exists)
- Asset's actual `ValueType` in Orchestrator: **`Text`**
- Error at 2026-05-13T08:14:34.490Z: `[Get Credential] Status code: 400 (Bad Request). Orchestrator response: Activity does not work with assets of type 'Text'. Invalid asset type.`
- This is NOT asset-not-found (asset present), NOT folder-not-found (folder present), NOT permission-denied (error code is "Invalid asset type", not "not authorized") — the failure is at the **activity-type / asset-type compatibility** layer.

---

**Immediate fix:**

### System Activities (Root Cause) — pick ONE of two branches

1. **Branch A — Fix the workflow (most common):** Replace the `Get Credential` activity with `Get Orchestrator Asset`.
   - **Why:** `Get Orchestrator Asset` (the `GetRobotAsset` activity) works on assets of type `Text`, `Integer`, and `Boolean`. If `ApiBaseUrl` is correctly modeled as a `Text` asset (an API URL is a string value, not a credential), the workflow should be using `Get Orchestrator Asset`.
   - **Where:** `Main.xaml` → replace `<ui:GetRobotCredential ... AssetName="ApiBaseUrl" ...>` with `<ui:GetRobotAsset AssetName="ApiBaseUrl" FolderPath="Remote Debugging" Value="[apiBaseUrl]" />` (declare a `String` variable `apiBaseUrl` and wire downstream consumers to it). Save, rebuild, republish the process.
   - **Who:** RPA developer
   - **Source:** `system-activities/playbooks/get-asset-wrong-activity-type.md` ("Developer selected the wrong activity when building the workflow" branch)

2. **Branch B — Fix the asset type:** If `ApiBaseUrl` is supposed to be a Credential, change its type in Orchestrator.
   - **Why:** If business intent is that `ApiBaseUrl` holds a username + password (e.g. for HTTP basic auth against an API), the asset type should be `Credential`, not `Text`.
   - **Where:** Orchestrator UI → Folder `Remote Debugging` → Assets → `ApiBaseUrl` → Edit. The type field cannot be changed in place; delete the existing Text asset and recreate it as type `Credential` with the correct username + password.
   - **Who:** RPA developer / admin (whoever owns the asset)
   - **Caution:** any other workflow that reads `ApiBaseUrl` as Text will break after the type change — audit all callers first.

---

**Preventive fix:**

1. **Studio** — Run the project's design-time analyzer before publishing.
   - **Why:** Studio's built-in rules include checks for activity-vs-asset type compatibility when an asset is bound at design time. Pre-publish analyzer runs catch this class of error before the job ever runs.
   - **Where:** Studio → Design → Analyze Project. Resolve any `ST-DBP-XXX` (data-binding) findings related to Get Credential / Get Asset before publishing.
   - **Who:** RPA developer

2. **Orchestrator** — Audit asset-type vs activity-type usage as part of pre-publish validation.
   - **Why:** A `Get Credential` activity bound to a Text asset is a recurring mistake when a workflow is copy-pasted from a credential-reading template. Catching it before publish prevents production faults.
   - **Where:** Add a pre-publish step that scans `.xaml` files for `GetRobotCredential` activities and queries `uip orch assets list --folder-key <folder>` to verify each referenced asset's `ValueType` is `Credential`.
   - **Who:** Platform / DevOps

3. **Documentation** — In the project README or internal wiki, document the activity-vs-asset-type matrix:
   - `Get Credential` / `GetRobotCredential` ↔ `Credential` only
   - `Get Orchestrator Asset` / `GetRobotAsset` ↔ `Text`, `Integer`, `Boolean`

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Workflow uses `Get Credential` activity on an asset whose actual type is `Text` (not `Credential`) | High | Confirmed | Yes | Error message "Activity does not work with assets of type 'Text'. Invalid asset type." + asset list shows `ApiBaseUrl` with `ValueType: "Text"` + Main.xaml uses `GetRobotCredential` | Branch A: replace with `Get Orchestrator Asset` in Main.xaml; OR Branch B: change asset type to `Credential` in Orchestrator |

---

Would you like help applying the fix — either editing `Main.xaml` to use `Get Orchestrator Asset` (Branch A) or walking through the Orchestrator asset re-creation flow (Branch B)? I can also clean up the `.local/investigations/` folder if you no longer need it.
