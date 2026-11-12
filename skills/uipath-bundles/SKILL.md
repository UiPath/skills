---
name: uipath-bundles
description: "UiPath Orchestrator bundles — versioned file trees in an Orchestrator folder, one command group per kind: knowledge bundles (`uip or kb`, Open Knowledge Format documents an agent reads as context, changed through reviewed change proposals) and skill bundles (`uip or skill-bundles`, the agent skills an agent loads, published directly, with version tags). Find, create, download, read a version or file, publish, compare a workspace, propose and merge (knowledge), tag (skills). PREVIEW: both command groups exist only on a prerelease `uip` build, and only on tenants with that kind's feature enabled — Step 0 checks; a miss means stopping. For Orchestrator assets, queues, buckets, jobs→uipath-platform. For context grounding / semantic search indexes→uipath-platform. For `uip solution` lifecycle→uipath-solution. For building the agent that uses the skills→uipath-agents."
when_to_use: "User says 'bundle', 'knowledge bundle', 'skill bundle', 'OKF', 'Open Knowledge Format', 'download the bundle', 'publish docs to Orchestrator', 'publish the skills to Orchestrator', 'what version of the bundle', 'bundle manifest', 'change proposal on a bundle', 'merge the proposal', 'comment on the proposal', 'tag the skill bundle', 'pin the skills to a version', 'roll the tag back', 'uip or kb', 'uip or skill-bundles'. Also when the documents an agent reads, or the skills it loads, are said to live in an Orchestrator folder rather than in the repo."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Bundles — `uip or kb` and `uip or skill-bundles`

A bundle is a folder-scoped Orchestrator entity holding a versioned file tree. Versions are immutable and numbered (v1, v2, …). Content is addressed by hash, so transfers move only what changed. Each kind has its own command group, and the two lifecycles differ where it matters most:

| | Knowledge bundle | Skill bundle |
|---|---|---|
| Holds | Markdown documents (Open Knowledge Format) an agent reads as context | Agent skills an agent loads |
| Command group | `uip or kb` | `uip or skill-bundles` (alias `uip or skill-bundle`) |
| Bundle argument | Its key (GUID) | Its name or its key |
| Version 1 | `publish` or `create --input` | `publish` or `create --input` |
| Later versions | Only by merging a reviewed change proposal | `publish` from a workspace |
| Reads take | A version number or `latest` | A number, a tag, a `sha256:` tree digest, or `latest` |
| Only here | Change proposals, `share`, `build` | Version tags |

## Critical Rules

1. **Identify the kind first, and keep each key with its group.** The kind is the one the user or task names (knowledge documents / OKF / proposals → `kb`; skills / tags → `skill-bundles`). When only a key is known, the group whose `get` (or `list`) returns the record owns it. Never pass one kind's key to the other group: it is refused with `This key is not a knowledge bundle.` or `This key is not a skill bundle.` — switch groups, do not retry.
2. **Preflight that group before anything else** (Step 0). `unknown command` means a stable build; a command the platform refuses means the tenant's feature for that kind is off. Both are stop conditions — say so and stop, never substitute the other group, bucket, asset or context-grounding commands.
3. **Every command needs a folder.** `--folder-path <FOLDER_PATH>` or `--folder-key <FOLDER_KEY>` every time. The one exception: inside a downloaded knowledge-bundle workspace `kb` reads the folder and bundle from the marker. Skill-bundle commands always take the folder; only `skill-bundles status` runs without one.
4. **Keys and ids come from the CLI, never from you.** Bundle keys from `list` or `get`, proposal ids from `change-proposal list`. Do not construct, guess, or carry one over from another folder.
5. **Later versions follow the kind.** A knowledge bundle's `publish` and `create --input` only ever make version 1; every later version comes from merging a change proposal. A skill bundle's `publish` takes the directory as the whole next version, so publish only from a full workspace: a base file the directory lacks is **deleted** (hidden files excepted, see Skill bundles).
6. **A 409 is never solved by deleting the bundle.** Deleting and re-creating destroys the version history, the review record and every tag. What each 409 means is in Failures.
7. **A refusal is not a login problem, and a content 404 does not prove the bundle is missing.** A 403 or a feature refusal needs an administrator. A 404 `BundleDto does not exist.` from a content command needs the `get` check in Step 0 before anything else. Never re-run `uip login`, retry, or re-create the bundle to get past either.
8. **Paths are bundle-relative and cannot climb.** A `--path` or `--artifact` with a `.` or `..` segment is refused before any request is sent; pass the path as the manifest lists it.
9. **Irreversible steps need their check first.** Knowledge: `diff` before `merge` — a merge publishes a version that cannot be edited. Skills: `--immutable` only when the user asked for an immutable tag in those words; confirm the version with `versions` before `tags set`; `publish --yes` only after the user approved the `DeletedPaths`.

## Step 0: Preflight — is this surface available?

Run once per session, for the group the kind needs:

```bash
uip or kb --help
uip or skill-bundles --help
```

- **Succeeds** → continue.
- **`unknown command`** (either group) → the installed `uip` is a stable build. Both groups register only on a prerelease build (`preview` / `dev` channel). Tell the user that plainly and stop — do not substitute the other group, bucket, asset or context-grounding commands, and do not guess an older command name.
- **The platform refuses a command** (`permission_denied`, a feature refusal) → the tenant lacks that kind's feature (knowledge bundles and skill bundles are enabled separately), or you lack the permission. Say so and stop; only an administrator can change it. It is not a login problem — never "fix" it by re-running `uip login`.
- **A content command answers 404 `BundleDto does not exist.`** (`versions`, `download`, `archive`, `file`, `history`, `sync`, `publish`, `create --input`, `kb build`, `skill-bundles tags`, or the upload step of `change-proposal create`/`update`) → that alone cannot tell a bundle hidden from you from a missing one. Run `get` once, on the same bundle in the same folder (`get` always reads the record), and branch on its envelope:
  - **Success** → you hold the bundle record but not that kind's content permission. Stop and report that; never re-create the bundle or retry.
  - **`ErrorCode: not_found`** → the key or the folder may be wrong. Ask the user which folder holds the bundle before listing any other folder; never re-create it.
  - **Any other failure** (`permission_denied`, a feature refusal, `server_error`, a network error) → stop and report it as it came. It does not show the bundle is missing.
- **`Skill bundle '<NAME>' does not exist in this folder.`** (`not_found`) → the name or the folder is wrong. Names match exactly, case included. Ask the user which folder holds the bundle before listing any other folder; never create one to fill the gap.
- **`This key is not a knowledge bundle.`** / **`This key is not a skill bundle.`** (`invalid_argument`, before any content is read) → the key belongs to the other kind (Rule 1). Do not retry with this group.

## Folders, keys and paging

`uip or folders list --all` finds a folder — its flags are its own (`--all`, `--path <PREFIX>`, `--name`), not `list`'s `--search`. Pass its `Path` (`Shared`, `Shared/Finance`) to `--folder-path`, or its `Key` to `--folder-key`. `Name` is the display name and is neither.

**Permissions.** Each kind splits them the same way: one set for the bundle record, one for its content. For skill bundles, every remote content command — the first `publish` included — needs `SkillBundleContent.View`; a write also needs the matching `SkillBundleContent.Create`, `.Edit` or `.Delete`. A skill-bundle name is looked up through the record, which also needs `SkillBundles.View`; a key skips the record. Report a missing grant as Step 0 says.

`--search` matches the bundle's **`Name` only** — not its description, and not the `title` inside its documents. A bundle named `ops-handbook-7` can hold a document titled "Contoso Operations Handbook", so searching what the user called it often returns an empty `Data: []` that reads like "no such bundle". When a descriptive search comes up empty, list the folder unfiltered and look at the names and descriptions. A folder often holds several plausible bundles — read `Description`, and if that is not enough, check one bundle's file names with `download` before answering from the wrong one. A skill-bundle name is matched exactly within the folder.

Page with `--limit` / `--offset`. `versions`, `history`, `tags list`, `change-proposal list` and `change-proposal list-comments` cut the window from the whole answer, so `--offset` counts rows, `Pagination.Total` is exact and `HasMore` is false on the last window. `skill-bundles list` reads one row past the page, so its `HasMore` is exact. `kb list` reports no total, so its `HasMore` is a guess from a full page: keep paging until a page comes back short.

On `kb share`, the scope (`--folder-path`) is the folder that already holds the bundle; `--add-folders` and `--remove-folders` name the folders being changed, and both apply in one call. Skill bundles are not shared from the CLI.

## Commands

Knowledge bundles — `uip or kb`:

| Goal | Command |
|---|---|
| Find bundles | `uip or kb list --folder-path <FOLDER_PATH> [--search <TEXT>] [--limit <LIMIT>] [--offset <OFFSET>] [--all-fields]` |
| One bundle's record | `uip or kb get <BUNDLE_KEY> --folder-path <FOLDER_PATH>` |
| Create, empty | `uip or kb create <NAME> --folder-path <FOLDER_PATH> [-d <TEXT>]` |
| Create + publish v1 from a directory | `uip or kb create <NAME> --folder-path <FOLDER_PATH> --input <DIRECTORY> -m <MESSAGE>` |
| Publish v1 into an existing empty bundle | `uip or kb publish <BUNDLE_KEY> --folder-path <FOLDER_PATH> --input <DIRECTORY> -m <MESSAGE>` |
| Rename / re-describe | `uip or kb update <BUNDLE_KEY> --folder-path <FOLDER_PATH> [-n <NAME>] [-d <TEXT>]` |
| Remove from a folder | `uip or kb delete <BUNDLE_KEY> --folder-path <FOLDER_PATH> --yes` |
| Share into / out of folders | `uip or kb share <BUNDLE_KEY> --folder-path <FOLDER_PATH> [--add-folders <FOLDER...>] [--remove-folders <FOLDER...>]` |
| Version history | `uip or kb versions <BUNDLE_KEY> --folder-path <FOLDER_PATH> [--limit <LIMIT>] [--offset <OFFSET>]` |
| One file across versions | `uip or kb history <BUNDLE_KEY> --folder-path <FOLDER_PATH> --path <PATH> [--limit <LIMIT>] [--offset <OFFSET>]` |
| Unpack a version into a workspace | `uip or kb download <BUNDLE_KEY> --folder-path <FOLDER_PATH> --destination <DIRECTORY> [--version <VERSION>]` |
| Whole version as a zip | `uip or kb archive <BUNDLE_KEY> --folder-path <FOLDER_PATH> --destination <ZIP_FILE> [--version <VERSION>]` |
| One file's content | `uip or kb file <BUNDLE_KEY> --folder-path <FOLDER_PATH> --path <PATH> [--version <VERSION>] [--destination <FILE>]` |
| A version's derived artifact | `uip or kb build <BUNDLE_KEY> --folder-path <FOLDER_PATH> --artifact graph.json` |
| What I changed, before proposing | `uip or kb status` inside a workspace |
| Whether a newer version exists | `uip or kb sync` inside a workspace, or `uip or kb sync <BUNDLE_KEY> --folder-path <FOLDER_PATH> --input <DIRECTORY>` |

Skill bundles — `uip or skill-bundles`:

| Goal | Command |
|---|---|
| Find bundles | `uip or skill-bundles list --folder-path <FOLDER_PATH> [--search <TEXT>] [--limit <LIMIT>] [--offset <OFFSET>] [--all-fields]` |
| One bundle's record | `uip or skill-bundles get <BUNDLE> --folder-path <FOLDER_PATH>` |
| Create, empty | `uip or skill-bundles create <NAME> --folder-path <FOLDER_PATH> [-d <TEXT>]` |
| Create + publish v1 from a directory | `uip or skill-bundles create <NAME> --folder-path <FOLDER_PATH> --input <DIRECTORY> -m <MESSAGE>` |
| Publish the next version | `uip or skill-bundles publish <BUNDLE> --folder-path <FOLDER_PATH> --input <DIRECTORY> -m <MESSAGE> [--yes]` |
| Rename / re-describe | `uip or skill-bundles update <BUNDLE> --folder-path <FOLDER_PATH> [--name <NAME>] [-d <TEXT>]` |
| Remove from a folder | `uip or skill-bundles delete <BUNDLE> --folder-path <FOLDER_PATH> --yes` |
| Version history | `uip or skill-bundles versions <BUNDLE> --folder-path <FOLDER_PATH> [--limit <LIMIT>] [--offset <OFFSET>]` |
| Unpack a version into a workspace | `uip or skill-bundles download <BUNDLE> --folder-path <FOLDER_PATH> --destination <NEW_DIRECTORY> [--version <VERSION>]` |
| Whole version as a zip | `uip or skill-bundles archive <BUNDLE> --folder-path <FOLDER_PATH> --destination <ZIP_FILE> [--version <VERSION>]` |
| One file's content | `uip or skill-bundles file <BUNDLE> --folder-path <FOLDER_PATH> --path <PATH> [--version <VERSION>] [--destination <FILE>]` |
| One file across versions | `uip or skill-bundles history <BUNDLE> --folder-path <FOLDER_PATH> --path <PATH> [--version <VERSION>] [--limit <LIMIT>] [--offset <OFFSET>]` |
| What I changed since download | `uip or skill-bundles status [--input <DIRECTORY>]` |
| What a workspace needs to match a version | `uip or skill-bundles sync <BUNDLE> --folder-path <FOLDER_PATH> [--input <DIRECTORY>] [--version <VERSION>]` |
| List tags | `uip or skill-bundles tags list <BUNDLE> --folder-path <FOLDER_PATH>` |
| Create or move a tag | `uip or skill-bundles tags set <TAG> --bundle <BUNDLE> --folder-path <FOLDER_PATH> --version <VERSION_NUMBER> [--immutable]` |
| Delete a mutable tag | `uip or skill-bundles tags delete <TAG> --bundle <BUNDLE> --folder-path <FOLDER_PATH> --yes` |

`<VERSION>` is what the kind's reads take (table above). On `tags set` and `tags delete` the tag is positional and the bundle is `--bundle`; `tags set --version` takes a number only. Add `--output json` when you parse the result. It is the CLI's global output-format flag, and it is separate from `--destination`, which is where a command writes files.

## Workspaces and the `.okf` marker

`download` unpacks a version's files plus `.okf/workspace.json`, a marker recording the bundle, the version and its manifest. Read the files straight from disk. The marker is the base the next change set diffs against — a knowledge-bundle proposal or a skill-bundle publish.

- **Do not write or edit the marker by hand.** An edit that breaks its shape (a hash that is not `sha256:` plus 64 hex, a path with `..` or a leading `/`, a version below 1) is refused with `invalid_argument` and a message saying the marker is not valid; an edit that keeps the shape valid is worse — it produces a wrong change set rather than an error. A marker the OS will not let you open is `local_permission_denied`, with the file in `Context.path`. Either way, download the version again.
- **Do not write anything else into the workspace either.** The next change set covers the *whole* directory, so a file you drop in — an archive you asked `archive --destination` for, an editor backup, a build artifact — becomes content it adds. Write command output outside the workspace.
- **Run `status` before any change set, and account for every path.** It prints each path with `Kind: Added`, `Modified` or `Deleted`, offline, and sends nothing. A path you did not touch is a file that drifted in — delete it from the workspace if it is not meant to be published, or tell the user it is there. **Never send a change set carrying a path you cannot explain**, and never treat `status` as a box to tick.
- **`status` and `sync` answer different questions.** `status` compares the working tree against the version you checked out; `sync` compares that checkout against a published version (`latest` unless `--version` says otherwise). Its report is **pull-direction**: `Changed` is what to download to match, `Deleted` what that version no longer carries. Only the files the marker lists are compared, so your own extra files never show. A file you edited or deleted locally shows under `Changed`. An empty `status` does not mean your copy is current, and an empty `sync` does not mean you have nothing to send. There is no apply command — `download` again.
- **A bundle key that disagrees with the workspace is refused, not preferred** (`The workspace belongs to another bundle.` on skill bundles). Drop the key, or download that bundle into its own directory.

Where the two kinds differ:

| | Knowledge bundle | Skill bundle |
|---|---|---|
| `--destination` | A directory; downloading again over the same one removes the files the new version dropped when you had not touched them (`Data.Removed`) and leaves the edited ones (`Data.Kept`) — check `Kept` before proposing, each is a file the next proposal would add back | A path that does not exist yet: never an existing directory, even an empty one, and do not create it first. An existing path is refused with `The destination already exists.` before any request. The selector is pinned to one version number first, so a tag that moves mid-download cannot mix two versions |
| A failed download | Refused with `server_error` → the archive named a different bundle or version than asked; nothing was written. Retry the same command, report it if it persists; never `archive` plus a manual unzip instead — that marker is the wrong base | A download that fails while writing leaves no workspace behind — no marker, no partial files, and an existing path is never removed — so once its cause is fixed (disk space, a local permission, a dropped connection) download again into a new path |
| Inside a workspace | Every verb except `delete` reads the marker — from `--input`, or by walking up from the working directory like git — so the key and the folder can be omitted. An explicit flag always wins. A stderr line `Using the workspace at <dir> for the bundle and folder.` says the target came from a marker; if you did not expect it, you are standing in someone's workspace. `delete` never infers. The marker records the folder, not the tenant: after switching tenants pass `--folder-path` explicitly — `kb list` and `kb create` would resolve the folder in the *new* tenant and look successful | Nothing is inferred: pass the bundle and the folder every time. `status` and `sync` take the directory with `--input`, or the working directory |

A refusal, a content 404 or a wrong-kind key fails before anything is written and is not retried: follow Step 0.

## Version 1 and `create --input`

`publish` into a bundle with no content, or `create --input`, produces **version 1**. Both walk the directory, hash every file, and publish the manifest with the files in the same request; a file past the 16 MiB inline limit is uploaded on its own first and reaches the manifest as an ordinary entry. The walk skips dot-prefixed files unless `--include-hidden`, and never publishes `.okf/`, `.git/` or `_refs/` (`_refs/` is where a download materializes *other* bundles' content). On knowledge bundles a symlink is judged by what it points at: `public -> .secrets` is skipped like `.secrets` unless `--include-hidden`, a link into `.git/` or `.okf/` is never published, and a link that resolves outside the workspace is not followed — put the file itself in the directory.

**`create --input` checks the directory, creates the record, then publishes.** A bad `--input` is refused before anything is created; a skill-bundle `create --input` also refuses a directory that is already a workspace (`The source is already a workspace.` — copy the content into a plain directory) or holds no files. When the publish half fails, the failure says `Bundle '<KEY>' was created, but its initial publication was not confirmed.` (the name in place of the key when the server returned none) and carries `Data.Name`, `Data.RecordCreated: true`, `Data.PublicationConfirmed: false` and, when known, `Data.Key`; its `Instructions` print the exact commands for this folder. `PublicationConfirmed: false` means the CLI got no confirmed commit, not that the bundle is empty — an interrupted request may still have landed. A failure with `Data.RecordCreated: true` is this case whatever its HTTP status, a 409 included.

1. Without `Data.Key`, first `list` the same folder with `--search` set to `Data.Name` and take the key of the exact name match, before anything else.
2. Run `versions` on that key in the same folder (and tenant): version 1 listed → the content is published, nothing more to do.
3. 404 `Bundle '<KEY>' has no content yet.` (or a successful empty list) → `publish` that key from the same directory.
4. Any other `versions` failure → stop and report it (Step 0) — it does not show the bundle is empty.

Never repeat `create` (the name is now taken) and never delete the record to retry. The bundle is new, so a knowledge bundle never needs a change proposal here.

`Objects` is how many distinct objects a change set named, `Inlined` how many travelled inside the commit and `Uploaded` how many needed a request of their own. `Inlined` equal to `Objects` with `Uploaded: 0` is the ordinary case; a non-zero `Uploaded` means a file was past the inline limit — a fact about size, not a problem. `Author` on a version, a proposal or a comment is an opaque actor id — `user:<guid>` for a person, `agent/<producer>` for an agent; no CLI call resolves it to a name, so report it as it comes.

## Knowledge bundles: later versions by change proposal

Every change after version 1 goes through a reviewed proposal. The loop, from an edited workspace:

```bash
uip or kb download <BUNDLE_KEY> --folder-path <FOLDER_PATH> --destination ./kb   # writes .okf/workspace.json
# ...edit files under ./kb...
uip or kb status                                            # every path the proposal will carry
uip or kb change-proposal create --title "<TITLE>"          # inside ./kb: folder, bundle and files all inferred
uip or kb change-proposal list-comments <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY> --since <LAST_COMMENT_ID> --unresolved --limit 50
# ...address the feedback in the same workspace...
uip or kb change-proposal update <PROPOSAL_ID>              # same inference; --input names another directory
uip or kb change-proposal resolve-thread <THREAD_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY> --proposal <PROPOSAL_ID> --body "Fixed in rev 2"
uip or kb change-proposal diff <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY>
uip or kb change-proposal merge <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY>
```

- **`create` and `update` need a workspace, not any directory.** They diff the files against the marker, whose version becomes the proposal's base. `--input` is optional here and on `sync`: inside the workspace the directory is found by walking up. A directory without a marker is refused rather than proposed against a guessed version. The stderr notice names what the workspace supplied (`the files, the bundle and the folder`).
- **After a merge, your workspace is a version behind.** `download` again before you continue: the marker still names the version you checked out, so `status` would report everything you just shipped as new — the one way to propose your own merged work a second time.
- **The proposal is the direct object, the bundle is scope.** The proposal id is positional and the bundle is `--bundle-key`. Proposal ids are small integers (`1`, `7`), not GUIDs.
- **Resolving a thread is itself a comment.** Give `--body` something useful ("Fixed in rev 2"); a later reply reopens the thread.
- **`merge` can come back conflicted**, meaning the files moved in a newer version. `download` again, re-apply the edit, and **`change-proposal update` the same proposal** — that takes its base to the new version and its status back to `Open`, and the review thread stays with it. Opening a new proposal also works but strands the existing comments on the old id. Never force anything. The failure carries `Data.Status: "Conflicted"`; `ErrorCode` is the same `invalid_argument` every merge refusal uses, so branch on `Data.Status`, not on the code.

Reviewing someone else's proposal:

```bash
uip or kb change-proposal list --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY> --status open --limit 20
uip or kb change-proposal get <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY>
uip or kb change-proposal diff <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY>
uip or kb change-proposal add-comment <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY> \
  --body "Chargeback is not a refund — see the published definition" \
  --path concepts/chargeback.md --line 7
uip or kb change-proposal resolve-thread <ROOT_COMMENT_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY> \
  --proposal <PROPOSAL_ID> --body "Rejected: contradicts v1"
uip or kb change-proposal merge <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY>   # accept
uip or kb change-proposal close <PROPOSAL_ID> --folder-path <FOLDER_PATH> --bundle-key <BUNDLE_KEY>   # reject
```

`list` is where you start: proposal ids come from it and from nowhere else. `--line` counts lines on the **proposal's new side**, not the published version — two proposals editing the same file will not agree on line numbers. Judge a proposal against the published content (`download` it, or `file` the documents it touches); a proposal that contradicts what is published needs evidence, not brevity. A proposal with no reviewer is fine to `create` and `merge` yourself — comments are a record, not a gate.

`kb file` returns the content inline when it decodes as UTF-8 text, and refuses binary without `--destination <FILE>` — pass it rather than reading bytes from the envelope.

## Skill bundles: later versions by `publish`, and tags

```bash
uip or skill-bundles download <BUNDLE> --folder-path <FOLDER_PATH> --destination ./skills
# ...edit files under ./skills...
uip or skill-bundles status --input ./skills            # offline: every path you are about to publish
uip or skill-bundles publish <BUNDLE> --folder-path <FOLDER_PATH> --input ./skills -m "<MESSAGE>"
```

- **The base comes from the marker.** In a downloaded workspace, `publish` diffs against the marker's version and sends only what changed, with every base file missing from the directory as a deletion (`DeletedPaths` in the result lists them; check it against what you meant to remove). A directory without a marker is accepted only for the first version: on a bundle with content it is refused with `This bundle already has content.` — download a workspace instead.
- **`--base-version <BASE_VERSION>`** sets the base of a directory without a marker. Use it only when the user names the base explicitly; every non-hidden file of version `<BASE_VERSION>` the directory lacks is deleted. When that would delete anything, `publish` stops first, uploading nothing: `ErrorCode: confirmation_required` (exit 1) with `Data.DeletedPaths`. Show the user every path in `DeletedPaths` and ask; re-run with `--yes` only after they agree. Never add `--yes` on your own — and when the intent is an edit, download a workspace instead. In a workspace `--base-version` must equal the marker's version — to publish against another version, download that version into a fresh workspace.
- **Read `WorkspaceUpdated` after a publish.** `true`: the workspace's marker now records the new version, and it is ready for the next edit. `false`: the version was published, but the server's tree differs from your copy (someone else's disjoint edit landed with it), the marker could not be written, or the directory was never a workspace (a plain directory never gets one) — follow `NextStep` and `download` a fresh workspace before editing again.
- **Hidden files are left out on both sides by default.** A dot-prefixed file in the directory is not published, a dot-prefixed base file the directory lacks is kept rather than deleted, and `status` reports neither. To add, edit or delete hidden content on purpose, pass `--include-hidden` to both `status` and `publish`.

**Tags.** A tag names one version; every read accepts it in place of a number. Names: up to 128 letters, digits, `_`, `.` or `-`, not starting with `.` or `-`, not digits alone, not `latest`.

1. `tags list` to see what exists and whether each is `Immutable`.
2. `versions` to confirm the version the user means.
3. `tags set <TAG> --bundle <BUNDLE> --version <VERSION_NUMBER>` creates or moves it; either needs skill-bundle content edit permission. Moving a tag changes what every reader of it gets — report the old and new version.
4. A 409 on `tags set` or `tags delete` means the tag is immutable. Stop and report it; do not delete the tag or pick another name without being asked.

## Failures worth recognizing

`Failure` envelopes carry `ErrorCode` and `Context.HttpStatus`.

| Answer | Kind | Meaning | Do |
|---|---|---|---|
| `Data.RecordCreated: true`, `PublicationConfirmed: false` (any status, 409 included) | Both | `create --input` made the record; its publish was not confirmed | Recover as Version 1 and `create --input` describes; never repeat `create` |
| 409 on `create` without `Data.RecordCreated` | Both | Name already used in this folder; nothing was created | Pick another name; give a generated bundle a distinguishing suffix — other agents publish into the same folders |
| 409 on `publish` | Knowledge | The bundle already has content | Stop; this needs a change proposal — unless you are finishing a `create --input` that reported `RecordCreated: true`, where it means version 1 landed |
| 409 on a later `publish` | Skills | A file you touched changed after your base | Download `latest` into a fresh directory, re-apply, publish again |
| 409 on `tags set` / `tags delete` | Skills | Tag is immutable | Stop and report |
| `This key is not a knowledge bundle.` / `This key is not a skill bundle.` | Both | The key belongs to the other kind | Use the other command group (Rule 1) |
| 404 `BundleDto does not exist.` | Both | Content hidden from you, or a wrong key or folder | Step 0: run `get` and branch on its answer |
| `This bundle already has content.` | Skills | Plain directory, bundle has versions | Download a workspace and publish from it |
| `confirmation_required` on `publish` | Skills | Plain directory with `--base-version` would delete `Data.DeletedPaths`; nothing was sent | Show the user `DeletedPaths` and ask; re-run with `--yes` only on their approval |
| `--base-version must match this workspace's base.` | Skills | Workspace marker disagrees with `--base-version` | Drop the flag, or download that version into a fresh workspace |
| `The destination already exists.` | Skills | `download --destination` names an existing path, even an empty directory | Pass a path that does not exist; do not create it first |
| `There are no content changes to publish.` | Skills | Directory equals the base | Nothing to do; say so |
| `invalid_argument` before any request | Both | Bad version selector, path, marker, or missing folder | Fix the argument; retrying unchanged will not help |

## Not available

Cross-bundle references expanded under `_refs/` — the server does not build them yet, so a downloaded workspace holds only its own bundle's files. No CLI surface for the bundle event feed; poll a proposal's comments with `--since` instead. Skill bundles have no `share` (the server's share route is not exposed to the CLI), no `build` (no build artifacts), and no change proposals; no command applies a `sync` report in place.
