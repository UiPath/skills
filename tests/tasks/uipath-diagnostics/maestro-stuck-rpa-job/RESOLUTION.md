# Final Resolution

Root Cause: UI selector mismatch in the child automation caused a cascading failure that left the Maestro BPMN instance permanently stuck.

What went wrong: The "Agentic Process" Maestro job has been stuck in Running state since September 23, 2025 (over 6 months) because a child automation faulted on a selector error and the BPMN process had no error handling to recover from it.

Why: The child job launched by the "BlankProcess6" service task failed with a `NodeNotFoundException` because the Click 'Collaboration' activity's strict selector contained `aaname='set'` instead of the correct `aaname='Collaboration'`. The selector was hardcoded with the wrong attribute value -- 'set' bears no resemblance to 'Collaboration', indicating a recording error during development. Healing Agent was not enabled on the process, so no automated recovery was attempted. When the child job faulted, the Maestro BPMN engine raised incident 170002 ("Failure in the Orchestrator Job") on the service task. Because the BPMN process definition contains no boundary error event on the service task -- the process is a simple linear flow (Start -> BlankProcess6 -> End) with zero error-handling elements -- the engine could not route the failure to any recovery path. The incident remains Open with no manual intervention (`userUpdated=null`), which keeps the execution cursor permanently stuck on the service task. Since the Maestro instance never completes, the parent Orchestrator ProcessOrchestration job remains in Running state indefinitely (it is serverless with no robot host, so heartbeat-based timeouts do not apply).

Evidence:

### UI Automation (Root Cause)
- **Exception:** `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` -- "Could not find the user-interface (UI) element for this action"
- **Failed activity:** Click 'Collaboration' at `Main.xaml > Main Sequence > NApplicationCard 'Edge My Apps' > Sequence 'Do' > NClick 'Click Collaboration'`
- **Selector used:** `<webctrl id='drawerHeader_0' tag='DIV' aaname='set' />` (strict mode)
- **Expected match:** The element with `id='drawerHeader_0'` actually has `aaname='Collaboration'`, not `aaname='set'`
- **Healing Agent:** Not enabled -- no healing artifacts found

### Maestro (Propagation)
- **Instance:** Agentic Process-42792329 (`0fbda085-5c96-4dab-a4b3-012c1914845a`)
- **Incident:** 170002 -- "Failure in the Orchestrator Job" (Open since 2025-09-23T09:47:17Z, no updates)
- **Faulted element:** "BlankProcess6" service task (`Activity_EW6HNH`) -- failed at 09:47:16Z
- **BPMN structure:** 3 elements only (Start -> ServiceTask -> End), zero boundary error events

### Orchestrator (Propagation)
- **Job:** Running since 2025-09-23T09:45:59Z -- no state transitions in over 6 months
- **Runtime type:** ProcessOrchestration (serverless)
- **Folder:** Solution 5 (personal workspace)

---

Immediate fix:

### UI Automation (Root Cause)

1. **Fix the selector** in the Click 'Collaboration' activity
   - Change `aaname='set'` to `aaname='Collaboration'` in `Main.xaml`
   - Who: RPA Developer

2. **Enable Healing Agent** on the process release
   - Where: Orchestrator > Solution 5 > Agentic Process release > Process Settings > `AutopilotForRobots: { Enabled: true, HealingEnabled: true }`
   - Who: RPA Developer

3. **Publish the updated package** before retrying

### Maestro (Propagation)

4. **Resolve the open incident** to unblock the instance
   - Where: Maestro Instance Management > Agentic Process-42792329 > Incidents tab > Retry (after fix is published)
   - Who: Process Owner

5. **Add a boundary error event** to the "BlankProcess6" service task
   - Where: Studio Web > Process.bpmn > attach Boundary Error Event to the service task
   - Who: RPA Developer

### Orchestrator (Propagation)

6. **No separate action needed** -- the job will complete once the Maestro instance finishes. If unrecoverable, cancel the job via Orchestrator > Solution 5 > Jobs > Kill/Cancel.

---

Preventive fix:

1. **UI Automation** -- Enable Healing Agent on all production processes with UI interactions
2. **Maestro** -- Add boundary error events to all service tasks in BPMN processes
3. **UI Automation** -- Validate selectors after application updates before deploying

---

Investigation Summary:

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence |
|---|---|---|---|---|---|
| H1 | Instance stuck due to unresolved incident 170002, no boundary error event | High | Confirmed (symptom) | No | BPMN XML has zero boundary events; incident Open 6+ months |
| H2 | Child job faulted: selector `aaname='set'` vs actual `aaname='Collaboration'` | High | **Confirmed** | **Yes** | NodeNotFoundException, 71% match, no healing |
| H3 | Healing Agent may have captured a fix | High | Eliminated | No | No healing artifacts exist |

---

Would you like help implementing any of the fixes, or should I clean up the `.investigation/` directory?
