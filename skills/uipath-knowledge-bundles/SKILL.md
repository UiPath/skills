---
name: uipath-knowledge-bundles
description: "Read and publish UiPath knowledge bundles via `uip or kb` — versioned sets of markdown documents (Open Knowledge Format) that live in an Orchestrator folder and that an agent reads from as context. Download a version into a local workspace, read one file or a whole version, publish a directory as version 1, and ask what a local copy needs to match a published version. PREVIEW: these commands exist only on a prerelease `uip` build and only on tenants with the knowledge-bundles feature enabled — Step 0 below is how you find out, and a miss means stopping, not improvising. Changing published content goes through a reviewed change proposal: `uip or kb change-proposal` opens one from an edited workspace, carries the review comments, and merges it to publish the next version. For Orchestrator assets, queues, buckets, jobs→uipath-platform. For context grounding / semantic search indexes→uipath-platform. For `uip solution` lifecycle→uipath-solution."
when_to_use: "User says 'knowledge bundle', 'knowledge bundles', 'OKF', 'Open Knowledge Format', 'download the knowledge bundle', 'publish docs to Orchestrator', 'what version of the bundle', 'bundle manifest', 'change proposal on a bundle', 'open a change proposal', 'merge the proposal', 'review the bundle change', 'comment on the proposal', 'give the agent its knowledge', 'where does the agent read its documentation from'. Also when a task needs the documents an agent reads as context and those documents are said to live in Orchestrator rather than in the repo."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Knowledge Bundles — `uip or kb`

A knowledge bundle is a folder-scoped Orchestrator entity holding a versioned tree of markdown documents. Versions are immutable and numbered (v1, v2, …); reads accept a number or the literal `latest`. Content is addressed by hash, so transfers move only what changed.

## Critical Rules

1. **Preflight before anything else.** `uip or kb --help` decides whether this surface exists at all. `unknown command` means a stable build and no amount of retrying changes it; a command that runs but is refused by the platform means the tenant's feature flag is off. Both are stop conditions — say so and stop, never substitute bucket, asset or context-grounding commands.
2. **Every command needs a folder.** `--folder-path <path>` or `--folder-key <guid>` on all of them. There is no tenant-wide listing to fall back on.
3. **Bundle keys come from `list`, never from you.** Same for proposal ids, which come from `change-proposal list`. Do not construct, guess, or carry one over from another folder.
4. **`publish` and `create --input` only ever make version 1.** Every later version comes from merging a change proposal. A 409 means the bundle already has content — never delete and re-create to get around it, that destroys the version history and the review record.
5. **A 403 or a feature refusal is not a login problem.** Do not "fix" it by re-running `uip login`; only an administrator can change it.
6. **`diff` before `merge`.** A merge publishes a version that cannot be edited afterwards.
7. **Paths are bundle-relative and cannot climb.** A `--path` or `--artifact` containing a `.` or `..` segment is refused before any request is sent; pass the path as the manifest lists it.


## Step 0: Preflight — is this surface available?

Run once per session:

```bash
uip or kb --help
```

- **Succeeds** → continue.
- **`unknown command`** → the installed `uip` is a stable build. These commands register only on a prerelease build (`preview` / `dev` channel). Tell the user that plainly and stop — do not substitute bucket, asset or context-grounding commands, and do not guess an older command name.
- **A command runs but the platform refuses it** → the tenant does not have the knowledge-bundles feature enabled. Say so and stop; only an administrator can change it. A `403`/feature failure is not a login problem — never "fix" it by re-running `uip login`.

## Every command is folder-scoped

Bundles live in a folder and are not addressable without one. Pass `--folder-path <path>` (or `--folder-key <guid>`) on **every** command.

`uip or folders list --all` finds one — its flags are its own (`--all`, `--path <prefix>`, `--name`), not `kb list`'s `--search`. Pass its `Path` field to `--folder-path` (a top-level folder is just `Shared`, a nested one `Shared/Finance`) or its `Key` to `--folder-key` — `Name` is the display name and is not what either option wants.

Bundles are identified by a GUID (`Key`). Get it from `list`, never construct it.

On `share`, the scope (`--folder-path`) is the folder that already holds the bundle; `--add-folders` and `--remove-folders` name the folders being changed, and both apply in one call.

`--search` matches the bundle's **`Name` only** — not its description, and not the `title` inside its documents. A bundle named `ops-handbook-7` can hold a document titled "Contoso Operations Handbook", so searching what the user called it often returns an empty `Data: []` that reads like "no such bundle". When a descriptive search comes up empty, list the folder unfiltered and look at the names and descriptions; page with `--limit` / `--offset` rather than trusting the first page. A folder often holds several bundles that all look plausible for a vague request — read `Description`, and if that is not enough, check one bundle's file names with `download` before answering from the wrong one.

## Commands

| Goal | Command |
|---|---|
| Find bundles | `uip or kb list --folder-path <p> [--search <text>] [--limit <n>] [--offset <n>] [--all-fields]` |
| One bundle's record | `uip or kb get <bundle-key> --folder-path <p>` |
| Create, empty | `uip or kb create <name> --folder-path <p> [-d <text>]` |
| Create + publish v1 from a directory | `uip or kb create <name> --folder-path <p> --input <dir> -m <message>` |
| Publish v1 into an existing empty bundle | `uip or kb publish <bundle-key> --folder-path <p> --input <dir> -m <message>` |
| Rename / re-describe | `uip or kb update <bundle-key> --folder-path <p> [-n <name>] [-d <text>]` |
| Remove from a folder | `uip or kb delete <bundle-key> --folder-path <p> --yes` |
| Share into / out of folders | `uip or kb share <bundle-key> --folder-path <p> [--add-folders <f...>] [--remove-folders <f...>]` |

| Version history | `uip or kb versions <bundle-key> --folder-path <p>` |
| Who changed one file, and when | `uip or kb history <bundle-key> --folder-path <p> --path <file>` |
| Unpack a version into a workspace | `uip or kb download <bundle-key> --folder-path <p> --destination <dir> [--version <n>]` |
| Whole version as a zip | `uip or kb archive <bundle-key> --folder-path <p> --destination <file>.zip [--version <n>]` |
| One file's content | `uip or kb file <bundle-key> --folder-path <p> --path <file> [--version <n>] [--destination <file>]` |
| One file across versions | `uip or kb history <bundle-key> --folder-path <p> --path <file>` |
| A version's derived artifact | `uip or kb build <bundle-key> --folder-path <p> --artifact graph.json` |
| What a local copy needs | `uip or kb sync <bundle-key> --folder-path <p> --input <dir>` |

Add `--output json` when you parse the result. It is the CLI's global output-format flag, and it is separate from `--destination`, which is where a command writes files.

## Reading a bundle as context

```bash
uip or kb download <bundle-key> --folder-path <p> --destination ./kb
```

That unpacks the version's files plus `./kb/.okf/base.json`, a marker recording the bundle, the version and its manifest. Read the markdown directly from disk. To check whether the copy is current, `sync` it — with no `--version` it compares against `latest`, and the report is **pull-direction**: `Changed` is what to download to match the published version, `Deleted` is what to remove locally. A file you deleted locally shows up in `Changed`, not `Deleted`.

## Publishing

`publish` and `create --input` only ever produce **version 1**, and only for a bundle with no content. A 409 from either means the bundle already has content: every later version comes from merging a change proposal (below). Never delete and re-create a bundle to work around it — that destroys the version history and the review record.

Both walk the directory, hash every file, upload only what the store lacks, then publish the manifest. Two rules the walk obeys:

- **Dot-prefixed files are skipped** unless `--include-hidden` is passed.
- **`.okf/`, `.git/` and `_refs/` are never published**, whatever the flags say — the format reserves them, and `_refs/` is where a download materializes *other* bundles' content. Publishing from a downloaded workspace is therefore safe.

## What the output means

`Author` on a version, a proposal or a comment is an opaque actor id — `user:<guid>` for a person, `agent/<producer>` for an agent. There is no CLI call that resolves it to a name or email, so report it as it comes rather than hunting for one.

`Failure` envelopes carry `Context.HttpStatus`. Two worth recognizing:

- **409 on `create`** → that name is already used in the folder. Pick another; do not retry. Names are unique per folder and other agents publish into the same folders, so give a generated bundle a distinguishing suffix rather than a bare word.
- **409 on `publish`** → the bundle already has content. Stop; this needs a change proposal.

`file` returns the content inline when it decodes as UTF-8 text, and refuses binary without `--destination <file>` — pass it rather than trying to read bytes from the envelope.

## Changing published content: `uip or kb change-proposal`

Every change after version 1 goes through a reviewed proposal. The loop, from an edited workspace:

```bash
uip or kb download <bundle-key> --folder-path <p> --destination ./kb   # writes .okf/base.json
# ...edit files under ./kb...
uip or kb change-proposal create --folder-path <p> --bundle-key <key> --input ./kb --title "<what changed>"
uip or kb change-proposal list-comments <proposal-id> --folder-path <p> --bundle-key <key> --since <last id> --unresolved
# ...address the feedback in the same workspace...
uip or kb change-proposal update <proposal-id> --folder-path <p> --bundle-key <key> --input ./kb
uip or kb change-proposal resolve-thread <thread-id> --folder-path <p> --bundle-key <key> --proposal <proposal-id> --body "Fixed in rev 2"
uip or kb change-proposal merge <proposal-id> --folder-path <p> --bundle-key <key>
```

Four things to know:

- **`create` and `update` need a workspace, not any directory.** They diff the files against `.okf/base.json`, which only a `download` writes, and that marker's version becomes the proposal's base. A directory without it is refused rather than proposed against a guessed version.
- **The proposal is the direct object, the bundle is scope.** So the proposal id is positional and the bundle is `--bundle-key`. Proposal ids are small integers (`1`, `7`), not GUIDs.
- **Resolving a thread is itself a comment.** Give `--body` something useful ("Fixed in rev 2"); a later reply reopens the thread.
- **`merge` can come back conflicted**, meaning the files moved in a newer version. Recovery is to download again, re-apply the edit, and open a new proposal — not to force anything.

`diff` before you merge — it is the only cheap check that the proposal contains what you think it does, and a merge publishes a version that cannot be edited afterwards.

### Reviewing someone else's proposal

The other half of the loop, and the one you land in when the proposal is not yours:

```bash
uip or kb change-proposal list --folder-path <p> --bundle-key <key> --status open
uip or kb change-proposal get <proposal-id> --folder-path <p> --bundle-key <key>
uip or kb change-proposal diff <proposal-id> --folder-path <p> --bundle-key <key>
uip or kb change-proposal add-comment <proposal-id> --folder-path <p> --bundle-key <key> \
  --body "Chargeback is not a refund — see the published definition" \
  --path concepts/chargeback.md --line 7
uip or kb change-proposal resolve-thread <root comment id> --folder-path <p> --bundle-key <key> \
  --proposal <proposal-id> --body "Rejected: contradicts v1"
uip or kb change-proposal merge <proposal-id> --folder-path <p> --bundle-key <key>   # accept
uip or kb change-proposal close <proposal-id> --folder-path <p> --bundle-key <key>   # reject
```

`list` is where you start: proposal ids come from it and from nowhere else. `--line` counts lines on the **proposal's new side**, not the published version — two proposals editing the same file will not agree on line numbers. Judge a proposal against the published content (`download` it, or `file` the documents it touches); a proposal that contradicts what is published needs evidence, not brevity.

A proposal with no reviewer is fine to `create` and `merge` yourself — comments are a record, not a gate.

## Not available yet

Cross-bundle references expanded under `_refs/` — the server does not build them yet, so a downloaded workspace holds only this bundle's own files. There is also no CLI surface for the bundle event feed; poll a proposal's comments with `--since` instead.
