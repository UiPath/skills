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

## CLI

```
uip or folders list-current-user                    — list all accessible folders (Personal, Solution, Standard)
uip or folders get <key-or-path>                    — get folder details
uip or jobs list --folder-key <key>                 — list jobs in a folder. Filters: --state, --process-name, --created-after/before, --started-after/before
uip or jobs get <key>                               — job details: state, arguments, timing, machine, errors
uip or jobs logs <key>                              — robot execution logs (--level Error, --limit N). Folder inferred from key.
uip traces spans get --job-key <key>                — job execution traces (activity states, execution path)
uip traces spans get <trace_id>                     — job execution traces based on the 'jobInformation.TraceId' field
uip or jobs history <key>                           — job state transition history (Pending → Running → Faulted, with timestamps)
uip or machines list                                — list registered machines
uip or licenses info                                — license allocation and usage
```

Key commands for diagnostics:
- `uip or folders list-current-user` — resolve folder key first; use this instead of `uip or folders list` to include Personal and Solution folders
- `uip or jobs list --folder-key <key> --state Faulted` — find faulted jobs in a folder. Use `--process-name`, `--created-after/before` to narrow results
- `uip or jobs get <key>` — starting point for any job investigation
- `uip or jobs logs <key> --level Error` — quickly find error entries in execution logs
- `uip traces spans get --job-key <key>` — job execution traces (activity states, execution path)
- `uip traces spans get <trace_id>` — job execution traces based on the 'jobInformation.TraceId' field
- `uip or jobs history <key>` — job state transition history with timestamps

Queue and queue-item commands are documented in the investigation guide's Queue Item Data Bundle section.

