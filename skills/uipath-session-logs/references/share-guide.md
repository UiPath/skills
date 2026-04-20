# Share Guide

Before attaching a capture to a bug report, ticket, or GitHub issue, copy it to a scratch directory and run through this checklist. The logger intentionally does NOT auto-redact: silent redaction is worse than a clear manual step because it tricks you into trusting output that may still leak.

## 1. Copy, do not edit in place

```bash
LATEST=$(ls -1dt .uipath-logs/*/ | head -1)
SHARE=$(mktemp -d -t uipath-capture-XXXX)
cp -R "$LATEST"/. "$SHARE/"
echo "$SHARE"
```

Work on `$SHARE`. The original capture stays intact in case you need to re-analyze later.

## 2. Redaction checklist

Scan the copied files for each category. Replace values with `<REDACTED>` — do not just delete lines (changes JSONL line counts and breaks positional pairing).

| Category | Where it shows up | Search pattern |
|----------|-------------------|----------------|
| Orchestrator / tenant URLs | `session.json`, tool inputs/responses | `cloud\.uipath\.com`, `tenant=` |
| PAT / personal access tokens | Environment vars, `Authorization:` headers in Bash inputs | `UIPATH_PAT`, `Authorization:\s*Bearer` |
| Client secrets | CLI inputs, env vars | `--client-secret`, `client_secret` |
| Cookie / session tokens | HTTP responses captured by Bash tool calls | `Cookie:\s`, `Set-Cookie:\s` |
| Customer data | Queue item payloads, document text, screenshots | Project-specific — review per-PR |
| User file paths with PII | `input.file_path` values | Home dir, real names |
| Tenant IDs / org IDs | `session.json.env`, CLI args | `UIPATH_TENANT_ID`, `UIPATH_ORGANIZATION_ID` |

### A quick pre-scan

```bash
grep -E -i 'bearer |pat[_-]?token|client[_-]?secret|password|set-cookie|uipath_pat' -r "$SHARE" | head
```

Any hit deserves a second look.

### Redaction helper

```bash
# Replace a known token everywhere in the copy
SECRET='eyJhbGciOi...'
grep -rl "$SECRET" "$SHARE" | xargs -I{} sed -i.bak "s|$SECRET|<REDACTED>|g" {}
find "$SHARE" -name '*.bak' -delete
```

On macOS, `sed -i.bak` keeps a backup — remove after verifying.

## 3. Drop the project snapshot if sensitive

`project-snapshot/` contains a copy of your `.uis` / `solution.json` / `project.json` from session start. These often include integration credentials or tenant references. If you cannot share the bundled project, remove the directory before packaging:

```bash
rm -rf "$SHARE/project-snapshot"
```

## 4. Package

```bash
OUT="$(dirname "$SHARE")/capture-$(basename "$LATEST").tgz"
tar -czf "$OUT" -C "$(dirname "$SHARE")" "$(basename "$SHARE")"
echo "Attach: $OUT"
```

## 5. Verify before sending

```bash
# Peek back inside the archive one more time
tar -tzf "$OUT" | head
tar -xzOf "$OUT" "$(basename "$SHARE")/session.json" | jq .
```

## 6. What to include in the ticket

- The archive from step 4
- The exact `claude --version` and `uip --version`
- The command that reproduced the issue
- `summary.json` highlights (error_count, tool_counts)
- A one-line description of the expected vs actual outcome
