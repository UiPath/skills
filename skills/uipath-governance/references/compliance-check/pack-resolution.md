# Pack Resolution

How the orchestrator gets from user intent to a local unzipped pack directory.

## Input forms

| User input | Action |
|---|---|
| `--pack-file <path>` | Use local file directly. V0 / offline / pre-published path. |
| `--pack-url <url>` | Download from explicit URL. |
| `--pack-id <id> [--pack-version <version>]` | Construct CDN URL; default version is `latest`. |
| Natural language ("check compliance against ISO 27001") | Infer `packId`, default to `latest`. Ask user to confirm before downloading. |

## CDN layout (when the pack service ships)

```
{cdn}/compliance-packs/
├── index.json
├── {packId}/
│   ├── latest/pack.uipolicy
│   ├── {version}/pack.uipolicy
│   └── versions.json
```

Construction:
- Latest: `{cdn}/compliance-packs/{packId}/latest/pack.uipolicy`
- Pinned: `{cdn}/compliance-packs/{packId}/{version}/pack.uipolicy`

## Download + unzip

```bash
# Download to a temp dir
tmp="$(mktemp -d)/pack"
mkdir -p "$tmp"
curl -fsSL "<url>" -o "$tmp/pack.uipolicy" || { echo "download failed"; exit 1; }

# Unzip
unzip -q "$tmp/pack.uipolicy" -d "$tmp/extracted"
```

Local `--pack-file`:

```bash
tmp="$(mktemp -d)/pack"
mkdir -p "$tmp/extracted"
unzip -q "<LOCAL_PACK_PATH>" -d "$tmp/extracted"
```

## Verification

After unzip, check:

```bash
test -f "$tmp/extracted/manifest.json"      || { echo "missing manifest.json"; exit 1; }
test -f "$tmp/extracted/clause-map.json"    || { echo "missing clause-map.json"; exit 1; }
test -d "$tmp/extracted/policies"           || { echo "missing policies/ dir"; exit 1; }
```

## Version handling

- User said nothing about version → resolve to `latest` from CDN `index.json` or (for local) use whatever version is in the pack's `manifest.json`.
- User pinned (e.g. "check compliance against ISO 27001 v1.2.0") → fetch exactly that version. If not found, stop and surface `pack version not found`.
- The compliance report always captures the **actual** `(packId, version)` from the parsed `manifest.json`, not the user's input phrase.

## V0 Stand-In

The Compliance Pack Service does not exist yet. Until it does, always use `--pack-file <path>` pointing to a locally compiled pack.
