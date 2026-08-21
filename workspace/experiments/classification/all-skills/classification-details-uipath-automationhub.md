# Classification Details — uipath-automationhub

**Classification: Strong**

---

## What the Skill Teaches

Publish and retrieve business processes in UiPath Automation Hub via the Open API, authenticating with the user's cloud bearer token (not an admin OpenAPI token).

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Auth token resolution (3-step priority order)** | **Yes — DETECT** | Fixed priority: env-auth → uip session file → user-provided; each step has an explicit source and fallback |
| 2 | **Header rule enforcement** | **Yes — VALIDATE/CHECK** | Fixed rules: always send Bearer, NEVER send x-ah-openapi-auth; 401 recovery path specified |
| 3 | **Intent routing (publish vs get)** | **Yes — DETECT** | Two-way rule table: publish/create/upload → publish-process.md; get/read/fetch/list → get-process.md |
| 4 | **Publish process to AH (in reference)** | **Yes — TRANSFORM-PIPELINE** | Schema-driven payload fetch → build body → POST to API endpoint; link-based doc attach |
| 5 | **Get process from AH (in reference)** | **Yes — EXTRACT** | Search or id-based GET → parse response → return process + attached documents |

---

## Codifiable Procedures (not yet scripted)

### 1. Auth Token Resolution — DETECT

**Source:** `skills/uipath-automationhub/SKILL.md` §Authentication (shared — both flows)

**What it does:** The skill specifies a three-step priority sequence to resolve the bearer token and org/tenant slugs before any API call: (1) check for `UIPATH_CLI_AUTH_TOKEN` with `UIPATH_CLI_ENABLE_ENV_AUTH=true` and take org/tenant from environment variables; (2) read `~/.uipath/.auth` (JSON) for `accessToken`, `baseUrl`, `organizationName`, `tenantName`; (3) ask the user to paste a cloud bearer token and org/tenant slugs. The Gateway URL is then constructed as `{baseUrl}/{org}/{tenant}/automationhub_/api/v1/openapi`. Line 19: "Resolve the cloud token + base URL + org + tenant in this **priority order**: 1. **Runtime env-auth (preferred)**... 2. **Logged-in `uip` session**... 3. **User-provided (last resort)**."

**Why it's mechanical:** The priority ordering, the exact file path and field names to read (`~/.uipath/.auth`), and the Gateway URL construction formula are all fully specified with no judgment.

**Turn savings:** Without a script, the agent checks each auth source as separate conversational steps and manually constructs the URL; a single auth-resolution script collapses all three checks and URL assembly into one call.

---

### 2. Header Rule Validation — VALIDATE/CHECK

**Source:** `skills/uipath-automationhub/SKILL.md` §Authentication → Header rules

**What it does:** The skill prescribes strict header rules for every API call: always include `Authorization: Bearer <token>` and `Content-Type: application/json` on POSTs; never include `x-ah-openapi-auth` or `x-ah-openapi-app-key`. On 401, if the token came from `~/.uipath/.auth`, the recovery path is to tell the user to `uip login` again, re-resolve, and retry. Line 35: "**NEVER** send `x-ah-openapi-auth` or `x-ah-openapi-app-key`. Those route to the admin-token path and reject a cloud token with **401** — never add them to 'fix' a 401."

**Why it's mechanical:** The header inclusion rules and the 401 recovery path are binary and fixed; there is no judgment about when or how to apply them.

**Turn savings:** Embedding header validation into an API call wrapper ensures the rules are applied consistently without the agent reasoning through them each time.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Every teaching area in the SKILL.md is codifiable — the auth resolution priority order, the header rules, the intent routing table, and (in the referenced flow files) the publish and get operations. The skill's SKILL.md itself is almost entirely composed of codifiable rules and pipelines; there is no judgment-heavy area that dominates the content.

**Why not None:** The three-step auth resolution priority order and the header rule enforcement are explicit DETECT and VALIDATE/CHECK procedures with no judgment required.

**Evidence locations:**
- Auth token resolution: `SKILL.md` §Authentication (lines 18–24)
- Header rules: `SKILL.md` §Authentication → Header rules (lines 34–39)
- Intent routing: `SKILL.md` §Routing — pick the flow by intent (lines 44–51)
