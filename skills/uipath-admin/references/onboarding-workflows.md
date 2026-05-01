# Onboarding Workflows

End-to-end workflows for onboarding users and robots to the UiPath platform. These are multi-step procedures that combine identity commands with Orchestrator operations.

## Prerequisites

```bash
# 1. Verify login
uip login status --output json

# 2. Extract organization ID from the response (field: organizationId)
# Store as ORG_ID for all subsequent commands
```

---

## Workflow 1: Robot Account Onboarding (Unattended Robots)

Onboard an unattended robot that can run processes autonomously. This is the primary workflow for setting up headless automation.

### Step 1 — Create Robot Account

Create the robot identity in Identity Server.

```bash
# Check for existing robot accounts with the same name
uip admin identity robot-accounts list --organization <ORG_ID> \
  --search "<ROBOT_NAME>" --output json

# Create the robot account
uip admin identity robot-accounts create "<ROBOT_NAME>" \
  --organization <ORG_ID> \
  --display-name "<ROBOT_DISPLAY_NAME>" \
  --output json
```

Save the `id` from the response — this is the robot account ID.

### Step 2 — Assign Organization Roles

Add the robot account to appropriate groups for role assignment.

```bash
# List available groups to find the right role group
uip admin identity groups list --organization <ORG_ID> --output json

# Add the robot account to the desired group(s)
uip admin identity groups add-members <GROUP_ID> \
  --organization <ORG_ID> \
  --user-ids "<ROBOT_ACCOUNT_ID>" \
  --output json
```

Common role groups for robots:
- **Automation User** — can execute automations
- **Robot Account Admin** — can manage other robot identities (rarely needed)

### Step 3 — Generate OAuth2 Credentials

Create an external app to generate Client ID + Secret for the robot.

```bash
# Create external app with scopes matching the robot's needs
uip admin identity external-apps create "<ROBOT_NAME>-credentials" \
  --organization <ORG_ID> \
  --scope "OR.Folders,OR.Assets,OR.Queues,OR.Jobs,OR.Machines,OR.Execution" \
  --output json
```

**Save the `id` (Client ID) and `secret` (Client Secret) from the response immediately.**
The secret is shown only once.

### Step 4 — Assign Folder Permissions (Orchestrator)

The robot needs access to Orchestrator folders containing its processes, assets, and queues. These commands use the `uipath-platform` skill's Orchestrator commands.

```bash
# List available folders
uip or folders list --output json

# Assign robot to folder (via Orchestrator API)
# Use the folder-level user/role assignment
```

> For detailed Orchestrator folder and permission management, use the `uipath-platform` skill.

### Step 5 — Create Machine Template (Orchestrator)

Create a machine template and assign it to the same folder as the robot.

```bash
# Create machine template (via Orchestrator API)
# Assign machine template to the folder
```

> Machine template management is handled via the `uipath-platform` skill or the Orchestrator REST API.

### Step 6 — Connect Robot to Machine

On the target machine, connect the UiPath Robot using the credentials from Step 3:

```bash
# Non-interactive login using the generated credentials
uip login \
  --client-id "<CLIENT_ID>" \
  --client-secret "<CLIENT_SECRET>" \
  --tenant "<TENANT_NAME>" \
  --output json
```

### Verification

After completing all steps, verify the robot is connected:

```bash
# Verify the robot account exists
uip admin identity robot-accounts get <ROBOT_ACCOUNT_ID> \
  --organization <ORG_ID> --output json

# Verify the external app exists
uip admin identity external-apps get <CLIENT_ID> \
  --organization <ORG_ID> --output json

# Verify folder access (via Orchestrator)
uip or folders list --output json
```

---

## Workflow 2: Human User Onboarding

Onboard a human user to the UiPath Automation Cloud platform.

### Step 1 — Invite the User

```bash
uip admin identity users invite \
  --email "<USER_EMAIL>" \
  --name "<FIRST_NAME>" \
  --surname "<LAST_NAME>" \
  --output json
```

The user receives an email invitation. They must accept and log in with a UiPath account.

### Step 2 — Assign Organization Roles

After the user accepts the invitation, add them to role groups.

```bash
# List the user to get their ID
uip admin identity users list --organization <ORG_ID> \
  --search "<USER_EMAIL>" --output json

# List available groups
uip admin identity groups list --organization <ORG_ID> --output json

# Add user to role group(s)
uip admin identity groups add-members <GROUP_ID> \
  --organization <ORG_ID> \
  --user-ids "<USER_ID>" \
  --output json
```

Common role groups for human users:
- **Organization Admin** — full platform access
- **Automation User** — can run automations
- **Automation Developer** — can develop and publish automations

### Step 3 — Assign Folder Permissions (Orchestrator)

```bash
# List folders
uip or folders list --output json

# Assign user to specific folders with appropriate roles
```

> For folder permission management, use the `uipath-platform` skill.

### Step 4 — User Signs In

Once the user signs in:
- Studio/Assistant auto-connects (if installed)
- Personal Workspace is created (if enabled in the tenant)

### Optional: Additional Setup

- **Enable Personal Workspaces** in tenant settings
- **Assign Studio/Assistant licenses** via the Orchestrator license management

---

## Workflow 3: Bulk User Onboarding

Invite multiple users and assign them to the same group.

### Step 1 — Invite All Users

```bash
uip admin identity users invite \
  --email "user1@example.com,user2@example.com,user3@example.com" \
  --output json
```

### Step 2 — Wait for Acceptance

Users must accept their invitations before they appear in the user list. Check periodically:

```bash
uip admin identity users list --organization <ORG_ID> \
  --search "example.com" --output json
```

### Step 3 — Add All to a Group

Once users appear in the list, collect their IDs and add them to the target group:

```bash
uip admin identity groups add-members <GROUP_ID> \
  --organization <ORG_ID> \
  --user-ids "<USER_ID_1>,<USER_ID_2>,<USER_ID_3>" \
  --output json
```

---

## Decision Guide: Which Workflow?

```
What are you onboarding?
├── A human user → Workflow 2 (Human User Onboarding)
├── An unattended robot → Workflow 1 (Robot Account Onboarding)
└── Multiple users at once → Workflow 3 (Bulk User Onboarding)
```
