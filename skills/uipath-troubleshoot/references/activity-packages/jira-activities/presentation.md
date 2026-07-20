# Jira Activities Presentation Rules

- **Activities** — use the display name (e.g., "Jira Scope", "Get Issue", "Search Issues"), not the fully qualified class name (e.g., `UiPath.Jira.Activities.JiraApplicationScope`)
- **Authentication** — name the mode in the user's terms ("Authentication Type = Api Token", "basic username/password", "OAuth 2.0"), and when the fix is a credential-format correction, state exactly which property is wrong and what it should be (e.g., "`Username` is the account email, not the Jira account ID")
- **Credential values** — never echo a token, password, or secret. Refer to them by property name (`Api Token`, `Password`, `Client Secret`) and data type (`SecureString` vs `String`)
- **Server URL** — when the fix is a URL correction, show both the wrong value (`https://acme.atlassian.net/secure/Dashboard.jspa`) and the corrected root value (`https://acme.atlassian.net`) so the user can see the exact edit
- **Deployment type** — distinguish "Jira Cloud" (`*.atlassian.net`) from "Jira Server / Data Center (on-premises)" explicitly; the classic pack's support boundary depends on it
- **Error strings** — quote the exact message (`Authentication information is invalid. Please check your credentials...`, `Response was not recognized as JSON`, `This activity is either missing or could not be loaded properly`) and any HTTP status (`500`) so the user can correlate it with the Output panel / job log
- **Dependency conflicts** — name the conflicting assembly and the two pinned versions when known (e.g., "`RestSharp` 106.x required by the Jira pack vs 110.x pulled in by ..."), and frame the Integration Service Jira connector as the durable alternative when the conflict cannot be resolved in-project
