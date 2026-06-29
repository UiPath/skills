# Jira Activities

Activities from the classic `UiPath.Jira.Activities` package for automating Atlassian Jira from a UiPath workflow. Every Jira operation runs inside a **Jira Scope** (`UiPath.Jira.Activities.JiraApplicationScope`) that opens an authenticated REST session against a Jira instance; child activities — Get Issue, Search Issues, Create Issue, Add Comment, Update Issue, etc. — run against that session over the Jira REST API.

## How Jira Scope Executes

`Jira Scope` builds a REST client from its connection properties, authenticates once at scope open, and exposes the session to child activities:

1. Read `Server URL`, `Authentication Type`, and the matching credential properties from the scope.
2. Build the underlying HTTP/REST client (the classic pack uses **RestSharp**) and authenticate against `<Server URL>/rest/api/...`.
3. Child activities issue REST calls on the open session and deserialize the JSON responses into UiPath types.
4. Close the session at end of scope.

Three properties of this model drive most failures:

- **Authentication is brokered by Atlassian, not UiPath.** The scope only forwards the credential you configured. Atlassian decides whether basic password auth is allowed (it is not, under enforced MFA/SSO), whether the username is a valid identity (Jira Cloud expects the **account email**, not the alphanumeric `accountId`), and whether the `Api Token` is well-formed. A rejected credential surfaces as `Authentication information is invalid`, regardless of which sub-cause produced it.
- **The pack targets Jira Cloud's REST shape.** The classic package is built and tested against Jira **Cloud** (`https://<your-domain>.atlassian.net`). A wrong/over-specified `Server URL` (a dashboard/project path appended) or an on-premises **Server / Data Center** instance can return HTML, a `500`, or a body the pack cannot parse — surfacing as `Response was not recognized as JSON` or an HTTP `5xx`.
- **The pack carries its own legacy dependencies.** `UiPath.Jira.Activities` pins specific versions of transitive libraries (notably **RestSharp**). When another package in the same project pins a different RestSharp, the assembly the workflow loads at runtime no longer matches the reference, and the activity fails to load — `This activity is either missing or could not be loaded properly` at design time, or a `FileLoadException` / `TypeLoadException` at runtime.

## Key Activities

- **Jira Scope** (`UiPath.Jira.Activities.JiraApplicationScope`) — authenticate and host all child Jira activities. Properties: `Server URL`, `Authentication Type` (`Api Token` / `Basic` / `OAuth 2.0`), `Username`, `Api Token` (`SecureString`), `Password` (`SecureString`), `Client Id`, `Client Secret`.
- **Get Issue / Search Issues / Get Issues by JQL** — read issues from the open session.
- **Get Transitions** — list the transitions legal from an issue's **current** status, with each transition's runtime `Id`, `name`, and required screen fields. Drive `Transition Issue` from this rather than a hardcoded ID.
- **Create Issue / Update Issue / Add Comment / Transition Issue** — write operations against the open session. `Add Comment` (`UiPath.Jira.Activities.AddComment`) takes an `IssueKey` (full `PROJECT-NNN` key), the comment `Text`, and optional `Visibility` (type + value); it must run inside a Jira Scope.

## Common Failure Patterns

- **`Authentication information is invalid. Please check your credentials...`** — Atlassian rejected the credential at scope open. Sub-causes: the `Api Token` was passed as a plain `String` instead of a `SecureString`; the `Username` is an alphanumeric Jira `accountId` instead of the account email; leftover `Client Id` / `Client Secret` from a different auth method conflict with `Authentication Type = Api Token`; or basic password auth is used on an org that enforces MFA/SSO (Atlassian blocks password auth — an API token is required).
- **`Response was not recognized as JSON` / HTTP `500`** — structural / routing problem, not a credential problem. The `Server URL` points past the root instance (e.g. ends in `/secure/Dashboard.jspa` or a project path) so the REST call hits an HTML page; or the target is an on-premises **Server / Data Center** instance whose endpoints diverge from the Cloud shape the pack expects.
- **`This activity is either missing or could not be loaded properly`** — dependency conflict. The legacy pack's transitive **RestSharp** (or similar) version is overridden by another package in the project, so the activity assembly cannot bind. Surfaces at design time in Studio, or at runtime as a `FileLoadException` / `TypeLoadException`.
- **`Transition Issue` rejected** — moving a ticket to a new status fails because the UiPath config does not match the active Jira workflow: a required transition-screen field was not supplied (`Field '<name>' is required`), a hardcoded transition ID is not legal from the issue's current status (`Transition '<id>' is not valid ...`), a workflow Condition/Validator or missing permission blocks the robot account, or an older pack version hits the `Atlassian.Jira.IssueFieldEditMetadataOperation` deserialization bug. Resolve transition IDs and required fields dynamically with `Get Transitions`.
- **`Add Comment` fails to post** — the activity is outside a Jira Scope, the `IssueKey` is missing its project prefix (`Issue Not Found` / `404`), the account authenticated but lacks the **Add Comments** permission in that project (`403 Forbidden`), or the comment `Visibility` names a group/project role that does not exist or the account is not in (`400`). Leave `Visibility` blank for a public comment.

## Package

NuGet: `UiPath.Jira.Activities`

The classic pack targets Jira Cloud and carries legacy transitive dependencies. For new work, or when a dependency conflict cannot be resolved, prefer the **Integration Service** Jira connector activities, which use a managed OAuth connection instead of an in-workflow scope. See the [package documentation](https://docs.uipath.com/activities/other/latest/jira/about-the-jira-activities-pack).
