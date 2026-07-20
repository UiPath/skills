# Troubleshooting Knowledge Base Guide

This document describes how the troubleshooting knowledge base is structured, what each part does, and how to create new content.

## Structure

```
references/
  summary.md                            <- Domain descriptions, CLI entry points, no-signature routing.
  investigation_guide.md                <- Generic investigation rules (all products).
  presenting.md                         <- Resolution formatting, fix assembly, approval gate.
  escalation.md                         <- Competitive-hypothesis protocol (probes, verifier).
  templates/                            <- Templates for creating new playbooks.
  products/{id}/                        <- One folder per product.
    overview.md                         <- (optional) Product overview and dependencies.
    investigation_guide.md              <- (optional) Product-specific investigation rules.
    presentation.md                     <- (optional) Product-specific display rules.
    summary.md                          <- (required) Playbook index with confidence levels.
    playbooks/                          <- (required) Individual playbook files.
  activity-packages/{id}/               <- One folder per activity package (same structure).
```

## Product / Activity Package Container

Each product or activity package has its own folder containing:

### overview.md (optional)

A summary describing the system and what it does. What features it provides, what it depends on, what kind of issues users encounter with it.

### investigation_guide.md (optional)

A specific investigation guide detailing what the agent must look out for when investigating issues for that particular product.

For example, in Orchestrator the agent must verify:
- The product it is investigating is the same as the process the client referred to
- The data gathered is from the correct folder
- The logs, traces, and jobs are related to the actual robot that the user referenced

Each product has different concerns. UI Automation needs to verify the correct activity and selector. Maestro needs to verify the correct BPMN process and task. This guide captures those product-specific verification rules.

### presentation.md (optional)

Product-specific display rules for how to format entity names, IDs, and labels in user-facing output. Defines how to refer to the product's entities (e.g., connections by display name, jobs by process name, instances by BPMN process name). Read at presentation time (`references/presenting.md` § 1) for every domain in the causal chain.

### summary.md (required)

The playbook index. Lists all playbooks for this product, organized by confidence level. Runtime routing greps playbook files directly; this index is the browse and fallback surface (family-playbook routing, escalation, silent failures). Every new playbook must be added here.

### playbooks/ (required)

The actual playbook files. Each file is a standalone, self-contained playbook covering one issue or one known error pattern.

When an issue has multiple distinct sub-scenarios (e.g., "Orchestrator Down" can be IIS crash, startup failure, or redirect loop), create separate standalone playbooks for each sub-scenario: `orchestrator-down-forcibly-closed.md`, `orchestrator-down-startup-failure.md`, `orchestrator-down-redirect-loop.md`. Each playbook's `## Context` covers its own causes and patterns. The summary lists all of them — triage matches the right ones, and hypotheses are tested in confidence order (high first).

## Playbooks

Every playbook uses the same structure: `## Context`, `## Investigation`, `## Resolution`. The difference between playbooks is how much you know about the issue when writing it.

| Confidence | What you know | `## Context` | `## Investigation` | `## Resolution` | Example |
|---|---|---|---|---|---|
| **High** | Exact error → exact cause | Match pattern + root cause | Quick verification (1-2 steps) | Concrete fix | "GetAsset" error → asset missing in folder |
| **Medium** | Specific error → known troubleshooting path | Causes, patterns, what to look for | Concrete troubleshooting steps | Fixes mapped to findings | SSL cert invalid → check cert, chain, trust store |
| **Low** | General symptoms → multiple possible causes | Causes, patterns, what to look for | General data gathering guidance (or absent) | Optional | Robot unresponsive → could be heartbeat, network, or machine issue |

### How to decide what to write

- **Do you know the exact cause from the error alone?** Write a high-confidence playbook. One verification step, one fix.
- **Do you have a repeatable troubleshooting path?** Write a medium-confidence playbook. Step-by-step investigation that leads to the answer.
- **Do you only know what to look for?** Write a low-confidence playbook. Describe the symptoms, causes, and what data to gather. The agent reasons from there.

You can always start with low confidence and upgrade later as you learn more about the issue.

### Standard Headers

All playbooks use the same three headers:

| Section | What goes here | Who reads it |
|---------|---------------|-------------|
| `## Context` | What the issue is, what causes it, what to look for. Always present. | The investigator, to confirm the match fits the evidence and learn the cause list. |
| `## Investigation` | Steps to troubleshoot or verify. Can be absent for low-confidence playbooks. | The investigator (follows steps in decision-tree order if present, reasons freely if absent). Escalation probes inherit these as their only allowed commands. |
| `## Resolution` | Known fixes. Can be absent if the fix depends on what the investigation finds. | Presentation phase (`references/presenting.md` assembles fixes for the user). |

Template: `templates/playbook-template.md`

### Greppable Signatures

Routing greps playbook files directly, so a playbook is reachable only if its `## Context` quotes the failure's signals verbatim:

1. Quote in "What this looks like" the exact strings the real failure produces — exception class (FQN), verbatim message fragments, localization resource keys, error codes, HTTP statuses. Never paraphrase; trim placeholder segments.
2. When two playbooks share a signal (same exception class, same message), each body must state its discriminator and explicitly redirect to the sibling playbook for the other case ("NOT for X → other-playbook.md").
3. A playbook with no crisp greppable signal (silent failure, hang, wrong result) is a last resort — a distinctive log line or state combination is still a signature. Such playbooks are reachable only via the no-signature routing table in `references/summary.md` and the domain's `summary.md`.
4. `confidence` (frontmatter) is a cap on root-cause certainty, not a routing rank.

### Cross-Product References

Playbooks may reference other product domains (e.g., an Orchestrator playbook mentioning "ProcessOrchestration" or "BPMN", a Maestro playbook referencing child Orchestrator jobs). Use explicit product names when describing cross-domain behavior — cross-domain signals (entity keys, exception namespaces) are what route the investigator across the domain boundary.

## How the Investigator Uses This

1. **Route** — greps the playbook corpus with extracted signals; loads only the matched playbook plus its domain's `investigation_guide.md`.
2. **Walk** — confirms the match against `## Context`, executes `## Investigation` in decision-tree order, verifies the cause against the "What can cause it" list before presenting.
3. **Escalate** — on ambiguity, `references/escalation.md` drafts one candidate per plausible playbook; probes gather evidence using only commands documented in the playbook or product overview.
4. **Investigation guides** (generic + product-specific) define how to verify data correlation before drawing conclusions. Applied regardless of playbook confidence.

## Creating New Content

Template is in `references/templates/playbook-template.md`. Copy it, set the `confidence` field, quote the failure's verbatim signature strings in `## Context` per Greppable Signatures above, fill in the sections, and add the entry to the product's `summary.md` (Confidence column must match the frontmatter).
