# UiPath Admin — Key Concepts

> when: you need the identity/organization model — the org hierarchy, or how robot accounts differ from external apps and from robot credentials.

## Organization hierarchy

```
Organization (org)
  └── Partition (= org in most cases)
        ├── Users           ← human identities
        ├── Groups          ← role containers (BuiltIn + Custom)
        ├── Robot Accounts  ← unattended automation identities
        └── External Apps   ← OAuth2 clients (Client ID + Secret)
```

## Robot accounts vs external apps

| Concept | Purpose | Managed by |
|---|---|---|
| **Robot account** | Identity — who the robot is | Identity Server (`uip admin`) |
| **Robot credentials** | Per-robot Client ID + Secret for machine auth | Orchestrator (machine connection) |
| **External app** | OAuth2 client for API integrations, CI/CD | Identity Server (`uip admin`) |

Robot credentials are provisioned automatically by Orchestrator on machine connect — not by creating external apps.
