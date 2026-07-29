# Scenario: web-http-proxy-blocked

Replays unattended job `7b2e1c04-9f3a-4d21-8c6e-2a5f9b1d3e40` (`PaymentGatewaySync`).
Fault: `System.Net.WebException: The remote server returned an error: (407) Proxy Authentication Required.` in HTTP Request (HttpClient) on a POST to an external endpoint. Maps to `web-activities/playbooks/http-request-proxy-blocked.md`.

The discriminating signal is **environment**: the process runs fine from Studio on the developer's laptop but faults only on the scheduled **unattended robot** on the corporate server network. The `407` means the corporate proxy is in the path but the robot's request carries no proxy credentials (the Web activities expose no proxy property and don't pick up the interactive user's system proxy under a service account). The fix is to route the robot's HTTP egress through the proxy with credentials — NOT a DNS/TLS fix, a wrong-endpoint fix, or an auth fix on the target API.

Fixtures hand-authored in the faithful-replay shape (scrubbed: host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/PaymentGatewaySync/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
