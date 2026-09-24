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
7. **Inside a workspace, omit the key and the folder** — but read the stderr line that says which workspace answered, and pass `--folder-path` explicitly after switching tenants.
8. **Paths are bundle-relative and cannot climb.** A `--path` or `--artifact` containing a `.` or `..` segment is refused before any request is sent; pass the path as the manifest lists it.


## Step 0: Preflight — is this surface available?

Run once per session:

```bash
uip or kb --help
```

- **Succeeds** → continue.
- **`unknown command`** → the installed `uip` is a stable build. These commands register only on a prerelease build (`preview` / `dev` channel). Tell the user that plainly and stop — do not substitute bucket, asset or context-grounding commands, and do not guess an older command name.
- **A command runs but the platform refuses it** → the tenant does not have the knowledge-bundles feature enabled. Say so and stop; only an administrator can change it. A `403`/feature failure is not a login problem — never "fix" it by re-running `uip login`.

## Every command is folder-scoped

Bundles live in a folder and are not addressable without one. Pass `--folder-path <path>` (or `--folder-key <guid>`) on **every** command — unless you are working inside a downloaded workspace, which answers for both (below).

`uip or folders list --all` finds one — its flags are its own (`--all`, `--path <prefix>`, `--name`), not `kb list`'s `--search`. Pass its `Path` field to `--folder-path` (a top-level folder is just `Shared`, a nested one `Shared/Finance`) or its `Key` to `--folder-key` — `Name` is the display name and is not what either option wants.

Bundles are identified by a GUID (`Key`). Get it from `list`, never construct it.

On `share`, the scope (`--folder-path`) is the folder that already holds the bundle; `--add-folders` and `--remove-folders` name the folders being changed, and both apply in one call.

`--search` matches the bundle's **`Name` only** — not its description, and not the `title` inside its documents. A bundle named `ops-handbook-7` can hold a document titled "Contoso Operations Handbook", so searching what the user called it often returns an empty `Data: []` that reads like "no such bundle". When a descriptive search comes up empty, list the folder unfiltered and look at the names and descriptions; page with `--limit` / `--offset` rather than trusting the first page. A folder often holds several bundles that all look plausible for a vague request — read `Description`, and if that is not enough, check one bundle's file names with `download` before answering from the wrong one.

## Inside a workspace, the bundle and the folder are optional

`uip or kb download` writes `.okf/workspace.json`, and every verb except `delete` reads it — from the directory passed to `--input`, or by walking up from the working directory the way git finds a repository. So after a download:

```bash
cd ./kb
uip or kb versions                    # no key, no folder
uip or kb change-proposal create --input . --title "..."
```

Four things to rely on:

- **An explicit flag always wins.** Passing `--folder-path` uses that folder, not the workspace's.
- **The command says when it inferred.** A line on stderr — `Using the workspace at <dir> for the bundle and folder.` — means the target came from a marker, not from you. If you did not expect it, you are standing in someone's workspace.
- **`delete` never infers.** It always wants the key. Removing a bundle from a folder is the one action a wrong working directory cannot undo.
- **The marker records the folder, not the tenant.** After switching tenants, a bundle-addressed verb fails on the bundle's key, but `kb list` and `kb create` will resolve the folder in the *new* tenant and look perfectly successful. Pass `--folder-path` explicitly when you have changed sessions.

**Do not write anything else into the workspace either.** `change-proposal create` diffs the *whole* directory against the marker, so a file you drop in there — an archive you asked `kb archive --destination` for, an editor backup, a build artifact — becomes content the proposal adds. Write command output somewhere outside the workspace, and run `diff` before `merge` so you see what the proposal actually carries.

Do not write or edit `.okf/workspace.json` by hand — it also carries the manifest a change proposal diffs against, so an edited marker produces a wrong change set rather than an error. Re-run `download` to refresh it.

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
| What I changed, before proposing | `uip or kb status` inside a workspace |
| Whether a newer version exists | `uip or kb sync` inside a workspace, or `uip or kb sync <bundle-key> --folder-path <p> --input <dir>` |

Add `--output json` when you parse the result. It is the CLI's global output-format flag, and it is separate from `--destination`, which is where a command writes files.

## Reading a bundle as context

```bash
uip or kb download <bundle-key> --folder-path <p> --destination ./kb
```

That unpacks the version's files plus `./kb/.okf/workspace.json`, a marker recording the bundle, the version and its manifest. The server writes the marker into the archive, so one request brings both. Read the markdown directly from disk. To check whether the copy is current, `sync` it — with no `--version` it compares against `latest`, and the report is **pull-direction** — both lists are things to do, not a history. `Changed` is what to download to match the published version, `Deleted` what this version no longer carries. It compares the **checkout**, meaning the files the marker lists, so files of your own sitting in the same directory are not part of it and never show up in either list. A file you edited locally, and one you deleted locally, both show under `Changed`: for each of them "download this" is what makes the copy match. There is no apply command — `download` the version again (into a fresh directory for a clean copy, or over the same one and then remove what `Deleted` named).

## Publishing

`publish` and `create --input` only ever produce **version 1**, and only for a bundle with no content. A 409 from either means the bundle already has content: every later version comes from merging a change proposal (below). Never delete and re-create a bundle to work around it — that destroys the version history and the review record.

Both walk the directory, hash every file, and publish the manifest with the files inside the same request. A file larger than 16 MB cannot travel that way and is uploaded on its own first; either way it reaches the manifest as an ordinary entry, so nothing about the result depends on which path a file took. Two rules the walk obeys:

- **Dot-prefixed files are skipped** unless `--include-hidden` is passed.
- **`.okf/`, `.git/` and `_refs/` are never published**, whatever the flags say — the format reserves them, and `_refs/` is where a download materializes *other* bundles' content. Publishing from a downloaded workspace is therefore safe.

## What the output means

`Objects` is how many distinct objects the change set named, `Inlined` how many travelled inside the commit and `Uploaded` how many needed a request of their own. `Inlined` equal to `Objects` with `Uploaded: 0` is the ordinary case for documents; a non-zero `Uploaded` means a file was past the inline limit, which is a fact about size and not a problem to report.

`Author` on a version, a proposal or a comment is an opaque actor id — `user:<guid>` for a person, `agent/<producer>` for an agent. There is no CLI call that resolves it to a name or email, so report it as it comes rather than hunting for one.

`Failure` envelopes carry `Context.HttpStatus`. Two worth recognizing:

- **409 on `create`** → that name is already used in the folder. Pick another; do not retry. Names are unique per folder and other agents publish into the same folders, so give a generated bundle a distinguishing suffix rather than a bare word.
- **409 on `publish`** → the bundle already has content. Stop; this needs a change proposal.

`file` returns the content inline when it decodes as UTF-8 text, and refuses binary without `--destination <file>` — pass it rather than trying to read bytes from the envelope.

## Changing published content: `uip or kb change-proposal`

Every change after version 1 goes through a reviewed proposal. The loop, from an edited workspace:

```bash
uip or kb download <bundle-key> --folder-path <p> --destination ./kb   # writes .okf/workspace.json
# ...edit files under ./kb...
uip or kb change-proposal create --title "<what changed>"   # inside ./kb: folder, bundle and files all inferred
uip or kb change-proposal list-comments <proposal-id> --folder-path <p> --bundle-key <key> --since <last id> --unresolved
# ...address the feedback in the same workspace...
uip or kb change-proposal update <proposal-id>              # same inference; --input names another directory
uip or kb change-proposal resolve-thread <thread-id> --folder-path <p> --bundle-key <key> --proposal <proposal-id> --body "Fixed in rev 2"
uip or kb change-proposal merge <proposal-id> --folder-path <p> --bundle-key <key>
```

Four things to know:

- **Run `status` before you propose, and act on what it says.** `uip or kb status` prints the change set the next `change-proposal create` would carry — each path with `Kind: Added`, `Modified` or `Deleted` — and sends nothing. It runs offline: no bundle key, no folder, no session.

  Running it is half the job. **Read every path it lists and account for each one.** A path you did not touch is a file that drifted into the workspace — command output, an archive you asked for, an editor backup — and a proposal carries it into the bundle. Before proposing: delete it from the workspace if it is not meant to be published, or tell the user it is there and that proposing would add it. **Never open a proposal carrying a path you cannot explain**, and never treat `status` as a box to tick before running `create` anyway.
- **After a merge, your workspace is a version behind.** `download` again before you continue. The marker still names the version you checked out, so `status` will report everything you just shipped as if it were new — it is comparing against your old base, correctly, and it cannot know a newer version exists without asking. This is the one way to propose your own merged work a second time.
- **`status` and `sync` answer different questions.** `status` compares the working tree against the version you checked out; `sync` compares that checkout against a published version. An empty `status` does not mean your copy is current, and an empty `sync` does not mean you have nothing to propose.
- **`create` and `update` need a workspace, not any directory.** They diff the files against `.okf/workspace.json`, which only a `download` writes, and that marker's version becomes the proposal's base. `--input` is optional here and on `sync`: run them inside the workspace and the directory is found by walking up, the same way the bundle and folder are. A directory without a marker — and a working directory with no workspace above it — is refused rather than proposed against a guessed version. The stderr notice names exactly what the workspace supplied (`the files, the bundle and the folder`), so you can see when a flag of yours decided something instead.
- **The proposal is the direct object, the bundle is scope.** So the proposal id is positional and the bundle is `--bundle-key`. Proposal ids are small integers (`1`, `7`), not GUIDs.
- **Resolving a thread is itself a comment.** Give `--body` something useful ("Fixed in rev 2"); a later reply reopens the thread.
- **`merge` can come back conflicted**, meaning the files moved in a newer version. Recovery is to `download` again, re-apply the edit, and **`change-proposal update` the same proposal** — that takes its base to the new version and its status back to `Open`, and the review thread stays with it. Opening a new proposal also works but strands the existing comments on the old id. Never force anything. The failure carries `Data.Status: "Conflicted"`; `ErrorCode` is the same `invalid_argument` every merge refusal uses, so branch on `Data.Status`, not on the code.

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
