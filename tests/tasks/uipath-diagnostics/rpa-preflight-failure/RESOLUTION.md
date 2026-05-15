# Final Resolution

---

**Root Cause:** Two missing infrastructure dependencies — asset 'PO_PricingTable' and Microsoft Outlook 365 Integration Service connection — caused a preflight check failure in the PurchaseOrderProcessing workflow.

**What went wrong:** The PurchaseOrderProcessing job (run 2026-05-04T12:09:55Z) faulted immediately after startup because its preflight check detected two missing dependencies and threw an unhandled "Preflight Failure" exception.

**Why:** The workflow's Main.xaml performs a preflight check before processing. During that check, two activities failed in sequence: first, the Get Asset activity ("ReadPricingAsset") could not find asset 'PO_PricingTable' in the PurchaseOrderProcessing folder — Orchestrator returned HTTP 404 / error code 1002, confirming the asset does not exist there. Second, the "Get PO Emails from Outlook 365" activity (ReadPOEmail) attempted to use Microsoft Outlook 365 connection ID `7d15b17a-da96-4759-85ba-f24aacbfb04b`, which does not exist anywhere in the tenant — it was either deleted after the process was published or was created in a personal workspace that is no longer accessible. Both failures set a "preflight failed" flag, and the subsequent "Check Preflight" If-block threw a "Preflight Failure" exception that terminated the job with a Faulted state. Neither failure is recoverable at runtime — both require infrastructure fixes before the job can run.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PurchaseOrderProcessing — Faulted at 2026-05-04T12:09:57.720Z (ran for 2.67 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-HOST
- Folder: PurchaseOrderProcessing
- Final error: `Throw "Throw Preflight Failure"` → `If "Check Preflight"` → Main.xaml
- Log timestamp of the thrown exception: 2026-05-04T12:09:57.870Z

### System Activities (Root Cause)
- Activity: Get Asset ("ReadPricingAsset")
- Asset name referenced: **PO_PricingTable**
- Error at 2026-05-04T12:09:57.853Z: `[ReadPricingAsset] Status code: 404 (Not Found). Orchestrator response: Could not find the asset 'PO_PricingTable'. Error code: 1002`
- Asset does not exist in the PurchaseOrderProcessing folder — confirmed by Orchestrator's own 404 / error code 1002

### Integration Service (Root Cause)
- Activity: Get PO Emails from Outlook 365 ("ReadPOEmail")
- Connector: Microsoft Outlook 365 (`uipath-microsoft-outlook365`)
- Connection ID: `7d15b17a-da96-4759-85ba-f24aacbfb04b`
- Error at 2026-05-04T12:09:57.266Z: `[ReadPOEmail] Connection [7d15b17a-da96-4759-85ba-f24aacbfb04b] is invalid or you do not have access to it`
- Verification: CLI queries returned empty for both folder-scoped and tenant-wide lookups — connection does not exist anywhere in the tenant

---

**Immediate fix:**

### System Activities (Root Cause)
1. Create asset `PO_PricingTable` in the PurchaseOrderProcessing folder in Orchestrator.
   - **Why:** The Get Asset activity requires an asset named exactly `PO_PricingTable` in that folder.
   - **Where:** Orchestrator UI → PurchaseOrderProcessing folder → Assets → Add Asset. Set name to `PO_PricingTable` (exact spelling), choose correct type (Text, Integer, Boolean, or Credential), and enter the value. Alternatively, if the asset was moved, update the AssetName property in the workflow or run the job in the folder where it's defined.
   - **Who:** RPA developer or admin
   - **Source:** `system-activities/playbooks/get-asset-not-found.md`

### Integration Service (Root Cause)
1. Create a new **Microsoft Outlook 365** connection in the PurchaseOrderProcessing folder.
   - **Why:** Connection `7d15b17a-da96-4759-85ba-f24aacbfb04b` does not exist anywhere in the tenant. ReadPOEmail cannot run without a valid connection accessible from the PurchaseOrderProcessing folder.
   - **Where:** Orchestrator UI → Integration Service → Connections → Add Connection → select **Microsoft Outlook 365** → assign to PurchaseOrderProcessing folder → authenticate. Or via CLI: `uip is connections create uipath-microsoft-outlook365 --folder-key 7f984a6b-1138-40fb-b48e-2c3ddf02b8f0`. After creating and authenticating, update the "Get PO Emails from Outlook 365" activity to reference the new connection ID and republish the process.
   - **Who:** RPA developer or admin
   - **Source:** `integration-service/playbooks/connection-invalid.md`

---

**Preventive fix:**

1. **Orchestrator** — Configure an alert subscription for faulted jobs in the PurchaseOrderProcessing folder.
   - **Why:** Both infrastructure dependencies were missing with no early warning. Orchestrator alerts can notify on job faults as soon as they occur.
   - **Where:** Orchestrator UI → Alerts → configure subscription with severity "Error" and component filter for PurchaseOrderProcessing folder jobs.
   - **Who:** Admin or platform team
   - **Source:** https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

2. **System Activities** — Wrap ReadPricingAsset in a Try/Catch block in Main.xaml.
   - **Why:** If the preflight check is ever removed or bypassed, the 404 would propagate as an unhandled exception. A Try/Catch allows clean termination with a descriptive error.
   - **Where:** Main.xaml → wrap the ReadPricingAsset Get Asset activity in Try/Catch → catch `UiPath.Core.Activities.OrchestratorCommunicationException` and throw a meaningful application exception.
   - **Who:** RPA developer

3. **Integration Service** — Create the Microsoft Outlook 365 connection in a shared folder rather than a personal workspace.
   - **Why:** The connection was absent tenant-wide — consistent with having been created in a personal workspace that was removed. Shared folder connections persist independently of individual users.
   - **Where:** Integration Service → create connection under the PurchaseOrderProcessing shared folder; ensure the robot account has at least `Connections.View` permission.
   - **Who:** Admin or platform team
   - **Source:** `integration-service/playbooks/connection-invalid.md`

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Asset 'PO_PricingTable' missing from PurchaseOrderProcessing folder | High | Confirmed | Yes | HTTP 404 / error code 1002 from Orchestrator at 12:09:57.853Z | Create asset in Orchestrator with correct type/value |
| H2 | Outlook 365 connection `7d15b17a...` absent tenant-wide | High | Confirmed | Yes | CLI returned empty for both folder and tenant-wide lookups | Create new Outlook 365 connection, update workflow, republish |

---

Would you like help implementing either fix — creating the `PO_PricingTable` asset or setting up the new Outlook 365 connection? I can also clean up the `.local/investigations/` folder if you no longer need it.
