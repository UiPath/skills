# Platform Resources Review Checklist

Quality checklist for UiPath Orchestrator resources — assets, queues, storage buckets, folders, processes, and scheduling.

## 1. Folder Organization

### Structure Quality

| Check | Severity | How to Verify |
|---|---|---|
| Modern folders used (not classic folders) | Warning | `uip or folders list --output json` |
| Folder hierarchy is logical (by department, process, or environment) | Info | Review folder structure |
| Folder nesting depth <=4 levels (performance degrades beyond this) | Warning | Check nesting depth |
| Folder names are descriptive and consistent | Info | Review naming patterns |
| No orphan folders (empty, unused folders) | Info | Check folder contents |
| Account not assigned to >1000 folders (performance limit) | Warning | Check folder assignments |

### Access Control

| Check | Severity | How to Verify |
|---|---|---|
| Access permissions follow least-privilege principle | Warning | Review folder role assignments |
| Attended and unattended robots have separate appropriate access | Warning | Check robot-folder assignments |
| No overly broad access (e.g., everyone has admin on all folders) | Warning | Review permission model |
| Service accounts have only necessary permissions | Warning | Check service account roles |

## 2. Asset Management

### Naming and Organization

| Check | Severity | How to Verify |
|---|---|---|
| Assets follow consistent naming convention | Warning | `uip resource assets list <FOLDER_ID> --output json` |
| Recommended pattern: `[Department]_[Process]_[AssetName]` | Info | Review asset names |
| No duplicate asset names in the same folder | Warning | Check for duplicates |
| Asset descriptions populated | Info | Check description fields |
| Assets organized in appropriate folders | Info | Review folder placement |

### Type Appropriateness

| Asset Content | Correct Type | Flag If Wrong Type |
|---|---|---|
| Passwords, API keys | `Credential` or `Secret` | **Critical** if using `Text` |
| Database connection strings | `DBConnectionString` | **Warning** if using `Text` |
| HTTP endpoints with auth | `HttpConnectionString` | **Warning** if using `Text` |
| Windows login credentials | `WindowsCredential` | **Critical** if using `Text` |
| Feature flags, settings | `Bool` or `Text` | Fine |
| Numeric thresholds | `Integer` | **Info** if using `Text` |
| General configuration | `Text` | Fine |

### Security

| Check | Severity | How to Verify |
|---|---|---|
| Sensitive values use `Credential`/`Secret` type (NOT `Text`) | Critical | Check asset types for sensitive data |
| Per-robot values used only when robots genuinely need different values | Info | Check per-robot configuration |
| Credential Store configured for external vault (CyberArk, Azure Key Vault, etc.) | Info | Check credential store settings |
| Different credential store configs per tenant (isolation) | Info | Check store configuration |
| No plaintext credentials visible in asset values | Critical | Review asset values |
| Cross-folder asset sharing is intentional (linked assets) | Warning | Check linked assets |

## 3. Queue Configuration

### Queue Setup

| Check | Severity | How to Verify |
|---|---|---|
| Queue names follow consistent convention | Warning | `uip resource queues list <FOLDER_ID> --output json` |
| Recommended pattern: `[Department]_[Process]_QueueName` | Info | Review queue names |
| Max retries configured (1-50, typically 3) | Warning | Check max retry setting |
| Auto-retry enabled for application exceptions | Warning | Check auto-retry setting |
| Unique reference configured (if duplicate detection needed) | Info | Check unique reference setting |
| Queue description populated | Info | Check description field |
| Encryption enabled for sensitive data | Warning | Check encryption setting |

### Queue Item Design

| Check | Severity | How to Verify |
|---|---|---|
| Specific Data uses primitive types only (Number, Boolean, String, DateTime) | Warning | Check queue item schemas |
| No colons, periods, commas, or @ in argument names | Critical | Review field names |
| Reference field used for linking to external systems | Info | Check reference usage |
| Priority levels used appropriately (Low/Normal/High) | Info | Check priority distribution |
| JSON schemas uploaded for validation (if available) | Info | Check schema configuration |
| No sensitive data in unencrypted queue items | Critical | Review data content |

### SLA and Monitoring

| Check | Severity | How to Verify |
|---|---|---|
| SLA configured for time-sensitive queues | Info | Check SLA settings |
| Deadline/Due Date used for urgent items | Info | Check item configurations |
| Retention policy configured (not relying on defaults) | Info | Check retention settings |
| Completed items retention: 1-180 days (default 30) | Info | Check completed retention |
| Uncompleted items retention: 30-540 days (default 180) | Info | Check uncompleted retention |

### Queue Triggers

| Check | Severity | How to Verify |
|---|---|---|
| Queue trigger configured for performer process | Warning | Check trigger settings |
| Maximum concurrent jobs set appropriately | Warning | Check scaling config |
| Trigger process matches the performer process | Critical | Verify process reference |
| Dynamic allocation enabled (if using machine templates) | Info | Check allocation mode |

## 4. Storage Buckets

| Check | Severity | How to Verify |
|---|---|---|
| Bucket names are descriptive | Info | Review bucket names |
| Appropriate storage provider configured | Info | Check provider settings |
| Access permissions restrict to necessary processes | Warning | Check bucket permissions |
| Cleanup/archival policy defined for temporary files | Info | Check lifecycle policies |
| No sensitive files stored without encryption | Warning | Review bucket contents |
| Bucket organized logically (not a catch-all dump) | Info | Review file organization |

## 5. Process Configuration

### Process Settings

| Check | Severity | How to Verify |
|---|---|---|
| Process version pinned (not using "latest" in production) | Warning | Check process version |
| Correct runtime type (Attended vs Unattended) | Critical | Check runtime settings |
| Machine template assigned appropriately | Warning | Check machine assignment |
| Background processes on appropriate machines (Linux if possible) | Info | Check machine type |
| Input arguments documented | Info | Check argument descriptions |
| Process description populated | Info | Check description |

### Scheduling

| Check | Severity | How to Verify |
|---|---|---|
| Time triggers use appropriate CRON expressions | Warning | Review schedule configuration |
| Triggers spaced at least 1 minute apart | Warning | Check trigger timing |
| Overlap handling configured (what happens if previous run hasn't finished) | Warning | Check overlap settings |
| Non-working days/hours considered in scheduling | Info | Check schedule appropriateness |
| Queue triggers preferred over time triggers when work is event-driven | Info | Review trigger type choice |

### Auto-Disable Awareness

Note: Orchestrator auto-disables triggers after 10 consecutive failed launches without a success in 24 hours. This is a platform behavior to be aware of during review.

## 6. Robot and Machine Management

| Check | Severity | How to Verify |
|---|---|---|
| Machine templates used (not individual machine configs) | Info | Check machine configuration |
| Templates restricted to appropriate process types | Info | Check template assignments |
| Robot licenses utilized efficiently | Info | Check license usage |
| Attended robots assigned to appropriate users | Warning | Check robot-user mapping |
| Unattended robots have dedicated service accounts | Warning | Check robot accounts |
| High-density robots configured where appropriate | Info | Check robot density settings |

## 7. Tags and Organization

| Check | Severity | How to Verify |
|---|---|---|
| Consistent tagging taxonomy used | Info | Review tags across resources |
| Tags applied to assets, processes, queues, and machines | Info | Check tag coverage |
| Tag labels follow naming conventions | Info | Review tag names |
| Key-value tags used for structured categorization (e.g., `Department: Finance`) | Info | Check tag types |

## 8. Monitoring and Alerting

| Check | Severity | How to Verify |
|---|---|---|
| Monitoring dashboards configured for critical processes | Warning | Check Insights/monitoring setup |
| Alerts configured for job failures | Warning | Check alert settings |
| Queue SLA monitoring enabled for time-sensitive queues | Info | Check SLA monitoring |
| Machine availability monitoring enabled | Info | Check machine monitoring |
| Alert thresholds appropriate (not too sensitive, not too loose) | Info | Review threshold values |

## 9. CI/CD and DevOps

| Check | Severity | How to Verify |
|---|---|---|
| Solution packaging used for deployment (not manual publish) | Warning | Check deployment method |
| CI/CD pipeline configured (Azure DevOps, Jenkins, GitLab) | Info | Check pipeline configuration |
| Automated tests included in pipeline | Info | Check test stage |
| Environment promotion path defined (dev → staging → prod) | Info | Check environment strategy |
| Configuration separated from code (config.json or solution configuration) | Warning | Check configuration management |
| Deployment versioning tracked | Warning | Check version history |

## 10. Governance Compliance

### Automation Ops Policies

| Check | Severity | How to Verify |
|---|---|---|
| Governance policies deployed and active | Warning | Check Automation Ops → Policies for active policies |
| Studio policies enforce Workflow Analyzer before publish | Warning | Check Studio policy → "Require analysis before publish" |
| Studio policies restrict package sources to approved repositories | Warning | Check Studio policy → Package Management |
| Studio policies restrict Git repositories to approved sources | Info | Check Studio policy → Source Control |
| Robot policies enforce Runtime Analyzer rules | Info | Check Robot policies for RT-UIA-001 and RT-OUT-001 |
| Policy deployment at correct scope (Tenant → Group → User hierarchy) | Info | Review policy deployment levels — more specific scopes override broader ones |
| Activity restrictions configured (block risky activities in StudioX) | Info | Check Studio policy → Activity restrictions |

### Runtime Analyzer Rules

| Rule ID | Rule | What It Controls |
|---|---|---|
| RT-UIA-001 | App/URL Restrictions | Controls which apps and URLs robots can automate at runtime. Configurable: `whitelistApps`, `whitelistUrls`, `blacklistApps`, `blacklistUrls`. Supports wildcards (`*`, `?`). |
| RT-OUT-001 | Email Blocklist | Prevents sending emails to restricted addresses. Applies to Mail, Microsoft 365, Google Workspace packages. Blocks send, reply, forward. |

### AI Trust Layer Configuration

| Check | Severity | How to Verify |
|---|---|---|
| AI Trust Layer enabled and configured | Warning | Check Automation Ops → AI Trust Layer |
| Unnecessary product toggles disabled (least privilege) | Warning | Review 12 product toggles — disable what the org does not use |
| Trace TTL configured per compliance (1, 7, or 30 days) | Warning | Check TTL enforcement setting |
| Input/output audit saving enabled | Warning | Check prompt/completion storage visibility |
| PII protection configured (pseudonymization before models) | Warning | Check PII masking settings |
| Third-party AI model usage scoped to correct tenant/group/user | Info | Check policy deployment scope |

### Audit and Compliance

| Check | Severity | How to Verify |
|---|---|---|
| Audit logging enabled at organization and tenant level | Warning | Check audit settings |
| Credential assets use external vault (CyberArk, Azure Key Vault, HashiCorp) | Info | Check credential store config |
| Encryption at rest (AES-256) and in transit (TLS 1.2) | Warning | Verify security settings |
| Data residency requirements met (correct server region) | Critical | Check tenant region |
| PII masking configured for AI-related features (AI Trust Layer) | Warning | Check PII masking settings |
| Audit trail retention meets compliance requirements (minimum 6 months for EU AI Act) | Warning | Check retention settings |

### Security Hardening

| Check | Severity | How to Verify |
|---|---|---|
| Firewall configured with DNS domain allowlists for UiPath URLs | Warning | Check firewall rules |
| IP restriction configured for Orchestrator access | Info | Check IP restriction settings |
| VPN gateway configured for cloud robots accessing on-premises resources | Info | Check VPN settings |
| Service accounts follow least-privilege principle | Warning | Review account permissions |
| Different credential store configs per tenant (isolation) | Info | Check store configuration |
| No plaintext credentials in any configuration | Critical | Audit all config files |

### Capacity Planning (Large Deployments)

For deployments with >50 robots:

| Check | Severity | How to Verify |
|---|---|---|
| SQL connection pool increased (Max Pool Size >=500 for 200+ robots) | Warning | Check connection string |
| Elasticsearch configured for log storage (>300 robots: only Error/Critical in SQL) | Warning | Check logging config |
| Multi-node Orchestrator behind load balancer (>500 robots) | Warning | Check infrastructure |
| Redis configured for session state and SignalR (multi-node) | Warning | Check Redis config |
| Robot NLog uses async wrapper for non-blocking writes | Info | Check NLog config |
| Queue throughput limits considered (1MB Specific Data limit) | Warning | Check queue item sizes |

## 11. Integration Service

### Connection Management

| Check | Severity | How to Verify |
|---|---|---|
| Pre-built connectors used instead of custom HTTP requests where available | Info | Check for HTTP Request activities that duplicate connector functionality |
| Connections use service accounts (not personal credentials) | Warning | Check connection authentication — service accounts preferred |
| Credentials rotated on regular schedule | Warning | Check credential expiration and rotation policy |
| Environment-specific connections configured (Dev/Test/Prod) | Warning | Verify connections point to correct environment endpoints |
| Only shared connections used (not individual) for agent-accessible tools | Warning | Check connection sharing settings |

### Trigger Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Event triggers filtered to relevant events only (not triggering on everything) | Warning | Check trigger event filter configuration |
| Triggered automations are idempotent (handle duplicate events safely) | Warning | Check for deduplication logic in triggered processes |
| Dead letter handling configured for failed trigger processing | Info | Check for error handling on trigger failures |
| Trigger firing rates monitored | Info | Check monitoring configuration |

### API Usage Patterns

| Check | Severity | How to Verify |
|---|---|---|
| API rate limits respected with retry logic (handle 429 Too Many Requests) | Warning | Check for retry/backoff on API calls |
| Batch operations used instead of looping single API calls | Warning | Check for single-item API calls inside loops |
| API errors handled explicitly (401 Unauthorized, 429, 500) | Warning | Check error handling around connector activities |

## 12. Data Fabric

### Entity Design

| Check | Severity | How to Verify |
|---|---|---|
| Entities model real business objects (Invoice, Customer, Order — not generic "Data") | Warning | Review entity names and field structure |
| Field types match the data they store (DateTime for dates, Decimal for money — not all String) | Warning | Check field type definitions |
| Relationships defined between related entities (One-to-Many, Many-to-Many) | Info | Check for Reference fields connecting entities |
| Unique constraints prevent duplicate records (e.g., InvoiceNumber) | Warning | Check unique field configuration |
| Fields used in frequent queries are indexed | Info | Check field indexing |

### Data Quality

| Check | Severity | How to Verify |
|---|---|---|
| Automations validate data before inserting into Data Fabric | Warning | Check for validation logic before `Create Entity Record` |
| Null values handled in queries and automations | Warning | Check for null handling in Data Fabric queries |
| Data retention policy defined (archival/cleanup of old records) | Info | Check data lifecycle management |
| Data Fabric used instead of Excel/CSV for shared cross-process data | Info | Check if Excel files are used where Data Fabric would be more appropriate |

## 13. Monitoring and Alerting Strategy

### Job Monitoring

| Check | Severity | How to Verify |
|---|---|---|
| Alerts configured for job failures | Warning | Check Orchestrator alert settings |
| SLA monitoring configured for time-sensitive processes | Warning | Check SLA threshold configuration |
| Queue backlog alerts configured | Warning | Check queue monitoring thresholds |
| License exhaustion alerts configured | Info | Check license usage monitoring |
| Log forwarding configured to centralized SIEM (Splunk, ELK, Azure Monitor) | Info | Check log forwarding settings |

### Logging Strategy

| Check | Severity | How to Verify |
|---|---|---|
| Log levels appropriate per environment (DEV=Trace, PROD=Info) | Warning | Check robot log level configuration |
| Custom business-level logs included (not just activity-level) | Info | Check for `Add Log Fields` and custom log messages |
| Sensitive data excluded from logs (PII, credentials) | Critical | Review log message content |

### Disaster Recovery

| Check | Severity | How to Verify |
|---|---|---|
| Orchestrator configuration backed up | Warning | Check backup procedures |
| Rollback procedures documented and tested | Warning | Check disaster recovery documentation |
| High availability configured for critical deployments | Info | Check HA infrastructure |
| Runbooks documented for incident response | Info | Check operational runbooks |

## 14. Queue Operations Depth

### Queue Item SpecificData Size

| Check | Severity | How to Verify |
|---|---|---|
| Queue item SpecificContent size < 1 MB (hard cap on Cloud, recommended cap on-prem) | Warning | Query queue items via API and check SpecificContent byte size. Grep workflow code for `Add Queue Item` where input is built from file reads, DataTable serialization, or Base64 encoding |
| Large payloads stored externally (Storage Bucket / DB) with only a reference in the queue item | Warning | Check queue item schemas for Base64 fields or large JSON blobs |

### Queue Priority Distribution

| Check | Severity | How to Verify |
|---|---|---|
| Queue priorities are distributed (not >90% High priority) | Warning | Query queue items grouped by Priority — if everything is High, priority has no effect |
| SLA prediction awareness (SLA predictions auto-set items to High priority) | Info | Check if SLA predictions are enabled on the queue — if so, confirm this is intentional |

### Queue Retention

| Check | Severity | How to Verify |
|---|---|---|
| Queue retention configured per volume (not relying on defaults for high-volume queues) | Warning | For queues with >1000 items/day, retention >30 days = database bloat. Check QueueItems row count |
| Queue retention policy explicitly documented per queue | Info | Check queue configuration |

## 15. Trigger / Schedule Antipatterns

| Check | Severity | How to Verify |
|---|---|---|
| Time triggers not clustered on same cron minute (avoids job-creation spike) | Warning | Export all triggers, parse cron, flag >5 triggers firing within the same minute |
| Trigger auto-disable is monitored (Orchestrator disables trigger after 10 consecutive failures without success in 24h) | **Critical** | Check audit logs for "System Administrator deactivated trigger" events. Configure alert on trigger state changes |
| Event-driven work uses queue triggers / Integration Service triggers (not time-based polling) | Info | Triggers that start with "check for new items" and exit immediately are polling — prefer event-based |
| Queue trigger configuration appropriate (minimum items, max concurrent jobs) to avoid ghost job spawns | Info | Check trigger config: `Minimum items to trigger first job`, `Maximum pending and running jobs` |

## 16. Asset and Credential Operations

### Credential Rotation

| Check | Severity | How to Verify |
|---|---|---|
| Credential expiry tracking in place (Orchestrator has no built-in expiry field) | **Critical** | Check for external credential store (CyberArk, Azure Key Vault) or companion tracking asset/documentation. AD password rotation (60-90 days) causes bot failure + account lockout if not tracked |
| Credential assets do NOT have name collisions across folders pointing to the same credential store entry | **Critical** | List credentials across folders via API; flag pairs where both Name and ExternalName match across different folders (password change in one silently changes all) |

### Asset Retrieval Efficiency

| Check | Severity | How to Verify |
|---|---|---|
| `Get Asset` / `Get Credential` NOT called in tight loops (use `CacheStrategy = Execution` if unavoidable) | Warning | Grep workflows for `GetAsset` / `GetCredential` inside `ForEach` / `While`. Each call = HTTP round-trip (hits rate limits on 10K+ item queues) |
| Per-robot asset values assigned for all production robots (not just dev robot) | Warning | For per-robot assets, verify values exist for every robot in the deployment folder |

## 17. Deployment and Publishing

| Check | Severity | How to Verify |
|---|---|---|
| Production packages NOT published directly from Studio (CI/CD bypass) | **Critical** | Check Orchestrator audit logs for `Package.Create` events where source is Studio (not a CI/CD service account) |
| Production packages use `Strict` runtime rule (not `Lowest Applicable Version`) for core activity packages | Warning | Parse published `.nupkg` project.json → dependencies runtime rule. `Strict` for UiPath.System, UiPath.UIAutomation, etc. |
| Workflow Analyzer enforced before publish (governance policy) | Warning | Check Automation Ops Studio policy → "Require analysis before publish". Verify `project_analysis_results.json` is present in published `.nupkg` |

## 18. Robot / Machine Configuration

| Check | Severity | How to Verify |
|---|---|---|
| Multiple unattended robots NOT sharing the same Windows user credentials on same machine | **Critical** | Check robot-machine-user mappings. Windows Desktop only supports one interactive session; even on Windows Server, same user = session conflicts. `Kill Process` with default `AppliedTo=All` terminates across ALL user sessions |
| Machine template runtime reservations sized to actual peak concurrency (not oversized) | Warning | Compare allocated runtimes vs peak concurrent jobs per machine. Allocated > 2× peak = idle license waste that blocks other folders/processes |

## 19. Monitoring Infrastructure Health

| Check | Severity | How to Verify |
|---|---|---|
| Orchestrator webhooks monitored for circuit-breaker open state | **Critical** | Circuit breaker opens after repeated failures; events during outage are PERMANENTLY LOST (not retried). After 7 days >50% failure, webhook auto-disabled. Check audit logs for webhook state changes |
| Log forwarding change awareness (switching SQL ↔ Elasticsearch makes historical logs invisible in UI) | Warning | Check `Logs.RobotLogs.ReadTarget` config changes; only one destination is queried at a time — historical logs in the other store vanish from UI |

## 20. Security Boundaries

| Check | Severity | How to Verify |
|---|---|---|
| Folders NOT relied on as hard security boundaries (cross-folder access is possible via `OrchestratorFolderPath` argument) | **Critical** | Grep project source for `OrchestratorFolderPath` / `FolderPath` arguments in Orchestrator activities. Any process referencing a folder outside its deployment folder = bypass potential. True isolation requires separate tenants |
| Integration Service connections scoped per environment (NOT shared across Dev/Test/Prod) | **Critical** | List IS connections by folder; flag same connection ID referenced from Dev and Prod folders. Dev runs could hit prod systems |
| Integration Service OAuth token expiry monitored (refresh tokens expire after 60 days of inactivity) | Warning | Check connection status via IS API. Look for `Status != Connected` or stale `lastAuthenticatedAt`. Expired refresh = silent 401s until manual re-auth |
