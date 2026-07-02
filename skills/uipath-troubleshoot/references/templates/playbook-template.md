---
confidence: high | medium | low
signatures:
  - kind: exception | message | message-key | error-code | error-code-prefix | http-status | state
    value: "<verbatim greppable string from the real failure>"
    note: "<optional discriminator — required when another playbook claims the same (kind, value)>"
exclusions:
  - "<signature> → <sibling-playbook>.md"   # optional — only when the body explicitly redirects
# silent: true                              # instead of signatures:, for playbooks with no greppable signature
---

# <Title>

## Context

What this looks like:
- <observable symptom 1>
- <observable symptom 2>

What can cause it:
- <cause 1>
- <cause 2>

What to look for:
- <signal or pattern that helps narrow down the cause>

## Investigation

1. <step — can be a CLI command, a comparison, a check, or any actionable instruction>
2. <step>
3. <step>

## Resolution

- **If <finding 1>:** <specific fix — what to change, where, how>
- **If <finding 2>:** <specific fix>
