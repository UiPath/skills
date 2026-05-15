---
confidence: high
---

# Insufficient Funds / Agent Units (400)

## Context

What this looks like:
- HTTP 400 from an agent or GenAI activity
- Error message: `Insufficient funds: Your account doesn't have enough credits for execution. Please add funds or contact your administrator for assistance.`

What can cause it:
- Tenant has exhausted its Agent Units (AU) allocation — agents and GenAI activities consume AU on every LLM call
- Community Edition free-tier credits exhausted (reset monthly)
- Enterprise subscription on a Flex license without AU allocated
- Known bug (~early 2026): Maestro debug incorrectly required AU even though standalone Agent debug did not; impacted customers without AU even when they expected debug to be free

What to look for:
- Whether the failing element is an Agent or GenAI activity — non-agent processes do not consume AU
- Tenant AU balance — exhausted vs not allocated
- Debug vs deployed — historical bug only affected debug mode

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json` — error message is self-explanatory
2. Confirm the element type: agent/GenAI vs other
3. Check AU balance: Orchestrator UI → **Admin > Tenant > Licenses > Consumption > Agent Units**
4. Verify debug-mode behaviour against the latest Maestro release notes — the debug-consumes-AU bug had a planned fix in late Feb / mid-March 2026

## Resolution

- **If AU exhausted on Enterprise:** purchase / allocate more via **Admin > Organization > Subscriptions** or contact the UiPath account manager
- **If Community / Flex with no AU:** request promo units or upgrade to a plan that includes AU
- **If only failing in debug:** confirm the Maestro deploy includes the fix for the debug-mode AU bug; if not, request rollout or escalate to the Maestro team
- **If the process should not need AU at all:** verify no Agent/GenAI activities are accidentally present in the path being executed

## References

- [Docs: Purchasing a Plan](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/purchasing-a-plan)
- [Forum: Insufficient funds](https://forum.uipath.com/t/agent-baseerror-insufficient-funds-your-account-doesnt-have-enough-credits-for-execution/5726606)
