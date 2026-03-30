# Diagnostics Knowledge Base Guide

This document describes how the diagnostics knowledge base is structured, what each part does, and how to create new content.

## Structure

```
references/
  summary.md                            <- Entry point. Routes agents to the correct product.
  investigation_guide.md                <- Generic investigation rules (all products).
  templates/                            <- Templates for creating new playbooks.
  products/{id}/                        <- One folder per product.
  activity-packages/{id}/               <- One folder per activity package.
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

### summary.md (required)

The playbook index. Lists all playbooks for this product, organized by confidence level. This is how agents discover which playbooks exist and their confidence. Every new playbook must be added here.

### playbooks/ (required)

The actual playbook files. Each file is a standalone, self-contained playbook covering one issue or one known error pattern.

When an issue has multiple distinct sub-scenarios (e.g., "Orchestrator Down" can be IIS crash, startup failure, or redirect loop), create separate standalone playbooks for each sub-scenario: `orchestrator-down-forcibly-closed.md`, `orchestrator-down-startup-failure.md`, `orchestrator-down-redirect-loop.md`. Each playbook's `## Context` covers its own causes and patterns. The summary lists all of them — triage matches the right ones, and hypotheses are tested in confidence order (high first).

## Playbooks

Every playbook uses the same structure: `## Context`, `## Investigation`, `## Resolution`. The difference between playbooks is how much you know about the issue when writing it.

| Confidence | What you know | `## Context` | `## Investigation` | `## Resolution` | Example |
|---|---|---|---|---|---|
| **High** | Exact error → exact cause | Match pattern + root cause | Quick verification (1-2 steps) | Concrete fix | "GetAsset" error → asset missing in folder |
| **Medium** | Specific error → known diagnostic path | Causes, patterns, what to look for | Concrete diagnostic steps | Fixes mapped to findings | SSL cert invalid → check cert, chain, trust store |
| **Low** | General symptoms → multiple possible causes | Causes, patterns, what to look for | General data gathering guidance (or absent) | Optional | Robot unresponsive → could be heartbeat, network, or machine issue |

### How to decide what to write

- **Do you know the exact cause from the error alone?** Write a high-confidence playbook. One verification step, one fix.
- **Do you have a repeatable diagnostic path?** Write a medium-confidence playbook. Step-by-step investigation that leads to the answer.
- **Do you only know what to look for?** Write a low-confidence playbook. Describe the symptoms, causes, and what data to gather. The agent reasons from there.

You can always start with low confidence and upgrade later as you learn more about the issue.

### Standard Headers

All playbooks use the same three headers:

| Section | What goes here | Who reads it |
|---------|---------------|-------------|
| `## Context` | What the issue is, what causes it, what to look for. Always present. | Triage (for initial data gathering). Generator (to produce hypotheses — 1 for high-confidence, 2-5 for medium/low). Tester (for understanding). |
| `## Investigation` | Steps to diagnose or verify. Can be absent for low-confidence playbooks. | Tester (follows steps if present, reasons freely if absent). |
| `## Resolution` | Known fixes. Can be absent if the fix depends on what the investigation finds. | Orchestrator (presents fixes to the user). |

Template: `templates/playbook.md`

## How Agents Use This

### Triage

Reads `summary.md` to find the right product, then reads the product's `summary.md` to find ALL matching playbooks. Records every match with its confidence in `state.json`. Multiple playbooks may describe the same issue — all are recorded.

### Hypothesis Generation

The generator reads `## Context` from all matched playbooks and produces hypotheses. Playbook confidence determines how many:

- **High confidence** → exactly 1 hypothesis per playbook, high confidence
- **Medium / Low confidence** → 2-5 hypotheses as normal

Hypotheses are tested in confidence order. High-confidence hypotheses are tested first.

### Testing

The tester reads `## Context` for understanding, then:
- If `## Investigation` exists → follows the steps
- If `## Investigation` is absent → reasons freely from context and evidence

### Investigation Guides

The investigation guide (generic + product-specific) tells agents how to verify their data is correct before drawing conclusions. Applied regardless of playbook confidence.

## Creating New Content

Template is in `references/templates/playbook.md`. Copy it, set the `confidence` field in the frontmatter (high, medium, or low), fill in the sections, and add the entry to the product's `summary.md`. The summary's Confidence column must match the playbook's frontmatter.
