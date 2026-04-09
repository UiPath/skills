---
name: uipath-upgrade
description: "Upgrade the UiPath skills plugin (this plugin) itself to the latest version from UiPath/skills on GitHub. Handles update/upgrade skills requests and session start upgrade notices. For Platform/Studio/Orchestrator→uipath-platform."
user-invocable: true
---

# UiPath Skills Upgrade

## When to Use This Skill

- The SessionStart hook injected a `UiPath skills plugin upgrade available` notice into the session context
- The user asks to upgrade, update, or refresh the UiPath skills plugin
- The user runs `/uipath-upgrade` directly
- The SessionStart hook injected a `UiPath skills plugin just upgraded` notice (show what's new)

## Critical Rules

1. NEVER upgrade without user consent unless `auto_upgrade` is `true`
2. ALWAYS use `--ff-only` for git merge to avoid conflicts with local changes
3. If `--ff-only` fails, warn the user — do NOT force-reset or discard their changes
4. ALWAYS write the `just-upgraded-from` marker after a successful upgrade
5. ALWAYS clear the cache and snooze files after a successful upgrade

## Inline Upgrade Flow

Follow these steps when the SessionStart hook context mentions that a UiPath skills plugin upgrade is available.

### Step 1: Check auto_upgrade setting

Run:

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/uipath-skills-config.sh" get auto_upgrade
```

If the output is `true`, skip to Step 3 (perform the upgrade silently).

Otherwise, proceed to Step 2.

### Step 2: Ask the user

Use AskUserQuestion with these 4 options:

> A new version of the UiPath skills plugin is available (current: {local}, latest: {remote}).

- A) **Yes, upgrade now**
- B) **Always keep me up to date** — auto-upgrade on every session start
- C) **Not now** — remind me later
- D) **Never ask again** — disable update checks

**If A:** proceed to Step 3.

**If B:** Run the following, then proceed to Step 3:

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/uipath-skills-config.sh" set auto_upgrade true
```

**If C:** Write the snooze file and continue with the user's original task. Read the current snooze level from `~/.uipath-skills/update-snoozed` (if it exists). If the snoozed version matches the remote version, increment the level (max 3). Otherwise, start at level 1.

```bash
# Read current snooze state
SNOOZE_FILE="$HOME/.uipath-skills/update-snoozed"
REMOTE_VERSION="<remote>"

if [ -f "$SNOOZE_FILE" ]; then
  SNOOZED_VER=$(awk '{print $1}' "$SNOOZE_FILE")
  SNOOZED_LEVEL=$(awk '{print $2}' "$SNOOZE_FILE")
  if [ "$SNOOZED_VER" = "$REMOTE_VERSION" ]; then
    NEW_LEVEL=$(( SNOOZED_LEVEL + 1 ))
    [ "$NEW_LEVEL" -gt 3 ] && NEW_LEVEL=3
  else
    NEW_LEVEL=1
  fi
else
  NEW_LEVEL=1
fi

mkdir -p "$HOME/.uipath-skills"
echo "$REMOTE_VERSION $NEW_LEVEL $(date +%s)" > "$SNOOZE_FILE"
```

Then stop the upgrade flow and continue with whatever the user originally asked.

**If D:** Run the following, then continue with the user's original task:

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/uipath-skills-config.sh" set update_check false
```

### Step 3: Detect git remote

Determine which git remote points to the upstream UiPath/skills repository:

```bash
cd "$CLAUDE_PLUGIN_ROOT"
# Check if upstream remote exists
if git remote get-url upstream 2>/dev/null | grep -qi "uipath/skills"; then
  REMOTE_NAME="upstream"
elif git remote get-url origin 2>/dev/null | grep -qi "uipath/skills"; then
  REMOTE_NAME="origin"
else
  git remote add upstream https://github.com/UiPath/skills.git
  REMOTE_NAME="upstream"
fi
echo "Using remote: $REMOTE_NAME"
```

### Step 4: Perform the upgrade

```bash
cd "$CLAUDE_PLUGIN_ROOT"
OLD_VERSION=$(grep '"version"' .claude-plugin/plugin.json | head -1 | sed 's/.*"\([0-9][^"]*\)".*/\1/')
git fetch <REMOTE_NAME>
git merge <REMOTE_NAME>/main --ff-only
NEW_VERSION=$(grep '"version"' .claude-plugin/plugin.json | head -1 | sed 's/.*"\([0-9][^"]*\)".*/\1/')
echo "Upgraded from $OLD_VERSION to $NEW_VERSION"
```

Replace `<REMOTE_NAME>` with the remote detected in Step 3.

If `git merge --ff-only` fails, tell the user:

> The upgrade could not be applied automatically because you have local changes.
> You can try:
> 1. `git stash && git merge <REMOTE_NAME>/main --ff-only && git stash pop`
> 2. Or manually resolve with `git merge <REMOTE_NAME>/main`

Do NOT force-reset or discard changes.

### Step 5: Write marker and clear state

After a successful upgrade:

```bash
mkdir -p "$HOME/.uipath-skills"
echo "$OLD_VERSION" > "$HOME/.uipath-skills/just-upgraded-from"
rm -f "$HOME/.uipath-skills/last-update-check"
rm -f "$HOME/.uipath-skills/update-snoozed"
```

### Step 6: Show what's new

Read `CHANGELOG.md` in the plugin root. Summarize the entries between the old version and the new version for the user.

If `CHANGELOG.md` does not exist, fall back to:

```bash
cd "$CLAUDE_PLUGIN_ROOT"
git log --oneline v${OLD_VERSION}..HEAD 2>/dev/null || git log --oneline --since="1 month ago" --max-count=20
```

### Step 7: Continue

Tell the user the upgrade is complete and continue with their original task.

## Standalone Usage

When the user runs `/uipath-upgrade` directly (not triggered by session-start notice):

1. Force a fresh version check by running:

```bash
rm -f "$HOME/.uipath-skills/last-update-check"
bash "$CLAUDE_PLUGIN_ROOT/hooks/update-check.sh"
```

2. If the output JSON `additionalContext` mentions `upgrade available`, follow Steps 2-7 above.
3. If no upgrade is reported (already up to date), tell the user: "UiPath skills plugin is already up to date (v{version})."

## Handling Just-Upgraded Notices

When the SessionStart hook context mentions `UiPath skills plugin just upgraded from <old> to <new>`:

Tell the user: "Running UiPath skills plugin v{new} (just updated from v{old})!"

Then read `CHANGELOG.md` and briefly summarize what changed. Continue with the user's task.

## What NOT to Do

- Do NOT run `git reset --hard` or `git clean` — the user may have local changes
- Do NOT modify `plugin.json` directly — the upgrade pulls the new version from upstream
- Do NOT skip the AskUserQuestion step unless `auto_upgrade` is `true`
- Do NOT prompt about upgrading if the context shows a just-upgraded notice — just report and continue
