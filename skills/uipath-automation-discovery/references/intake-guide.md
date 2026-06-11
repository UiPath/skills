# Intake Guide (Phase 0)

Detailed intake steps. Load this file during Phase 0.

## 0A. Company Context

Elicit from the user:
- What does the company do? (industry, size, business model)
- Relationship with automation today? (dedicated COE? ad-hoc? nothing?)
- Known pain points? (capture as hypotheses to validate, not conclusions)

## 0B. Tool & System Inventory

Ask explicitly for each category. Build this table:

```
| Category       | Tool             | Access Method        | Verified? |
|----------------|------------------|----------------------|-----------|
| Messaging      |                  | MCP / CLI / browser  |           |
| Email          |                  | MCP / CLI / API      |           |
| Wiki           |                  | MCP / API / browser  |           |
| Issue Tracker  |                  | MCP / API / CLI      |           |
| CRM            |                  | CLI / API / browser  |           |
| HRIS           |                  | API / browser        |           |
| ERP / Finance  |                  | API / browser        |           |
| Code / DevOps  |                  | CLI / API            |           |
| Monitoring     |                  | API / browser        |           |
| Expense/Travel |                  | browser              |           |
| Procurement    |                  | API / browser        |           |
| Calendar       |                  | MCP / CLI / API      |           |
| Doc Storage    |                  | MCP / CLI / API      |           |
| Internal Search|                  | browser              |           |
```

## 0C. Access Verification

Test each tool with a minimal read-only operation before committing to mine it.
If access fails, note it and move on — don't block discovery on one tool.

Example access tests (adapt to your environment):
- Slack: MCP `slack_read_channel` or `slack_search_public`
- Confluence: MCP `searchConfluenceUsingCql` with simple CQL
- Jira: MCP `searchJiraIssuesUsingJql` with simple JQL
- Salesforce: `sf data query --result-format json` (Salesforce CLI)
- Gmail/Outlook: whichever mail MCP or CLI the user has configured
- GitHub: `gh api user --jq .login` (GitHub CLI)
- If a named tool is unavailable, ask the user which installed tool or connector to use. Do not invent CLI flags.

## 0D. Org Structure & Scope

- Point me to an org chart? (wiki page, HRIS, etc.)
- Complete department list (including shared services: IT, HR, Finance, Legal, Procurement)
- Any departments off-limits?
- Key people to watch? (executives, ops leads)

## 0E. Output & Audience

- Where should the report go? (Confluence, Notion, Google Docs, local file)
- Who is the audience? (leadership, COE, department heads)
- Draft or publish directly?

## 0F. User Hypotheses

Capture what the user already suspects as search targets, not conclusions:
- "I think expense is broken" → search for evidence in Phase 1
- "Sales forecasting takes too long" → look for signals

## 0G. Scope Control

Agree on depth before starting:
- **Quick scan** (~1 hour): Messaging channels + wiki only. Cap at 10 findings. Stop after 2 source passes with no new high-confidence findings.
- **Standard** (~3 hours): All verified sources. Full department map. Cap at 25 findings. Max 2 retries per failed source.
- **Deep dive** (~6+ hours): Per-department behavioral agents. PDD deep reads. Strategic analysis. Cap at 35 findings. Timebox Phase 1 at 3 hours.

Share interim findings after each phase. Ask before going deeper.

## 0H. Privacy & Authorization

Before mining, confirm:
- Is the requester authorized to analyze these systems and employee data for this purpose?
- Are private channels, DMs, or special-category HR data (payroll, performance reviews) in scope? Default: excluded.
- Should findings name individuals or use pseudonyms (e.g., "Sales Ops Lead A")? Default: pseudonymize.
- Any jurisdiction constraints? (GDPR, works council, internal privacy policy.) Apply the stricter rule when uncertain.

Document the agreed privacy scope. Revisit if you discover sensitive data during mining.
