# Sample Access Policy — Starter Reference

Use this canonical sample when the user has **no concrete intent** ("I want to create an access policy", "help me set one up") **or has gaps** (missing resource type, no caller, no actor identity, no name). Show the **Spec narrative** plus the **JSON definition** as a starter so the user can either adopt it as-is or point at the parts they want to change. The sample seeds the **Policy Spec** that Phase 1 ([planning-arch.md](./planning-arch.md)) iterates with the user.

> **When to use this guide.** Phase 1 routes here when the user's request cannot be classified into Resource / Actor Process / Actor Identity / tag phrases — i.e., when intent analysis would otherwise have no defaults to draw from. Do NOT use it when the user has already described a specific policy.

---

## Sample Spec narrative (natural-language description)

> **"Only the 'Order Processing' Maestro can invoke Production Agents"**
>
> This is a **tool-use policy** in **simulation mode** that allows a specific Maestro — "Order Processing" — running on behalf of a specific user to invoke any Agent tagged `Production`.
>
> - **What is being protected:** all Agents that carry the `Production` tag.
> - **Who/what is allowed to call them:** the Maestro named "Order Processing," but only when it is executed by the designated user.
> - **Effect:** `Allow` — the matching call is permitted.
> - **Status:** `Simulated` — the policy is evaluated and logged but not yet enforced, so violations are surfaced for review without blocking real traffic.
>
> **Intent:** lock down Production-tagged Agents so they can only be driven by the sanctioned Maestro orchestration. Running it in simulation first lets the team verify the rule matches real traffic before flipping enforcement on.

---

## Sample policy — JSON definition

```json
{
    "policyType": "ToolUsePolicy",
    "organizationId": "<ORG_UUID>",
    "tenantId": "<TENANT_UUID>",
    "name": "Only the \"Order Processing\" Maestro can invoke Production Agents",
    "description": "Restrict tool-use of Production-tagged Agents so the only allowed caller is the \"Order Processing\" Maestro in Shared/Solution_Maestro_demo.",
    "selectors": [
        {
            "resourceType": "Agent",
            "values": ["*"],
            "operator": "Or",
            "tags": {
                "values": ["Production"],
                "operator": "Or"
            }
        }
    ],
    "executableRule": {
        "values": [
            {
                "type": "AgenticProcess",
                "values": ["<AGENTIC_PROCESS_UUID>"],
                "operator": "Or"
            }
        ]
    },
    "actorRule": {
        "values": [
            {
                "type": "User",
                "values": ["<USER_UUID>"],
                "operator": "Or"
            }
        ]
    },
    "enforcement": "Allow",
    "status": "Simulated"
}
```

> Replace `<ORG_UUID>` and `<TENANT_UUID>` from `~/.uipath/.auth` (Critical Rule #3). Replace `<AGENTIC_PROCESS_UUID>` and `<USER_UUID>` via [resource-lookup-guide.md](./resource-lookup-guide.md) once the user names a real process and user (Critical Rule #15). Resolve every `<…_UUID>` during Phase 1 — before the Spec is approved and Phase 2 composes the JSON. Never let a placeholder flow into the working file.

---

## How the sample seeds the Spec Components Table

The row meanings, allowed values, and defaults live in [planning-arch.md § Spec output format](./planning-arch.md#spec-output-format) — do not duplicate them here. The sample only supplies the **values** below; pre-fill them into the canonical table when the user adopts or adapts the sample.

| Row | Sample value |
|---|---|
| 1 (Policy name) | `Only the "Order Processing" Maestro can invoke Production Agents` |
| 2 (Description) | one-sentence summary of the narrative above |
| 3 (Status) | `Simulated` |
| 4 (Enforcement) | `Allow` |
| 5 (Resource type) | `Agent` |
| 6 (Resource scope) | `all` |
| 7 (Resource tag filter) | Any-of `[Production]` |
| 8 (Actor Process type) | `Maestro` |
| 9 (Actor Process scope) | one specific UUID — resolve via [resource-lookup-guide.md](./resource-lookup-guide.md) |
| 10 (Actor Process tag filter) | `(none)` |
| 11 (Actor Identity type) | `User` |
| 12 (Actor Identity scope) | one specific UUID — resolve via [resource-lookup-guide.md](./resource-lookup-guide.md) |

---

## How to present the sample

When intent is missing or thin, show the user **both** the Spec narrative and the JSON definition above (do not paraphrase — keep them verbatim so the user can compare to the file the skill will create), then ask the user to pick one of three paths:

```
This is a common access-policy shape — protect a tagged Resource, allow exactly one Actor Process, and narrow it to one Actor Identity.

Pick one to continue:
  1. Use this sample as-is (I'll just resolve the org/tenant/process/user UUIDs).
  2. Use this sample but adapt some rows (tell me which Spec rows you want to change — Resource, Actor Process, Actor Identity, tag filter, name, status). Enforcement is always `Allow` and cannot be changed (Critical Rule #2).
  3. Describe your own policy from scratch and I'll build the Spec with you.
```

Map the user's reply:

- **Option 1** → seed the Spec Components Table from the [mapping table above](#how-the-sample-seeds-the-spec-components-table) — every row pre-filled. Run [resource-lookup-guide.md](./resource-lookup-guide.md) to resolve the Maestro and User UUIDs (do NOT keep `<…_UUID>` placeholders). Read `~/.uipath/.auth` for `organizationId` / `tenantId` (Critical Rule #3). Continue to the [planning-arch.md](./planning-arch.md) Review gate — explicit `yes` is still required.
- **Option 2** → seed the Spec Components Table from the sample for rows the user did NOT change; mark the rows they want to change as `(missing)` and re-enter the [planning-arch.md](./planning-arch.md) iteration loop on those rows only.
- **Option 3** → drop the sample, return to [planning-arch.md](./planning-arch.md) intent analysis with the user's full description and build the Spec from scratch.

---

## Anti-patterns

- Do NOT silently start composing JSON when the user has not picked one of the three options. The sample is a prompt, not an approved Spec.
- Do NOT submit the sample to `uip gov access-policy create` with `<…_UUID>` placeholders intact — every UUID must be resolved first (Critical Rule #3 + Critical Rule #15).
- Do NOT emit `enforcement: "Deny"` when adapting the sample — `"Deny"` is **not authorable** (Critical Rule #2). Keep `enforcement: "Allow"` and reframe any Deny intent: ask what should be **allowed** and target that set, or use `operator: "None"` on tags / values to express "everything except X" (Critical Rule #2).
- Do NOT leave `status: "Simulated"` out when the user picks Option 1 or doesn't say otherwise — Simulated is the safe default for newly created policies (Critical Rule #13).
- Do NOT skip the Phase 1 review gate just because the user picked Option 1. The user must still explicitly approve the Spec before Phase 2 composes the working file (Critical Rule #6).
