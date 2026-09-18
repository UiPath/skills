---
name: uipath-knowledge-bundles
description: "Read and publish UiPath knowledge bundles via `uip or knowledge-bundles` — versioned sets of markdown documents (Open Knowledge Format) that live in an Orchestrator folder and that an agent reads from as context. Download a version into a local workspace, read one file or a whole version, publish a directory as version 1, and ask what a local copy needs to match a published version. PREVIEW: these commands exist only on a prerelease `uip` build and only on tenants with the knowledge-bundles feature enabled — Step 0 below is how you find out, and a miss means stopping, not improvising. Changing published content needs a reviewed change proposal, which has no CLI surface yet. For Orchestrator assets, queues, buckets, jobs→uipath-platform. For context grounding / semantic search indexes→uipath-platform. For `uip solution` lifecycle→uipath-solution."
when_to_use: "User says 'knowledge bundle', 'knowledge bundles', 'OKF', 'Open Knowledge Format', 'download the knowledge bundle', 'publish docs to Orchestrator', 'what version of the bundle', 'bundle manifest', 'change proposal on a bundle', 'give the agent its knowledge', 'where does the agent read its documentation from'. Also when a task needs the documents an agent reads as context and those documents are said to live in Orchestrator rather than in the repo."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Knowledge Bundles — `uip or knowledge-bundles`

A knowledge bundle is a folder-scoped Orchestrator entity holding a versioned tree of markdown documents. Versions are immutable and numbered (v1, v2, …); reads accept a number or the literal `latest`. Content is addressed by hash, so transfers move only what changed.

## Step 0: Preflight — is this surface available?

Run once per session:

```bash
uip or knowledge-bundles --help
```

- **Succeeds** → continue.
- **`unknown command`** → the installed `uip` is a stable build. These commands register only on a prerelease build (`preview` / `dev` channel). Tell the user that plainly and stop — do not substitute bucket, asset or context-grounding commands, and do not guess an older command name.
- **A command runs but the platform refuses it** → the tenant does not have the knowledge-bundles feature enabled. Say so and stop; only an administrator can change it. A `403`/feature failure is not a login problem — never "fix" it by re-running `uip login`.

## Every command is folder-scoped

Bundles live in a folder and are not addressable without one. Pass `--folder-path <path>` (or `--folder-key <guid>`) on **every** command. `uip or folders list` finds one.

Bundles are identified by a GUID (`Key`). Get it from `list`, never construct it.

`--search` matches the bundle's **`Name` only** — not its description, and not the `title` inside its documents. A bundle named `ops-handbook-7` can hold a document titled "Contoso Operations Handbook", so searching what the user called it often returns an empty `Data: []` that reads like "no such bundle". When a descriptive search comes up empty, list the folder unfiltered and look at the names and descriptions; page with `--limit` / `--offset` rather than trusting the first page.

## Commands

| Goal | Command |
|---|---|
| Find bundles | `uip or knowledge-bundles list --folder-path <p> [--search <text>] [--limit <n>] [--offset <n>] [--all-fields]` |
| One bundle's record | `uip or knowledge-bundles get <bundle-id> --folder-path <p>` |
| Create, empty | `uip or knowledge-bundles create <name> --folder-path <p> [-d <text>]` |
| Create + publish v1 from a directory | `uip or knowledge-bundles create <name> --folder-path <p> --input <dir> -m <message>` |
| Publish v1 into an existing empty bundle | `uip or knowledge-bundles publish <bundle-id> <dir> --folder-path <p> -m <message>` |
| Rename / re-describe | `uip or knowledge-bundles update <bundle-id> --folder-path <p> [-n <name>] [-d <text>]` |
| Remove from a folder | `uip or knowledge-bundles delete <bundle-id> --folder-path <p> --yes` |
| Share into / out of folders | `uip or knowledge-bundles share <bundle-id> --folder-path <p> [--add-folders <f...>] [--remove-folders <f...>]` |
| Version history | `uip or knowledge-bundles versions <bundle-id> --folder-path <p>` |
| Unpack a version into a workspace | `uip or knowledge-bundles download <bundle-id> --folder-path <p> --output <dir> [--version <n>]` |
| Whole version as a zip | `uip or knowledge-bundles archive <bundle-id> --folder-path <p> --output <file>.zip [--version <n>]` |
| One file's content | `uip or knowledge-bundles file <bundle-id> <path> --folder-path <p> [--version <n>] [--output <file>]` |
| One file across versions | `uip or knowledge-bundles history <bundle-id> <path> --folder-path <p>` |
| A version's derived artifact | `uip or knowledge-bundles build <bundle-id> graph.json --folder-path <p>` |
| What a local copy needs | `uip or knowledge-bundles sync <bundle-id> <dir> --folder-path <p>` |

Add `--output json` when you parse the result.

## Reading a bundle as context

```bash
uip or knowledge-bundles download <bundle-id> --folder-path <p> --output ./kb
```

That unpacks the version's files plus `./kb/.okf/base.json`, a marker recording the bundle, the version and its manifest. Read the markdown directly from disk. To check whether the copy is current, `sync` it — the report is **pull-direction**: `Changed` is what to download to match the published version, `Deleted` is what to remove locally. A file you deleted locally shows up in `Changed`, not `Deleted`.

## Publishing

`publish` and `create --input` only ever produce **version 1**, and only for a bundle with no content. Every later version comes from merging a change proposal, which has **no CLI surface yet** — if the user wants to change published content, say that and stop rather than deleting and re-creating the bundle. There is no hidden command for it: do not try `knowledge-proposals`, `propose`, or a variation, and do not read a 409 as a sign you used the wrong command name.

Both walk the directory, hash every file, upload only what the store lacks, then publish the manifest. Two rules the walk obeys:

- **Dot-prefixed files are skipped** unless `--include-hidden` is passed.
- **`.okf/`, `.git/` and `_refs/` are never published**, whatever the flags say — the format reserves them, and `_refs/` is where a download materializes *other* bundles' content. Publishing from a downloaded workspace is therefore safe.

## What the output means

`Failure` envelopes carry `Context.HttpStatus`. Two worth recognizing:

- **409 on `create`** → that name is already used in the folder. Pick another; do not retry.
- **409 on `publish`** → the bundle already has content. Stop; this needs a change proposal.

`file` returns the content inline when it decodes as UTF-8 text, and refuses binary without `--output <file>` — pass it rather than trying to read bytes from the envelope.

## Not available yet

Do not attempt these, and do not tell the user they exist: change proposals and their comments (no commands), cross-bundle references expanded under `_refs/` (the server does not build them yet, so a downloaded workspace holds only this bundle's files), and reading a file out of a proposal rather than a published version.
