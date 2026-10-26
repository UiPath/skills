> when: explaining UiPath platform hierarchy, robot types, folder types, or asset types

## Key Concepts

### UiPath Platform Hierarchy

```
Organization
  └── Tenant(s)
        └── Folder(s)              ← Orchestrator folders (logical containers)
              ├── Processes         ← Published automation packages
              ├── Assets            ← Key-value configuration (Text, Bool, Integer, Credential, Secret)
              ├── Queues            ← Work item queues for distributed processing
              ├── Jobs              ← Running/completed process executions
              ├── Triggers          ← Event-based or queue-based job triggers
              ├── Schedules         ← Time-based job scheduling (cron)
              ├── Storage Buckets   ← File storage for automation data
              ├── Machines          ← Robot execution environments
              └── Robots            ← Attended/Unattended execution agents
```

### Robot Types

| Type           | Description                                                        | Use Case                                                 |
| -------------- | ------------------------------------------------------------------ | -------------------------------------------------------- |
| **Attended**   | Runs alongside a human user, triggered via UiPath Assistant        | Front-office tasks, user-assisted automation             |
| **Unattended** | Runs autonomously in virtual environments, managed by Orchestrator | Back-office tasks, scheduled processing, 24/7 operations |

### Folder Types

| Type              | Description                                  |
| ----------------- | -------------------------------------------- |
| **Standard**      | Default folder for organizing automations    |
| **Personal**      | User-specific workspace                      |
| **Virtual**       | Logical grouping without physical separation |
| **Solution**      | Folder created by solution deployment        |
| **DebugSolution** | Debug variant of a solution folder           |

### Asset Types

| Type                     | Description                |
| ------------------------ | -------------------------- |
| **Text**                 | Plain text value           |
| **Bool**                 | Boolean (true/false)       |
| **Integer**              | Numeric integer value      |
| **Credential**           | Username + password pair   |
| **Secret**               | Encrypted secret value     |
| **DBConnectionString**   | Database connection string |
| **HttpConnectionString** | HTTP connection string     |
| **WindowsCredential**    | Windows credential pair    |
