# Studio Playbooks

**Overview:** [overview.md](./overview.md) — profiles, license acquisition, Autopilot, tenant-service dependencies, and CLI surface.

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Studio Autopilot Unavailable / "disabled by your organization" | Medium | Studio's developer Autopilot greyed out ("disabled by your organization" / "could not connect to the Autopilot service") or Studio unlicensed ("No license exist for this installation") — caused by required tenant services (`orchestrator`, `autopilotstudio`) being **Disabled**. Also covers the related-but-separate **Autopilot for Everyone** (UiPath Assistant) install returning 404 when its services (`autopilotforeveryone`, `agenthub`, `agentsruntime`, `semanticproxy`, `du`) are disabled | [studio-autopilot-unavailable.md](./playbooks/studio-autopilot-unavailable.md) |
