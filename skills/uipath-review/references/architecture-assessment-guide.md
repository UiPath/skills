# Architecture Assessment Guide

Architecture-level evaluation framework for UiPath automation solutions during Step 4 (Optimization). Evaluate design decisions, not implementation quality; use type-specific checklists for implementation review.

## 1. Process Suitability

Determine whether automation and the selected automation type are appropriate.

| Criterion | Favorable | Unfavorable | Assess by |
|---|---|---|---|
| Rule-based | Clear, documented rules | Human judgment or intuition required | Read PDD or infer from workflow logic |
| High volume | >50 transactions/day OR high frequency | <5 transactions/week | Ask user or check queue volume data |
| Stable interfaces | Applications rarely change UI/API | Frequent UI redesigns or API changes | Ask about application change frequency |
| Digital input | Digital data | Handwritten, verbal, or physical input | Check workflow input sources |
| Low exception rate | >80% follow the standard path | >50% require human intervention | Check exception-handling complexity |
| Measurable | Clear ROI metrics | Benefits are intangible or difficult to measure | Check KPI tracking |

| Finding | Severity | Recommendation |
|---|---|---|
| Process is not rule-based and uses RPA (not agent) | Warning | Consider an agent-based or hybrid approach |
| Volume is very low (<5/week) with complex automation | Info | Assess whether ROI justifies complexity |
| Interfaces change frequently | Warning | Use resilience measures such as Object Repository, anchor-based selectors, and healing |
| Input is not digital and no DU pipeline exists | Warning | Add a Document Understanding pipeline or consider a manual step |
| Exception rate >50% | Warning | Reconsider scope or add human-in-the-loop handling |
| No metrics or monitoring | Info | Add KPI tracking to justify ROI |

## 2. Complexity Classification

| Level | Criteria | Architecture expectations |
|---|---|---|
| **Simple** | Single application, linear flow, <10 steps, structured data | Single workflow or simple sequence; REFramework optional; basic error handling |
| **Medium** | 2-3 applications, branching, data transformations, 10-30 steps | REFramework or equivalent; Config.xlsx; proper error handling; sub-workflows |
| **Complex** | Multiple applications, many exception paths, queues, unstructured data, business rules | Dispatcher-Performer; REFramework mandatory; library extraction; comprehensive testing |
| **Advanced** | RPA + agents + humans, long-running, cross-system orchestration, AI/ML | Maestro/Flow orchestration; agents for reasoning; evaluation sets; full CI/CD |

| Mismatch | Severity | Recommendation |
|---|---|---|
| Simple process with complex architecture | Info | Remove unnecessary REFramework, queues, or libraries |
| Complex process with simple architecture | Warning | Add REFramework, proper error handling, and configuration management |
| Advanced process without Flow/Maestro orchestration | Warning | Add orchestration for multi-actor coordination |
| Agent used for a simple deterministic task | Info | Replace with RPA for cost efficiency and determinism |
| RPA used for an advanced reasoning task | Warning | Replace with an agent or hybrid approach |

### Process Mining as Suitability Input

When Process Mining or Task Mining data exists, use it in the suitability assessment.

| Data source | Indicates | Review action |
|---|---|---|
| Process Mining event logs | Actual flow, variants, bottlenecks, and rework loops | Verify that automation matches the actual process, not only the documented ideal |
| Task Mining recordings | Desktop actions, time per step, and user variation | Verify coverage of the most common task variant first |
| Variant analysis | Number of real process paths | Treat high variation (>10 common variants) as higher complexity |
| Automation scoring | Volume × rule-based-ness × stability | Verify scored candidates match the targeted processes |
| Baseline metrics | Current cycle time, error rate, and throughput | Use for post-automation comparison |

| Check | Severity | Verify by |
|---|---|---|
| Process Mining data validated scope, if available | Info | Ask whether mining was performed during discovery |
| Baseline metrics were recorded before automation | Info | Check for pre-automation measurement |
| Automation targets highest-volume, lowest-variation paths | Info | Compare scope with mining variant analysis |

## 3. Environment Separation

Verify isolation for safe deployment.

### Environment Existence

| Check | Severity | Verify by |
|---|---|---|
| Separate Development, Test/QA, UAT, and Production environments exist | Warning | Ask or check Orchestrator folder structure |
| Each environment has its own Orchestrator folder | Warning | Check folder configuration |
| Configuration differs by environment (URLs, paths, credentials) | Warning | Check config.json or asset management |
| Deployment follows Dev → Test → UAT → Prod | Info | Ask about deployment process |

### Configuration Isolation

| Check | Severity | Verify by |
|---|---|---|
| No production URLs or paths are in development code | Warning | Grep project files for production domain names |
| Credentials are environment-specific, not shared | Critical | Check credential asset configuration |
| Queue names differ by environment OR folder isolation is used | Warning | Check queue naming or folder strategy |
| Assets are folder-scoped, not global | Warning | Check asset folder assignments |
| Config.json or solution configuration supports environment overrides | Info | Check configuration structure |

### Deployment Safety

| Check | Severity | Verify by |
|---|---|---|
| Rollback plan documents how to revert to the previous version | Info | Check documentation or deployment procedures |
| Production uses version pinning, not "latest" | Warning | Check process version configuration |
| CI/CD enforces tests before production deployment | Info | Check pipeline configuration |
| Production change approval exists | Info | Ask about governance |

## 4. Architecture Principles Scoring

Score each applicable principle from 1-5 and report the scores. These six principles inform Step 4 and do **not** feed the agent letter grade, which is computed from finding counts in [agent-grading-rubric.md](agents/agent-grading-rubric.md). Exclude a principle only when it genuinely does not apply (for example, queue-style Scalability for a single agent), and state the exclusion.

### Modularity (1-5)

| Score | Criteria |
|---|---|
| 1 | Monolithic: all logic in one workflow, no separation of concerns |
| 2 | Some separation: Main.xaml delegates a few tasks, but workflows remain large |
| 3 | Adequate: clear workflow responsibilities and some reuse |
| 4 | Good: clean separation, libraries for shared logic, testable components |
| 5 | Excellent: fully modular, library-based, independently testable, documented interfaces |

Assess by counting workflows and checking responsibilities, library usage, and duplicated logic.

### Scalability (1-5)

| Score | Criteria |
|---|---|
| 1 | Sequential processing, no queue support, single robot |
| 2 | Sequential, but multiple robots could be supported with minor changes |
| 3 | Queue-based processing OR multiple-robot support |
| 4 | Dispatcher-Performer with queue and horizontal scaling |
| 5 | Elastic scaling, cloud robots, load-balanced queue processing, performance optimization |

Assess queue usage, Dispatcher-Performer design, robot configuration, and batch processing.

### Resilience (1-5)

| Score | Criteria |
|---|---|
| 1 | No error handling or retry; crashes on first failure |
| 2 | Basic Try-Catch without retry or transaction recovery |
| 3 | REFramework or equivalent retry logic and basic exception handling |
| 4 | Business/System exception distinction, circuit breaker, and recovery procedures |
| 5 | Retry with backoff, circuit breaker, graceful degradation, and self-healing selectors |

Assess exception handling, retry configuration, REFramework compliance, and recovery workflows.

### Maintainability (1-5)

| Score | Criteria |
|---|---|
| 1 | No naming conventions, documentation, or version control |
| 2 | Some naming conventions and minimal documentation |
| 3 | Consistent naming, Config.xlsx, basic documentation, and version control |
| 4 | Clean, documented, tested code that is easy to onboard developers to |
| 5 | Full documentation, comprehensive tests, CI/CD, code review, and activity annotations |

Assess naming conventions, Config.xlsx usage, test coverage, documentation, and git history.

### Security (1-5)

| Score | Criteria |
|---|---|
| 1 | Hardcoded credentials, plaintext passwords, no access control |
| 2 | Some credentials in assets, but inconsistent |
| 3 | All credentials in Orchestrator assets; SecureString used |
| 4 | External credential store, least-privilege robot accounts, no PII in logs |
| 5 | Vault integration, encrypted queues, audit trails, PII masking, compliance readiness |

Assess credential storage, SecureString usage, log content, queue encryption, and access controls.

### Governance (1-5)

| Score | Criteria |
|---|---|
| 1 | No process documentation, monitoring, or approval workflow |
| 2 | Basic PDD and some monitoring |
| 3 | PDD and SDD, Orchestrator monitoring, and change management |
| 4 | CoE standards, Automation Ops policies, and CI/CD pipeline |
| 5 | CoE oversight, approval workflows, audit compliance, automation inventory, and KPI tracking |

Assess documentation, monitoring dashboards, Automation Ops policies, deployment procedures, and governance controls.

## 5. Non-REFramework State Machines

For State Machine layouts outside REFramework, verify:

| Check | Severity | Verify by |
|---|---|---|
| Each state has one clear responsibility | Warning | Read state names and entry actions |
| Every state has at least one outgoing transition | Critical | Check for dead-end states |
| Each state has a default transition | Warning | Check for unhandled conditions that could cause runtime hangs |
| No infinite cycle lacks an exit condition | Critical | Trace transitions and verify every cycle exits |
| Entry and exit actions are lightweight | Info | Check that heavy logic is in transitions or sub-workflows |
| State names are descriptive, not "State1" or "State2" | Info | Review state naming |
| Final State is reachable from every state through some transition path | Critical | Trace reachability to Final State |
