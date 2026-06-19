# Architecture Assessment Guide

Architecture-level evaluation framework for UiPath automation solutions. Use during Step 4 (Optimization) of the review workflow to assess whether the right approach, architecture, and operational practices were chosen.

> This guide evaluates **design decisions**, not implementation quality. Use the type-specific checklists (RPA, agent, flow) for implementation-level review.

## 1. Process Suitability Assessment

Before evaluating how well the automation is built, assess whether automation was the right choice and whether the right type of automation was chosen.

### Suitability Criteria

| Criterion | Favorable for Automation | Unfavorable | How to Assess |
|---|---|---|---|
| Rule-based | Process follows clear, documented rules | Requires human judgment or intuition | Read PDD or infer from workflow logic |
| High volume | >50 transactions/day OR high frequency | <5 transactions/week | Ask user or check queue volume data |
| Stable interfaces | Applications rarely change UI/API | Frequent UI redesigns or API changes | Ask user about application change frequency |
| Digital input | Data available in digital format | Handwritten, verbal, or physical inputs | Check input sources in workflow |
| Low exception rate | >80% of cases follow the standard path | >50% require human intervention | Check exception handling complexity |
| Measurable | Clear metrics to quantify ROI | Benefits are intangible or hard to measure | Check for KPI tracking in solution |

### Suitability Findings

| Assessment Result | Severity | Recommendation |
|---|---|---|
| Process is not rule-based and uses RPA (not agent) | Warning | Consider agent-based or hybrid approach |
| Volume is very low (<5/week) with complex automation | Info | ROI may not justify automation complexity |
| Application interfaces change frequently | Warning | Design for resilience: Object Repository, anchor-based selectors, healing |
| Input is not digital and no DU pipeline | Warning | Add Document Understanding pipeline or consider manual step |
| Exception rate >50% | Warning | Reconsider automation scope or add human-in-the-loop |
| No metrics or monitoring in place | Info | Add KPI tracking for ROI justification |

## 2. Complexity Classification

Classify the solution's complexity to set appropriate review expectations.

| Level | Criteria | Architecture Expectations |
|---|---|---|
| **Simple** | Single application, linear flow, <10 steps, structured data | Single workflow or simple sequence. REFramework optional. Basic error handling. |
| **Medium** | 2-3 applications, branching logic, data transformations, 10-30 steps | REFramework or equivalent. Config.xlsx. Proper error handling. Sub-workflows. |
| **Complex** | Multiple applications, many exception paths, queues, unstructured data, business rules | Dispatcher-Performer. REFramework mandatory. Library extraction. Comprehensive testing. |
| **Advanced** | Multi-actor (RPA + agents + humans), long-running, cross-system orchestration, AI/ML | Maestro/Flow orchestration. Agents for reasoning. Evaluation sets. Full CI/CD. |

### Complexity Mismatch Findings

| Mismatch | Severity | Recommendation |
|---|---|---|
| Simple process with Complex architecture (over-engineered) | Info | Simplify — remove unnecessary REFramework, queues, or libraries |
| Complex process with Simple architecture (under-engineered) | Warning | Add REFramework, proper error handling, config management |
| Advanced process without orchestration layer (Flow/Maestro) | Warning | Add orchestration for multi-actor coordination |
| Agent used for Simple deterministic task | Info | Replace with RPA for cost efficiency and determinism |
| RPA used for Advanced reasoning task | Warning | Replace with agent or hybrid approach |

### Process Mining as Suitability Input

If Process Mining or Task Mining data is available, use it to inform the suitability assessment:

| Data Source | What It Tells You | Review Action |
|---|---|---|
| Process Mining event logs | Actual process flow, variants, bottlenecks, rework loops | Verify the automation matches the actual process (not just the documented ideal) |
| Task Mining recordings | Step-by-step desktop actions, time per step, variation across users | Verify automation covers the most common task variant first |
| Variant analysis | How many different paths exist in the real process | High variation (>10 common variants) = higher complexity classification |
| Automation scoring | Volume × rule-based-ness × stability | Verify scored candidates match the solution's target processes |
| Baseline metrics | Current cycle time, error rate, throughput | Use as benchmark for post-automation comparison |

| Check | Severity | How to Verify |
|---|---|---|
| Process Mining data was used to validate automation scope (if available) | Info | Ask if mining was performed during discovery |
| Baseline metrics recorded before automation (cycle time, error rate) | Info | Check for pre-automation measurement |
| Automation targets the highest-volume, lowest-variation process paths | Info | Compare automation scope to mining variant analysis |

## 3. Environment Separation Review

Verify that the solution has proper environment isolation for safe deployment.

### Environment Existence

| Check | Severity | How to Verify |
|---|---|---|
| Separate environments exist: Development, Test/QA, UAT, Production | Warning | Ask user or check Orchestrator folder structure |
| Each environment has its own Orchestrator folder | Warning | Check folder configuration |
| Configuration differs per environment (URLs, paths, credentials) | Warning | Check config.json or asset management |
| Deployment follows a promotion path (Dev → Test → UAT → Prod) | Info | Ask user about deployment process |

### Configuration Isolation

| Check | Severity | How to Verify |
|---|---|---|
| No production URLs or paths in development code | Warning | Grep for production domain names in project files |
| Credentials are environment-specific (not shared across environments) | Critical | Check credential asset configuration |
| Queue names differ per environment OR use folder isolation | Warning | Check queue naming or folder strategy |
| Assets are folder-scoped (not global) for environment isolation | Warning | Check asset folder assignments |
| Config.json or solution configuration supports environment overrides | Info | Check configuration structure |

### Deployment Safety

| Check | Severity | How to Verify |
|---|---|---|
| Rollback plan documented (how to revert to previous version) | Info | Check documentation or deployment procedures |
| Version pinning used in production (not "latest") | Warning | Check process version configuration |
| CI/CD pipeline enforces tests before production deployment | Info | Check pipeline configuration |
| Change approval process exists for production deployments | Info | Ask user about governance |

## 4. Architecture Principles Scoring

Score each principle on a 1-5 scale. Report scores in the review.

### Modularity (1-5)

| Score | Criteria |
|---|---|
| 1 | Monolithic: all logic in one workflow, no separation of concerns |
| 2 | Some separation: Main.xaml delegates a few tasks, but workflows are still large |
| 3 | Adequate: workflows have clear responsibilities, some reuse |
| 4 | Good: clean separation, libraries for shared logic, testable components |
| 5 | Excellent: fully modular, library-based, independently testable, documented interfaces |

**How to assess:** Count workflows, check responsibilities, look for library usage, check for duplicated logic.

### Scalability (1-5)

| Score | Criteria |
|---|---|
| 1 | Sequential processing, no queue support, single robot only |
| 2 | Sequential but could support multiple robots with minor changes |
| 3 | Queue-based processing OR supports multiple robots |
| 4 | Dispatcher-Performer with queue, supports horizontal scaling |
| 5 | Elastic scaling, cloud robots, load-balanced queue processing, performance-optimized |

**How to assess:** Check for queue usage, Dispatcher-Performer pattern, robot configuration, batch processing.

### Resilience (1-5)

| Score | Criteria |
|---|---|
| 1 | No error handling, no retry logic, crashes on first failure |
| 2 | Basic Try-Catch, but no retry, no transaction recovery |
| 3 | REFramework or equivalent retry logic, basic exception handling |
| 4 | Proper Business/System exception distinction, circuit breaker, recovery procedures |
| 5 | Full resilience: retry with backoff, circuit breaker, graceful degradation, self-healing selectors |

**How to assess:** Check exception handling, retry configuration, REFramework compliance, recovery workflows.

### Maintainability (1-5)

| Score | Criteria |
|---|---|
| 1 | No naming conventions, no documentation, no version control |
| 2 | Some naming conventions, minimal documentation |
| 3 | Consistent naming, Config.xlsx, basic documentation, version control |
| 4 | Clean code, well-documented, tested, easy to onboard new developers |
| 5 | Fully documented, comprehensive tests, CI/CD, code review process, activity annotations |

**How to assess:** Check naming conventions, Config.xlsx usage, test coverage, documentation, git history.

### Security (1-5)

| Score | Criteria |
|---|---|
| 1 | Hardcoded credentials, plaintext passwords, no access control |
| 2 | Some credentials in assets, but inconsistent |
| 3 | All credentials in Orchestrator assets, SecureString used |
| 4 | External credential store, least-privilege robot accounts, no PII in logs |
| 5 | Full security: vault integration, encrypted queues, audit trails, PII masking, compliance-ready |

**How to assess:** Check credential storage, SecureString usage, log content, queue encryption, access controls.

### Governance (1-5)

| Score | Criteria |
|---|---|
| 1 | No process documentation, no monitoring, no approval workflow |
| 2 | Basic PDD exists, some monitoring |
| 3 | PDD and SDD, Orchestrator monitoring, change management |
| 4 | CoE standards followed, Automation Ops policies, CI/CD pipeline |
| 5 | Full governance: CoE oversight, approval workflows, audit compliance, automation inventory, KPI tracking |

**How to assess:** Check documentation, monitoring dashboards, Automation Ops policies, deployment procedures.

## 5. Non-REFramework State Machine Assessment

For projects using State Machine layout outside of REFramework:

| Check | Severity | How to Verify |
|---|---|---|
| Each state has a single, clear responsibility | Warning | Read state names and entry actions |
| All states have at least one outgoing transition | Critical | Check for dead-end states |
| Default transition defined for each state (prevents runtime hangs) | Warning | Check for unhandled transition conditions |
| No infinite cycles without exit conditions | Critical | Trace state transitions — verify every cycle has an exit |
| Entry and exit actions are lightweight (heavy logic in transitions or sub-workflows) | Info | Check entry/exit action complexity |
| State names are descriptive (not "State1", "State2") | Info | Review state naming |
| Final State is reachable from every state through some transition path | Critical | Trace reachability to Final State |
