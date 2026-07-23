# Agent Review Checklist

Manual quality checklist for UiPath AI agent projects — both low-code (`agent.json`) and coded (Python) agents.

> **Unit of Work:** Before running the checks below, complete Step 3a (Unit of Work Discovery) from `SKILL.md`. For low-code agents the declared unit is `agent.json` → `inputSchema`. For coded agents it is the `Input` Pydantic class in `main.py`. Compare that contract with what one invocation actually produces, and report one-to-many behavior using the transaction-shape guidance in `SKILL.md`.

## 1. Agent Type Appropriateness

Before reviewing implementation details, verify the right agent type was chosen:

| Criterion | Should Be Low-Code | Should Be Coded |
|---|---|---|
| Behavior expressible through prompts + pre-built tools | Yes | Overkill |
| Needs custom LLM reasoning or state machines | Wrong choice | Yes |
| Requires third-party Python libraries | Wrong choice | Yes |
| Standard UiPath capabilities only | Yes | Unnecessary complexity |
| Complex conditional HITL resume logic | Cannot do | Yes |
| Multi-agent routing in code | Cannot do | Yes |
| Speed of iteration is priority | Yes | Slower |
| Team is Python-proficient | Either works | Natural fit |

**Severity:** Flag agent type mismatch as **Warning** with recommendation.

## 2. Low-Code Agent Quality

> Report captured refresh, validation, and review-CLI failures verbatim. Do not reproduce checks those commands actually performed. A deterministic rule that the installed CLI did not emit must not be treated as having passed. The judgment catalog owns focused, rule-tagged semantic checks; the rows below cover broader deployment and operational context.

### Project and Model Fit

| Check | Severity | How to Verify |
|---|---|---|
| Project name communicates the agent's business purpose | Warning | Compare the name with the prompt, schemas, and business context |
| Selected model fits the task, cost, latency, and governance requirements | Warning | Compare model capabilities and deployment constraints with the intended workload |

### System Prompt Deployment Fit

| Check | Severity | How to Verify |
|---|---|---|
| Prompt language is suitable for deployed users and tested tool/runtime capabilities | Info | Review supported user languages and test multilingual tool calls where applicable |

### Tool Integration

| Check | Severity | How to Verify |
|---|---|---|
| Referenced processes, API workflows, and connections resolve in the target environment with the required access model | Critical | Verify published resources, shared connections, permissions, and environment mappings |
| Callers in review scope handle the agent's declared output contract correctly | Warning | Trace agent outputs into consuming workflows and compare expected fields, types, and failure states |
| Tool-call audit data is sufficient for the side effects and compliance risk involved | Info | Verify production traces or logs capture the tool, target, outcome, correlation, and actor where required |

### Context Grounding

For agents using context grounding:

| Check | Severity | How to Verify |
|---|---|---|
| Retrieval strategy and ingestion mode fit the source material and query pattern | Warning | Compare runtime versus indexed retrieval and text versus mixed-media ingestion with the use case |
| Index naming and alias strategy distinguish the corpus and deployment environment while allowing source versions to change without prompt churn | Info | Compare index names, stable aliases, source versions, and environment mappings with the release strategy |
| Referenced indexes resolve in the target environment and intended users can access them | Critical | Verify index identity, permissions, and environment mapping |
| Sync cadence keeps knowledge fresh enough for the business decision | Warning | Compare source-change frequency, ingestion schedule, and acceptable staleness |
| Result count balances recall, latency, and token cost | Info | Evaluate representative queries against the configured result count |
| Threshold balances precision against the risk of missing relevant content | Info | Evaluate representative positive, ambiguous, and no-answer queries |
| Context descriptions distinguish sources well enough for multi-source retrieval | Info | Compare descriptions and confirm each gives a clear selection cue |

### Escalation Operations

| Check | Severity | How to Verify |
|---|---|---|
| Escalation target resolves and has appropriate ownership and SLA | Critical | Verify the target in the deployment environment and confirm operational ownership, coverage, and response time |

### Guardrails

Review guardrails only through the review CLI and the structured guardrail workflow in `SKILL.md` Step 2.5. Carry those findings verbatim or apply their catalog rules; do not create parallel manual guardrail findings from this checklist.

## 3. Coded Agent Quality

### Dependency Maintenance

| Check | Severity | How to Verify |
|---|---|---|
| Every dependency has a demonstrated runtime or development use | Info | Trace imports, plugins, and build tooling before recommending removal |
| Version constraints balance reproducibility, supported compatibility, and upgrade policy | Warning | Compare constraints and lock data with the organization's release strategy |

### Runtime Design

| Check | Severity | How to Verify |
|---|---|---|
| LLM clients and other expensive resources initialize at a scope appropriate to the runtime | Warning | Assess import-time side effects, credential availability, reuse, concurrency, and redundant per-call construction |
| Observability captures the business decisions, tool outcomes, latency, and correlation needed to diagnose production failures | Warning | Trace representative execution paths and assess the usefulness of emitted spans and events |
| LLM and external-service timeouts fit the end-to-end SLA and fallback behavior | Info | Compare timeout and retry budgets with upstream and downstream limits |

### Framework-Specific Design

#### LangGraph

| Check | Severity | How to Verify |
|---|---|---|
| Conditional routing matches the capabilities and contracts of destination nodes | Warning | Trace each route condition through representative states and worker responsibilities |
| Every graph cycle has a business-valid exit condition | Critical | Review graph topology and termination behavior for unresolved and repeated states |
| Checkpointing strategy fits long-running, resumable, and conversational behavior | Info | Compare persistence needs, recovery expectations, and runtime-provided checkpointing |

#### LlamaIndex

| Check | Severity | How to Verify |
|---|---|---|
| Index lifecycle and retrieval design fit corpus size, freshness, and query behavior | Info | Review index construction, update strategy, retrieval flow, and expected workload |

#### OpenAI Agents SDK

| Check | Severity | How to Verify |
|---|---|---|
| Structured tool results are mapped coherently into agent context and downstream decisions | Warning | Trace tool-result fields across calls, handoffs, and final output construction |

## 4. Evaluation Quality

### Scenario and Decision Coverage

| Check | Severity | How to Verify |
|---|---|---|
| Evaluation scenarios cover representative happy paths, edge and error cases, corrected production failures, and adversarial inputs in proportion to deployment risk | Warning | Compare the scenario set with the business process, production incident history, threat model, and deployment criticality |
| Confidence policy is appropriate for probabilistic outputs | Warning | Confirm thresholds are calibrated against observed errors and the cost of false positives and false negatives |
| Low-confidence or unclear results have a viable downstream escalation path | Warning | Trace the consuming workflow and verify the human-review or fallback path in the target environment |

### Mocking Strategy

| Check | Severity | How to Verify |
|---|---|---|
| External dependencies are mocked realistically and consistently without replacing the behavior under evaluation | Warning | Compare mocks across evaluation sets with production contracts, representative responses, and failure modes |

## 5. Platform Constraints

Verify current platform documentation before reporting a limitation:

| Limitation | Impact | Check |
|---|---|---|
| Conversational agents cannot run automations on the user's local desktop | Critical if desktop execution is expected | Verify the architecture does not assume local execution |
| File-upload limits may exclude expected documents | Warning if large documents are expected | Compare current platform limits with representative files and failure handling |
| Channel integrations may support only a subset of message patterns | Info | Verify required Teams or Slack interaction patterns against current channel capabilities |

## 6. Deployment Readiness

| Check | Severity | How to Verify |
|---|---|---|
| Release and version-management policy supports compatibility, rollback, and traceability | Info | Review release identifiers, change history, rollback procedure, and consumer compatibility expectations |

## 7. Agent Security Review

### Tool Permissions

| Check | Severity | How to Verify |
|---|---|---|
| File-access tools are restricted to business-approved paths and storage locations | Warning | Verify effective permissions and path restrictions in the target environment |

### Data Protection

| Check | Severity | How to Verify |
|---|---|---|
| Context indexes containing sensitive data are inaccessible to unintended audiences | Critical | Verify source classification, index ACLs, and the agent's deployed audience |
| Production traces and logs exclude or mask sensitive values not required for diagnosis or audit | Warning | Inspect representative trace and log payloads against data classification and incident-response needs |
| Memory retention matches the business purpose, privacy policy, and deletion obligations | Info | Compare configured retention with data classification and regulatory requirements |
| Sensitive data is stored in memory only when necessary and with appropriate protection | Warning | Review memory use against minimization, access-control, and encryption requirements |

### User-Facing Controls

| Check | Severity | How to Verify |
|---|---|---|
| Rate limiting and abuse controls fit the exposure and cost of user-facing agents | Info | Verify effective tenant, channel, and upstream limits under expected and abusive traffic |

## 8. AI Trust Layer Audit

Verify that the organization's AI Trust Layer is properly configured for the agent's use case.

### Product Toggle Review

| Toggle | Default | Review Action |
|---|---|---|
| Enable calls to third-party AI models | Enabled | Verify this is intentional; disable if the agent should use only UiPath-hosted models |
| Enable Agents | Yes | Required for low-code agent operation |
| Enable Coded Agents | Yes | Disable if only low-code agents are used |
| Enable Document Understanding features | Yes | Disable if Document Understanding is not used |
| Enable UiPath GenAI activities | Yes | Verify scope and disable unused capabilities |

**Review principle:** Apply least privilege by disabling toggles the deployed solution does not need.

### Trace and Audit Settings

| Check | Severity | How to Verify |
|---|---|---|
| Trace retention fits compliance requirements | Warning | Verify the effective AI Trust Layer retention setting |
| Input/output audit saving is appropriate for production agents | Warning | Balance incident investigation needs with data-minimization requirements |
| PII protection is configured before data reaches models where required | Warning | Verify effective pseudonymization or masking with representative sensitive inputs |

## 9. Agent Governance Policies

If the organization uses Automation Ops agent governance:

| Check | Severity | How to Verify |
|---|---|---|
| Minimum reliability score matches production risk tolerance | Warning | Verify the effective governance threshold and its evidence base |
| Maximum token count controls response cost without truncating valid work | Info | Compare the effective token limit with representative executions |
| Temperature policy matches allowed task variability | Info | Compare the effective threshold with classification, extraction, and generation workloads |
| Human review is required for Autopilot-generated suggestions where business risk warrants it | Info | Verify effective approval policy and reviewer ownership |
