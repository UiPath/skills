# Report Template

Adapt the output format to whatever the company uses (Confluence, Notion,
Google Docs, SharePoint, or local markdown). The structure below is universal.

## Page Structure

```
Title: Internal Automation Discovery Report — {Month} {Year}

1. Header
   - Author, date, sources summary (list every system mined)

2. Executive Summary
   - Total opportunities found
   - #1 insight (the replicable model finding — this is always the headline)
   - Meta-insight (biggest strategic gap or dogfooding finding)

3. Part 1: Behavioral Analysis
   3a. Replicable Model Opportunity Table
       | Working Model | Where It's Missing | Addressable Volume |
   3b. Single Points of Failure Table
       | Person | System/Channel | Role | Risk |
   3c. Top 15 Behavioral Opportunities (ranked by evidence)
       | # | Automation | Source & Evidence | Impact |
       Each row: specific system, quantitative metric, person names

4. Part 2: Department Coverage
   4a. Departments with ZERO automation coverage (table)
       | Department | Existing Automations | Key Gap |
   4b. Departments with coverage but remaining gaps (table)
   4c. Key existing automation summaries (table with maturity + ROI)
   4d. Cross-cutting patterns paragraph (common systems, architectures)

5. Part 3: Strategic Analysis
   - Business context paragraph (revenue, growth, strategy, challenges)
   - Strategic gaps table
       | # | Automation | Strategic Driver | Why Missing Matters |

6. Part 4: Prioritized Recommendations
   - Tier 1: Replicate Proven Models (task checklist)
   - Tier 2: Behavioral Workflow Automations (task checklist)
   - Tier 3: Operational Gaps (task checklist)
   - Tier 4: Business-Critical Strategic (task checklist)

7. Summary Statistics Table
   | Metric | Value |
   Include: data points analyzed, existing automations found,
   departments mapped, SPOFs identified, total opportunities,
   ROI benchmarks from existing projects

8. Methodology
   - Every data source used with what was found
   - Generation date
   - "Living document — add your own pain points below"
```

## Task List Format

Use checkboxes so items can be tracked:

```markdown
## Tier 1: Replicate Proven Models

- [ ] Replicate {model_name} to {target_1} ({volume} volume)
- [ ] Replicate {model_name} to {target_2} ({volume} volume)

## Tier 2: Behavioral Workflow Automations

- [ ] {automation_name} ({evidence summary})
```

## Evidence Standards

Every opportunity MUST include at minimum:
- **Source**: Where the evidence came from (channel name, system, email pattern)
- **Quantitative metric**: Message count, hours spent, frequency, ticket volume
- **Who is affected**: Person name (for SPOFs) or team/department
- **Estimated impact**: Deflection %, hours saved, cycle time reduction, or qualitative

Tier 4 (strategic) is the only tier allowed to lack direct behavioral evidence,
but must reference specific business metrics or strategy documents.

## Adapting to Output Platforms

| Platform | How to Create |
|---|---|
| Confluence | Atlassian MCP `createConfluencePage` with markdown contentFormat |
| Notion | Notion API or MCP to create page |
| Google Docs | Google Docs API or `gws-docs` CLI |
| SharePoint | SharePoint API or manual upload |
| Local file | Write markdown to user's filesystem |

When no wiki/doc platform is available, produce a well-formatted local
markdown file the user can share however they choose.
