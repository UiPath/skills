---
name: uipath-gov-aops-policy
description: "UiPath AOps governance — enforce rules (\"block/restrict/require X\") by mapping intent to a Product policy via `uip gov aops-policy`. Create/update/delete/list/deploy policies to users, groups, tenants. For platform ops→uipath-platform."
allowed-tools: Bash, Read, Write, Grep, Glob
---

# UiPath AOps Governance

> **Preview** — skill is under active development; surface and behavior may change.

Skill for managing AOps governance policies and deploying them to users, groups, or tenants via the `uip gov aops-policy` CLI.

> **Terminology.** "AOps" = **Automation Ops** (a.k.a. AutomationOps), UiPath's governance console. An "AOps policy" — managed via `uip gov aops-policy` and this skill — is an **Automation Ops Governance Policy** covering product runtime / design-time behavior (Studio, StudioX, Assistant, Robot, AI Trust Layer, …). This is **distinct from a Governance Access Policy** (identity / role / access control), which this skill does NOT cover.

## When to Use This Skill

Activate on both **explicit policy requests** and **natural-language governance intent** — users rarely say "AOps policy" by name.

**Explicit requests:**
- User asks to create, update, delete, list, or get a governance policy
- User asks to deploy a policy to a user, group, or tenant
- User asks to check the effective (deployed) policy for a user, group, or tenant
- User asks about `uip gov aops-policy` commands
- User asks to configure policy field values for a product

**Governance intent (rule/policy patterns without naming the product):**
- "I want to **block / restrict / disable / disallow** X for my users / team / tenant"
- "I want to **require / enforce / mandate** X"
- "I want to **allow only** X / **limit** users to X"
- "How do I **govern / control / gate** who can do X"
- "Set up a **rule / guardrail / policy** that does X"
- "Users / agents / robots should / should not be able to X"
- "Stop Assistant popping up", "auto-launch Assistant", "disable Marketplace widget" → Assistant policy (see [aops-governance-recipes-guide.md](./references/aops-governance-recipes-guide.md) A-recipes)
- "Only allow automating outlook.exe / excel.exe", "block regedit / cmd.exe", "whitelist internal URLs", "block emails to gmail" → Robot runtime rules RT-UIA-001 / RT-OUT-001 (R-recipes)
- "Enforce analyzer before publish", "require release notes", "whitelist our GitHub repos", "force everyone to include our custom analyzer package (ST-USG-027)" → Studio policy (S-recipes)
- "Hide developer panel in StudioX", "stop citizen devs saving projects locally" → StudioX policy (X-recipes)

These are AOps governance requests — treat them as a `create policy` flow starting at [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md) Step 1, Case B (intent-based product selection). See the intent-mapping examples below to prime product selection, and [aops-governance-recipes-guide.md](./references/aops-governance-recipes-guide.md) for the field mappings behind each recipe.

## Recognize Governance Intent → Pick a Product Policy

When the user expresses a governance rule without naming a product, your job is to map the **intent keywords** to the right **Product policy**. The bootstrap (every product's `form-template-locale-resource.json`) is the source of truth — always rank products by locale-keyword matches (aops-policy-manage-guide Step 1, Case B). These examples are priors to narrow the search, not a substitute for grepping the locale files:

| User says... | Likely Product | Signal keywords to grep |
|---|---|---|
| "block Gemini / Claude / ChatGPT", "restrict which LLMs agents can use", "disable external AI models" | `AITrustLayer` | model names, "provider", "feedback", "region" |
| "lock down Studio", "disable Studio feedback / telemetry", "restrict Studio packages / activities" | `Development` (Studio) | "feedback", "package", "activity", "publish" |
| "control StudioX citizen-dev features", "restrict business-user automations" | `Business` (StudioX) | "StudioX", "citizen", "template" |
| "govern what Robot can run", "restrict attended / unattended runtime" | Robot product (check bootstrap) | "runtime", "process", "attended" |
| "control Agents / Agent Builder features", "restrict agent tool access" | Agents product (check bootstrap) | "agent", "tool", "builder" |
| "enforce a tenant-wide default", "apply to everyone in the tenant" | *Any product* — this is a **deployment** signal, not product selection. Route to [aops-policy-deploy-guide.md](./references/aops-policy-deploy-guide.md) after create. | — |

**Workflow for intent-based requests:**
1. Run the bootstrap (aops-policy-manage-guide Step 1) to materialize every product's schema.
2. Extract intent keywords from the user's phrasing.
3. Rank products by case-insensitive keyword matches in each product's `form-template-locale-resource.json` (Case B). Present the top 3.
4. Do NOT hard-code the mapping above — always verify against the live locale files. Product names and fields change per release.
5. If intent is ambiguous (matches multiple products) or zero products match, ask the user to clarify before proceeding.

## Critical Rules

1. Always use `uip login` before running any `uip gov aops-policy` commands.
2. Always use the product `name` (identifier) in CLI commands, not the `label` shown to the user.
3. For `create`: always bootstrap before selecting or confirming a product. Run `uip gov aops-policy template list --output-dir "$SESSION_DIR/products" --output json` — this writes each product's `form-template.json` (whose top-level `product` object holds `{name, label}`), `form-data.json`, and `form-template-locale-resource.json` into `$SESSION_DIR/products/<ProductName>/`. The product catalog is implicit — enumerate `$SESSION_DIR/products/*/form-template.json` and read `.product.{name, label}` from each file. Do NOT create a separate `products.json` or run `product list`. Use the bootstrapped schemas to validate the user's chosen product against their stated intent; if the intent's fields live under a different product, suggest that product instead.
4. For `create`, read the form template, default form data, and locale labels from `$SESSION_DIR/products/<ProductName>/` (produced by the bootstrap). For `update`, the caller creates `$SESSION_DIR` first (see aops-policy-manage-guide update Step 1) and then configure-guide runs `template get` with `--output-form-data` and `--output-template-locale-resource` into the same per-product subfolder. Use the locale file for human-readable labels and the form-data (create) or existing policy data (update) for the working blueprint. Prefer Mode A (intent-based auto-fill) over field-by-field prompting whenever the user supplied any intent. Do not construct policy data JSON manually.
5. Use the component `key` as the JSON key in policy data — never the label or humanized name.
6. Write the raw policy data object to the data file — do not wrap it in `{ "data": {...} }`. The final policy data file must match the format of the form-data file produced by `template get --output-form-data`.
7. Omit optional flags (`--description`, `--priority`, `--availability`) if the user skips them — do not pass empty strings.
8. Stop and show the error to the user if any command fails.
9. For `update`: always `get` the existing policy first and show its current values before asking what to change. **Use the existing policy's `Data.data` as the update blueprint** (`jq '.Data.data' > "$SESSION_DIR/existing-policy-data.json"`) — NOT the product's default `form-data.json`. Using the product defaults as the update blueprint would silently wipe every non-default setting the user previously configured.
10. For `delete`: always `get` the policy and show a summary, then ask for explicit confirmation before running the delete command.
11. **Prompt only for missing information.** If the user's original request already supplied a value (product, policy name, description, priority, or field intent), use it silently. Do not re-confirm values the user already provided. Confirm unchanged defaults is never required — silence means "keep defaults".
12. **Single confirmation gate per mutation.** Exactly one yes/no review precedes each `create`, `update`, or `delete` call. Do not add intermediate yes/no gates (no per-page confirmation, no "save this configuration?" after configure). The caller in [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md) owns the final review.
13. **Never ask the user to edit this skill.** Do not suggest that the user add their request as an example to `SKILL.md`, a reference file, or any other part of the skill. The user's job is to describe what they want governed; your job is to execute the existing flow (bootstrap → Case A/B → configure → review → create). If the user's intent does not map to any product after the bootstrap + locale grep, ask them to clarify the rule or pick a product from the list — do NOT propose skill edits as a workaround.
14. **Deployment precedence is User > Group > Tenant.** Pick the narrowest scope that matches the user's ask. "Apply to one person" → user-level deployment. "Exception for team X" → group-level (the tenant rule still covers everyone else). "Everyone in the tenant" → tenant-level. See [aops-policy-deploy-guide.md — Deployment precedence](./references/aops-policy-deploy-guide.md#deployment-precedence).
15. **Every create/update review MUST show Priority + the current #1 holder.** Before the single review gate, run `uip gov aops-policy list --product-name "$PRODUCT_NAME" --order-by priority --order-direction asc --output json` — even when the user already supplied a priority — and cite the policy at priority 1 (name + GUID) next to the proposed priority in the review block, along with a one-line rank-impact note ("placed last — does not reorder existing winners" vs. "outranks <name> at the group level"). Omitting this row silently lets the user approve a priority whose group-level consequences they never saw. Exact format: [aops-policy-manage-guide.md — Step 4](./references/aops-policy-manage-guide.md#step-4--final-review-before-create-single-confirmation-gate).
16. **Every create/update review MUST include a clickable `Policy data` link with the full absolute path to `$SESSION_DIR/aops-policy-data.json`.** Render it as a markdown link (`[aops-policy-data.json](/absolute/path/to/.../aops-policy-data.json)`) using the **resolved absolute path** — never a relative path, a literal `<SESSION_DIR>` placeholder, or a `~/` path. Run `realpath` (or equivalent) to resolve. This is the user's only chance to inspect every composed field (including defaults not surfaced in the changed-settings diff) before the mutation runs. Reviews without this link are incomplete — do not call `create` / `update` after an incomplete review. Exact format: [aops-policy-manage-guide.md — Step 4](./references/aops-policy-manage-guide.md#step-4--final-review-before-create-single-confirmation-gate) and [Step 5](./references/aops-policy-manage-guide.md#step-5--final-review-before-update-single-confirmation-gate).
17. **Do NOT show an `Availability:` row in the create/update review unless the user explicitly supplied a value.** Availability is the offline grace period (in days) during which a client (Studio, Assistant, etc.) keeps applying the cached copy of this policy when it cannot reach Automation Ops. It is almost always left at the server default, and surfacing it as `(none)` adds noise to the review. When the user did supply it, show it inline alongside Priority (e.g. `Priority: 4, Availability: 30`) rather than as a standalone row. Semantics: must be an integer > 0; sending `0` causes the server to normalize to `30`; when multiple products contribute to a merged policy response, the smallest `availability` across contributors wins.

## Quick Start

These steps are for **creating a new policy from scratch**. For existing policies or targeted operations, jump straight to the relevant guide via the [Task Navigation](#task-navigation) table below.

### Step 0 — Verify the `uip` CLI

```bash
which uip && uip --version
```

If not installed (both commands fail):
```bash
npm install -g @uipath/uipcli
```

### Step 1 — Check login status

All `uip gov aops-policy` commands require authentication.

```bash
uip login status --output json
```

If not logged in:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Create a session directory and bootstrap every product's schema

Isolate scratch files for this run in a session directory, then fetch every product's form template, default form data, and locale resource in a single call (Critical Rule #3).

```bash
SESSION_DIR="./aops-sessions/$(date +%Y%m%d-%H%M%S)-$(uuidgen | cut -c1-8 | tr '[:upper:]' '[:lower:]')"
mkdir -p "$SESSION_DIR/products"
uip gov aops-policy template list --output-dir "$SESSION_DIR/products" --output json
```

This writes `form-template.json`, `form-data.json`, and `form-template-locale-resource.json` into `$SESSION_DIR/products/<ProductName>/` for every product. The product catalog is implicit — enumerate `$SESSION_DIR/products/*/form-template.json` and read `.product.{name, label}` from each file.

See [configure-aops-policy-data-guide.md — Step 1](./references/configure-aops-policy-data-guide.md) for the full bootstrap procedure.

### Step 3 — Select the product

Two cases, per [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md):

- **Case A — user named the product.** Use it silently (Critical Rule #11). Validate that the user's stated intent maps to fields in that product's schema; if not, suggest the better-fitting product.
- **Case B — infer from intent.** Extract intent keywords and search every product's `form-template-locale-resource.json` to rank matches. Present the top 3 and let the user confirm. See the intent-mapping table above for priors.

### Step 4 — Configure policy data

Prefer **Mode A (intent-based auto-fill)** over **Mode B (field-by-field prompting)** whenever the user supplied any intent (Critical Rule #4).

- Walk the form.io component tree in `form-template.json`.
- Apply user intent to matching components using their `key` (never the label — Critical Rule #5).
- Look up labels from `form-template-locale-resource.json` when surfacing choices to the user.
- Write the resulting raw object to `$SESSION_DIR/aops-policy-data.json` — do NOT wrap it in `{ "data": {...} }` (Critical Rule #6).

See [configure-aops-policy-data-guide.md](./references/configure-aops-policy-data-guide.md) for the full component-tree traversal.

### Step 5 — Single review gate

Show only the **changed** values (not unchanged defaults) and require an explicit `yes`. This is the only confirmation gate in the entire create flow (Critical Rule #12). Use the canonical wording from [Confirmation-gate wording](#confirmation-gate-wording) below.

The review block MUST include:
- A `Priority` row with (a) the proposed priority number, (b) the current #1 holder's policy name and GUID, and (c) a one-line rank-impact note (Critical Rule #15).
- A `Policy data` row with a clickable markdown link to the composed `$SESSION_DIR/aops-policy-data.json` — using the resolved path, not a `<SESSION_DIR>` placeholder (Critical Rule #16).

See [aops-policy-manage-guide.md — Step 4 review template](./references/aops-policy-manage-guide.md#step-4--final-review-before-create-single-confirmation-gate) for the exact format. If you skipped the priority-landscape `list` call in Step 3, run it before showing the review — the user cannot consent to the rank impact without seeing whose position the new policy is landing behind.

### Step 6 — Create

```bash
uip gov aops-policy create \
  --product-name "<PRODUCT_NAME>" \
  --name "<POLICY_NAME>" \
  --input "$SESSION_DIR/aops-policy-data.json" \
  --output json
```

Omit `--description`, `--priority`, `--availability` if the user did not supply them (Critical Rule #7). Stop and surface the error if the command fails (Critical Rule #8).

### Step 7 — Post-create choice

Present the next steps as a numbered Markdown list. See **Completion Output** below for the exact options.

## Anti-patterns

- Do NOT construct policy data JSON manually or guess field keys — every key and nested structure must be derived from the form.io component tree in `form-template.json`, and every value must start from `form-data.json` (create) or `Data.data` (update). Hand-written JSON silently drops or mis-names fields, producing policies that look fine to the CLI but do nothing at runtime.
- Do NOT guess field labels from the component `key` — humanizing the key (e.g., `feedbackEnabled` → "Feedback Enabled") is often wrong. Look the label up in `form-template-locale-resource.json` first.
- Do NOT shortcut the bootstrap by running `template get` for a single product in the create flow — you need every product's schema in `$SESSION_DIR/products/` to rank intent matches against live locale files (Rule #3).
- Do NOT pick a product from the intent-mapping table above without also grepping the live locale files — product names and fields drift per release. The table is a prior, not the answer.
- Do NOT dismiss a "block / restrict / require / enforce" request as out of scope because the user didn't say the word "policy" — these are governance intents that belong to this skill.
- Do NOT write runtime-rule policies (RT-UIA-001 application/URL lists, RT-OUT-001 email blocklist) with empty parameter arrays. The rules are enabled by default but enforce nothing until their `AllowedApplications` / `BlockedURLs` / `BlockedEmails` lists are populated. If the user's intent didn't supply values, surface the no-op to them before creating. See [aops-governance-recipes-guide.md — R1/R2/R3](./references/aops-governance-recipes-guide.md#robot-runtime-analyzer-recipes).
- Do NOT deploy a product policy to a license type that doesn't include that product (e.g. an Assistant policy to the `Unattended` license type — it only covers Robot). Check the license-type → product coverage in [aops-policy-commands.md — license-type list](./references/aops-policy-commands.md#uip-gov-aops-policy-license-type-list) before building the tenant assignment file.
- Do NOT assume enforcing a Studio policy activates the default Workflow Analyzer rule set. Once governance is enforced, every built-in rule becomes DISABLED unless explicitly listed in `Analyzer.EmbeddedRulesConfig.Rules` with `IsEnabled: true`. If the user asks to "enforce Workflow Analyzer" without naming rules, ask which rules matter or apply a CoE baseline and confirm — do not save an empty `Rules` array. See [aops-governance-recipes-guide.md — S3](./references/aops-governance-recipes-guide.md#s3--enable-and-configure-workflow-analyzer-rules).
- Do NOT promise a cloud policy will apply to clients that aren't Interactively Signed-In to Orchestrator. Studio / StudioX / Assistant connected via unattended or service-account sign-in ignore cloud-deployed policies. If a user reports "my policy isn't taking effect", check the client's sign-in mode before debugging the policy contents.

## Task Navigation

| I need to... | Read these |
| --- | --- |
| **Create a new policy from intent** | Quick Start + [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md) (Case B) + [configure-aops-policy-data-guide.md](./references/configure-aops-policy-data-guide.md) |
| **Create a policy when the user named the product** | [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md) (Case A) + [configure-aops-policy-data-guide.md](./references/configure-aops-policy-data-guide.md) |
| **Update an existing policy** | [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md) — blueprint from `Data.data`, NOT `form-data.json` (Rule #9) |
| **Delete a policy** | [aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md) — show summary + explicit `yes` (Rule #10) |
| **List policies** | [aops-policy-manage-guide.md — List](./references/aops-policy-manage-guide.md) |
| **Get a single policy by GUID** | [aops-policy-manage-guide.md — Get](./references/aops-policy-manage-guide.md) |
| **Deploy a policy to a user / group / tenant** | [aops-policy-deploy-guide.md](./references/aops-policy-deploy-guide.md) |
| **Query what policy is deployed to a tenant** | [aops-policy-deployed-guide.md](./references/aops-policy-deployed-guide.md) — use `get` |
| **Query what rules effectively apply to me** | [aops-policy-deployed-guide.md](./references/aops-policy-deployed-guide.md) — use `list` |
| **Find a canonical recipe for a common governance intent** | [aops-governance-recipes-guide.md](./references/aops-governance-recipes-guide.md) — check here first; apply the recipe's product + field mapping before field-by-field prompting |
| **Configure individual field values (form.io traversal)** | [configure-aops-policy-data-guide.md](./references/configure-aops-policy-data-guide.md) |
| **Recognize a governance intent** | Intent-mapping table at the top of this SKILL.md |
| **Pick the right product for an intent** | Bootstrap (Step 2) + keyword search on locale files (Rule #3) + intent-mapping table |

## Key Concepts

### Bootstrap and the implicit product catalog

`uip gov aops-policy template list --output-dir <dir>` writes every product's `form-template.json`, `form-data.json`, and `form-template-locale-resource.json` into `<dir>/<ProductName>/`. There is no separate `product list` step — enumerate products by globbing the bootstrapped directory and reading the top-level `product` object from each `form-template.json`. This is the source of truth (Critical Rule #3).

### Case A vs Case B

- **Case A** — the user named the product. Use it silently; validate intent against its schema.
- **Case B** — the user described a rule but did not name a product. Rank products by keyword matches in each `form-template-locale-resource.json`. Present top 3.

### Deployed policy vs effective rules

| Command | Returns | Use when |
|---------|---------|----------|
| `deployed-policy get` | Tenant-level deployed policy assignment for a `(licenseType, product, tenant)` | "What policy is deployed to this tenant?" |
| `deployed-policy list` | Effective rule values for the calling user after the user → group → tenant chain | "What rules actually apply to me?" |

See [aops-policy-deployed-guide.md](./references/aops-policy-deployed-guide.md).

### Product name vs product label

The product `name` is the CLI identifier (e.g., `Development`, `AITrustLayer`). The `label` is the human display string. Always pass `name` to CLI flags; surface `label` only in user-facing messages (Critical Rule #2).

### Session directory

Scratch space for a single run: `./aops-sessions/<YYYYMMDD-HHMMSS>-<short-uuid>/`. Holds bootstrapped product schemas under `products/<ProductName>/`, the working `aops-policy-data.json`, and (for update) `existing-policy-data.json`. Reuse `$SESSION_DIR` across related operations such as configure → deploy.

### Priority rules

Priority is **NOT** what decides which policy wins across user / group / tenant — that's the resolution chain (User > Group > Tenant), which is determined by scope, not by Priority. Priority only ever matters as a **tie-breaker within the same level**, and in practice it only actually breaks ties at the **group level**:

| Level | Can multiple policies compete for the same product? | Role of Priority |
|-------|-----------------------------------------------------|------------------|
| User   | No — each `(user, product)` has at most one assignment. | None. Priority has no effect. |
| Group  | **Yes** — a user can belong to multiple groups, each with its own policy for the same product. | **Tie-breaker.** Lowest priority number wins among the competing group assignments. |
| Tenant | No — each `(tenant, product, licenseType)` has exactly one assignment. | None. Priority has no effect. |

Outside of the group-level tie-breaker, Priority is essentially an admin-facing ordering hint (it controls the order policies appear in the Automation Ops catalog / `aops-policy list`, not which one applies at runtime).

**Practical consequence for the create flow:** default a new policy to the **largest existing priority + 1** (i.e. place it *last*), so creation never silently reorders the group-level tie-breaker outcome for existing users. Only lower the number when the user explicitly asks for the new policy to outrank specific existing policies at the group level. Always explain this before prompting for a priority value. See also [Deployed policy vs effective rules](#deployed-policy-vs-effective-rules) for how scope resolution works.

### Confirmation-gate wording

Every mutation runs through a single yes/no review (Critical Rule #12). Use these templates verbatim so wording stays consistent across the skill:

| Operation | Template |
|-----------|----------|
| Create | `Create policy "<POLICY_NAME>" for <PRODUCT_LABEL>? (yes / no / keep editing)` |
| Update | `Apply update to policy "<POLICY_NAME>"? (yes / no / keep editing)` |
| Delete | `Delete policy "<POLICY_NAME>"? This cannot be undone. (yes / no)` |
| Deploy (any subject) | `Apply these changes to <SUBJECT_NAME>? (yes / no)` |
| Deployment delete-all | `Delete all policy assignments for <SUBJECT_NAME>? This cannot be undone. (yes / no)` |
| Tenant remove | `Remove <PRODUCT_LABEL> assignment from <TENANT_NAME>? This cannot be undone. (yes / no)` |

`keep editing` is treated the same as `no` — route the user back to the relevant step (metadata / field-configure / subject-pick) and re-enter the review gate only after the change is applied.

### Mode A vs Mode B (policy data configuration)

- **Mode A (auto-fill)** — prefer whenever the user supplied any intent. Walk the form.io tree and apply the intent to matching components automatically.
- **Mode B (field-by-field)** — fall back only when the user has no stated intent or explicitly asks to see every field.

See [configure-aops-policy-data-guide.md](./references/configure-aops-policy-data-guide.md).

## Completion Output

When you finish a mutating operation, report:

1. **Operation & result** — e.g., `Created policy <name> (GUID: <guid>) for product <productName>`.
2. **Session directory** — print `$SESSION_DIR` so the user can inspect bootstrapped schemas and the `aops-policy-data.json` that was submitted.
3. **Non-default fields set** — summary of fields the user configured vs. ones that stayed at defaults. (Omit this line after `delete`.)
4. **Next step** — present a numbered Markdown list under `### What would you like to do next?` with these options (single post-mutation gate, per Critical Rule #12):

```markdown
### What would you like to do next?

1. **Deploy to a user** — hand off to [aops-policy-deploy-guide.md](./references/aops-policy-deploy-guide.md) with subject = user.
2. **Deploy to a group** — hand off to [aops-policy-deploy-guide.md](./references/aops-policy-deploy-guide.md) with subject = group.
3. **Deploy to the tenant** — hand off to [aops-policy-deploy-guide.md](./references/aops-policy-deploy-guide.md) with subject = tenant.
4. **List policies to verify** — run `uip gov aops-policy list --output json` and show the new/updated entry.
5. **Query effective rules** — run `deployed-policy list` (or `get`) per [aops-policy-deployed-guide.md](./references/aops-policy-deployed-guide.md).
6. **Something else** — accept free-form string input and act on it (e.g., "just leave it", "export the policy data", "create another one").

Reply with the number.
```

Do not run any of these actions automatically. Wait for the user's selection.

**Per-operation adjustments to the list:**
- After `create` or `update`: offer all options above.
- After `deploy`: replace the three Deploy options with a single **Verify deployment** option that runs `deployed-policy get <licenseType> <productName> <tenantIdentifier>` to confirm the assignment took effect. Keep **Query effective rules** (via `deployed-policy list`) as the follow-up check for chain-resolved values.
- After `delete`: offer only **List policies to verify** and **Something else**.

## References

- **[aops-policy-commands.md](./references/aops-policy-commands.md)** — Single source of truth for every `uip gov aops-policy` subcommand, its flags, input/output shapes, and authentication modes (including S2S token acquisition). Every other guide links here for command details rather than inlining them.
- **[aops-policy-manage-guide.md](./references/aops-policy-manage-guide.md)** — Full CRUD lifecycle: list, get, create, update, delete. Owns the single final-review gate before every mutation. Documents Case A (user-named product) vs Case B (intent-based selection).
- **[configure-aops-policy-data-guide.md](./references/configure-aops-policy-data-guide.md)** — Form.io component-tree traversal, locale lookups for human-readable labels, Mode A (intent-based auto-fill) vs Mode B (field-by-field), and the bootstrap of every product's schema into `$SESSION_DIR/products/`.
- **[aops-policy-deploy-guide.md](./references/aops-policy-deploy-guide.md)** — Assign policies to user / group / tenant via `deployment <subject> configure --input`. Non-interactive: the agent builds the assignment JSON, calls `configure --input`, and verifies with `deployment <subject> get`.
- **[aops-policy-deployed-guide.md](./references/aops-policy-deployed-guide.md)** — Query the single effective policy (`get`) vs every applicable rule for the calling user (`list`). Positional argument reference (`<LICENSE_TYPE> <PRODUCT_NAME> <TENANT_ID>`) and S2S flag semantics (`--s2s-token`, `--user-id`, `--tenant-only`).
