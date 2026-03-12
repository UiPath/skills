# Evidence Schema

## Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `.investigation/evidence/` | Interpreted evidence summaries | JSON files with analysis and interpretation |
| `.investigation/raw/` | Raw data dumps | Unprocessed MCP responses, RAG results, file contents |

Created by: Triage sub-agent, Hypothesis Tester sub-agent
Read by: All sub-agents, orchestrator

## File naming

### Evidence files (`.investigation/evidence/`)

- `triage-initial.json` — initial data from triage (job info, error, etc.)
- `{hypothesis-id}-{source}.json` — evidence for a specific hypothesis
  - e.g., `H1-mcp-data.json`, `H1-rag-results.json`, `H2a-source-analysis.json`

### Raw data files (`.investigation/raw/`)

- `triage-{tool-name}.json` — raw triage MCP response
- `{hypothesis-id}-{tool-name}.json` — raw MCP/RAG response for a hypothesis
  - e.g., `H1-Jobs_GetByKeyByIdentifier.json`, `H1-GetJobTraces.json`, `H1-rag-query.json`

## Structure

Each evidence file:

```json
{
  "id": "evidence-unique-id",
  "hypothesis_id": "H1",
  "source": "mcp | rag | knowledge_graph | user | source_code",
  "collected_by": "triage | tester",
  "timestamp": "ISO8601",
  "query": "What was queried or asked (MCP tool name, RAG query, file path read)",
  "raw_data_ref": "raw/H1-Jobs_GetByKeyByIdentifier.json",
  "raw_data_summary": "Condensed summary of what was found (keep under 100 lines)",
  "interpretation": "What this evidence means for the hypothesis",
  "elimination_checks": [
    {
      "criterion": "what elimination criterion from evidence_needed.to_eliminate was checked",
      "result": "what the query/check actually returned",
      "outcome": "passed (hypothesis survives) | failed (hypothesis eliminated)"
    }
  ],
  "execution_path_traced": [
    {
      "step": "description of this step in the expected execution path",
      "expected": "what the hypothesis predicts should have happened",
      "actual": "what the data actually shows",
      "verified_by": "which MCP query or data source confirmed this"
    }
  ],
  "playbook_compliance": [
    {
      "playbook": "product/orchestrator.md",
      "section": "On: queue items failing [phase: testing]",
      "requirement": "Get ALL failed queue items (paginate if >100)",
      "completed": true,
      "details": "Retrieved all 160 items across 2 pages"
    }
  ],
  "needs_user_input": false,
  "user_question": null
}
```

## Rules

- **Raw data MUST be written to `.investigation/raw/` immediately** — write the full response to a raw file BEFORE summarizing
- **Never keep raw data in context** — write it to a raw file, then read it back only if needed for analysis. Do not hold MCP responses, log dumps, or RAG results in the agent's working memory.
- Evidence files contain summaries and interpretation only; they reference raw files via `raw_data_ref`
- If a sub-agent needs user input, set `needs_user_input: true` and `user_question` to the question
- The orchestrator reads evidence files (not raw files) to make decisions
- Evidence files are immutable once written — new evidence gets a new file
- Raw files are immutable once written — they are the source of truth for what was actually returned
