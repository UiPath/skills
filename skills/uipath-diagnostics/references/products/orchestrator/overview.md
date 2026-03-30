# Orchestrator

Web application that manages automation resources, robots, processes, and execution. Central hub for attended and unattended automation orchestration.

Orchestrator serves as the backbone for:
- **Deployment** — publishing automation packages and managing versions
- **Execution** — starting, stopping, and monitoring automation jobs
- **Configuration** — managing assets, queues, and environment settings
- **Scheduling** — defining triggers and schedules for unattended execution
- **Monitoring** — tracking job status, execution logs, and system health

## Organization Model

```
Organization (cloud.uipath.com)
  └── Tenant                        ← Isolated environment (dev, staging, prod)
        └── Folder                  ← Logical container for resources
              ├── Processes         ← Published .nupkg automation packages
              ├── Jobs              ← Running or completed executions
              ├── Assets            ← Key-value configuration store
              ├── Queues            ← Distributed work item queues
              ├── Triggers          ← Event/queue-based job triggers
              ├── Schedules         ← Cron-based job scheduling
              ├── Storage Buckets   ← File storage for automation data
              ├── Machines          ← Robot execution environments
              └── Robots            ← Attended/Unattended agents
```

## Dependencies

- **Identity Server** — authentication and token management; Orchestrator cannot function without it
- **SQL Server** — stores all Orchestrator data (jobs, queues, assets, audit, configuration)
- **Elasticsearch** (optional) — stores robot execution logs; if unavailable, logs are lost but jobs still run
- **IIS / ASP.NET Core** — hosts the Orchestrator web application
- **Load Balancer / Reverse Proxy** — in clustered deployments, routes traffic and terminates SSL

## Features

- **Robot Management** — Provisioning, configuration, and monitoring of attended and unattended robots
- **Process Execution & Job Management** — Launch and monitor automation jobs with dynamic robot dispatch
- **Queues & Transaction Management** — Work item queue management with priority, state tracking, retries
- **Queue Triggers** — Auto-launch jobs when queue items arrive
- **Scheduled Triggers** — Time-based recurring triggers for unattended execution
- **Folders & Tenants** — Hierarchical org modeling with resource isolation
- **Assets** — Key-value config store (text, int, bool, credential, secret)
- **Machine Management** — Machine objects for robot host tracking
- **Packages Management** — NuGet package repository for automation packages
- **Storage Buckets** — Folder-scoped file storage (Azure, S3, MinIO, FileSystem)
- **Credential Stores** — Pluggable credential providers (Azure Key Vault, HashiCorp)
- **Webhooks** — Event subscriptions with HTTP delivery and HMAC signing
- **OData REST API** — Programmatic API for all Orchestrator entities
- **Role-Based Access Control** — Fine-grained RBAC with default and custom roles
- **Monitoring** — Real-time dashboards for machines, queues, processes (30-day window)
- **Alerts** — In-app notifications, email summaries, custom Raise Alert activity
- **Logs** — Robot execution log capture per folder
- **Audit** — Audit trail of administrative actions for compliance

