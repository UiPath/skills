#!/usr/bin/env node
// Detects whether Claude Code has an allowlist for `uip` subcommands.
// If none is found, prints a one-line nudge pointing at /uipath:install-permissions.
// Non-blocking — never fails the session, even if detection fails.
//
// Runs under Node.js (>= 20), which is present wherever the skills were
// installed through the Node-based `uip` CLI. hooks.json guards the spawn and
// silently no-ops when `node` is not on PATH.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

function main() {
  // Only run inside a Claude Code plugin context.
  if (!process.env.CLAUDE_PLUGIN_ROOT) return;

  // Codex exposes Claude-compatible plugin environment variables for hook
  // compatibility. This nudge is Claude-specific, so keep Codex sessions silent.
  if (process.env.PLUGIN_ROOT) return;

  // Candidate settings files, most-to-least specific.
  const candidates = [];
  if (process.env.CLAUDE_PROJECT_DIR) {
    candidates.push(path.join(process.env.CLAUDE_PROJECT_DIR, ".claude/settings.local.json"));
    candidates.push(path.join(process.env.CLAUDE_PROJECT_DIR, ".claude/settings.json"));
  }
  candidates.push(path.join(process.cwd(), ".claude/settings.local.json"));
  candidates.push(path.join(process.cwd(), ".claude/settings.json"));
  candidates.push(path.join(os.homedir(), ".claude/settings.json"));

  // If any candidate already mentions Bash(uip...) in its permissions, stay silent.
  // Intentional simplification: this matches `allow`, `ask`, AND `deny` blocks.
  // Any explicit `uip` rule means the user has made a decision about this CLI —
  // we don't second-guess by nudging them toward a permissive allowlist.
  for (const file of candidates) {
    let content = "";
    try {
      content = fs.readFileSync(file, "utf8");
    } catch {
      continue;
    }
    if (content.includes("Bash(uip")) return;
  }

  // No allowlist detected — print a one-line nudge to stderr (the Claude Code
  // SessionStart convention for status messages).
  process.stderr.write(
    "uipath: To skip 25+ approval prompts per uip build, run: /uipath:install-permissions\n",
  );
}

try {
  main();
} catch {
  // never-fail: detection problems must not block the session
}
process.exit(0);
