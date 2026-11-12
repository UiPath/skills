---
name: uipath-skill-bundles
description: "UiPath skill bundles via `uip or skill-bundles` — versioned file trees of agent skills stored in an Orchestrator folder. Create a bundle, publish a directory as a new version, download or read a version by number, tag or `latest`, compare a workspace with a version, and move version tags. PREVIEW: prerelease `uip` build and the skill-bundles feature only — Step 0 checks; a miss means stopping. For knowledge bundles, OKF documents or change proposals (`uip or kb`)→uipath-knowledge-bundles. For assets, queues, buckets, jobs→uipath-platform. For building the agent that uses the skills→uipath-agents."
when_to_use: "User says 'skill bundle', 'skill bundles', 'publish the skills to Orchestrator', 'download the skill bundle', 'which version of the skills', 'tag the skill bundle', 'pin the skills to a version', 'roll the tag back', 'uip or skill-bundles'. Also when the skills an agent loads are said to live in an Orchestrator folder rather than in the repo."
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Skill Bundles — `uip or skill-bundles`

A skill bundle is a folder-scoped Orchestrator entity holding a versioned file tree of agent skills. Versions are immutable and numbered (v1, v2, …). Reads take a number, a tag, or `latest`. Content is addressed by hash, so transfers move only what changed. `uip or skill-bundle` is an alias.

Knowledge bundles are a different kind with a different lifecycle: their later versions come only from reviewed change proposals, through `uip or kb`. Neither command group reaches the other kind's bundles.

## Critical Rules

1. **Preflight before anything else.** Run `uip or skill-bundles --help` once. `unknown command` means a stable build; a command the platform refuses means the tenant's skill-bundles feature is off. Both are stop conditions — say so and stop, never substitute `uip or kb`, bucket or asset commands.
2. **Every remote command needs a folder.** Pass `--folder-path <path>` or `--folder-key <guid>` every time, inside a workspace too. Only `status` runs without one.
3. **Publish only from a full workspace.** `publish` treats the directory as the whole next version: a file the base version has and the directory lacks is **deleted**. Download the version into a directory, edit there, publish that directory. Never publish a directory holding only the files you changed.
4. **A `publish` conflict is never solved by deleting the bundle.** A 409 means a file you touched changed after your base (or, on a first publish, that the bundle meanwhile got content). Download `latest` into a fresh directory, re-apply the edit, publish again. Deleting and re-creating destroys the version history and every tag.
5. **`--immutable` is permanent.** An immutable tag can never be moved or deleted, by anyone. Pass it only when the user asked for an immutable tag in those words.
6. **Moving a tag changes what every reader of it gets.** Confirm the target version with `versions` before `tags set`, and report the old and new version.
7. **A refusal is not a login problem, and a content 404 does not prove the bundle is missing.** Never re-run `uip login`, retry, or re-create the bundle to get past either. Follow Step 0.
8. **Paths are bundle-relative and cannot climb.** A `--path` with a `.` or `..` segment is refused before any request is sent; pass the path as the manifest lists it.

## Step 0: Preflight — is this surface available?

```bash
uip or skill-bundles --help
```

- **Succeeds** → continue.
- **`unknown command`** → the installed `uip` is a stable build; these commands register only on a prerelease (`preview` / `dev`) build. Tell the user and stop.
- **The platform refuses a command** (`permission_denied`, a feature refusal) → the tenant lacks the skill-bundles feature or you lack the permission. Say so and stop; only an administrator can change it.
- **A content command answers 404 `BundleDto does not exist.`** (`publish`, `create --input`, `versions`, `download`, `archive`, `file`, `history`, `sync`, `tags`) → this alone cannot tell a bundle hidden from you from a missing one. Run `get` once, on the same bundle in the same folder (`get` always reads the record), and branch on its envelope:
  - **Success** → you hold the bundle record but not skill-bundle content permission. Stop and report that.
  - **`not_found`** → the key or the folder is wrong. Ask the user which folder holds the bundle before listing any other folder.
  - **Any other failure** (`permission_denied`, a feature refusal, `server_error`) → stop and report it as it came. It does not show the bundle is missing.
- **`Skill bundle '<name>' does not exist in this folder.`** (`not_found`) → the name or the folder is wrong. Names match exactly, case included. Ask the user which folder holds the bundle before listing any other folder; never create one to fill the gap.
- **`This key is not a skill bundle.`** → the GUID names a knowledge bundle. Those belong to `uip or kb`, a different skill.

## Addressing a bundle

The bundle is positional and takes its **name or its key** (GUID): `uip or skill-bundles versions my-skills --folder-path Shared`. A name is matched exactly within the folder. Keys come from `list` or `get`; never construct one.

**Permissions.** Every remote content command — the first `publish` included — needs `SkillBundleContent.View`; a write also needs the matching `SkillBundleContent.Create`, `.Edit` or `.Delete`. A name is looked up through the bundle record, which also needs `SkillBundles.View`; a key skips the record. Report a missing grant as Step 0 says; only an administrator can add one.

`uip or folders list --all` finds a folder — pass its `Path` (`Shared`, `Shared/Finance`) to `--folder-path`, or its `Key` to `--folder-key`. `Name` is the display name and is neither.

`list --search` is a contains match on the name only. `list` reports no total, so `HasMore` is a guess from a full page: keep paging with `--limit` / `--offset` until a page comes back short. On `versions`, `history` and `tags list` the window is cut from the whole answer, so `--offset` counts rows.

## Commands

| Goal | Command |
|---|---|
| Find bundles | `uip or skill-bundles list --folder-path <p> [--search <text>] [--limit <n>] [--offset <n>] [--all-fields]` |
| One bundle's record | `uip or skill-bundles get <bundle> --folder-path <p>` |
| Create, empty | `uip or skill-bundles create <name> --folder-path <p> [-d <text>]` |
| Create + publish v1 from a directory | `uip or skill-bundles create <name> --folder-path <p> --input <dir> -m <message>` |
| Publish the next version | `uip or skill-bundles publish <bundle> --folder-path <p> --input <dir> -m <message>` |
| Rename / re-describe | `uip or skill-bundles update <bundle> --folder-path <p> [--name <name>] [-d <text>]` |
| Remove from a folder | `uip or skill-bundles delete <bundle> --folder-path <p> --yes` |
| Version history | `uip or skill-bundles versions <bundle> --folder-path <p> [--limit <n>] [--offset <n>]` |
| Unpack a version into a workspace | `uip or skill-bundles download <bundle> --folder-path <p> --destination <empty-dir> [--version <v>]` |
| Whole version as a zip | `uip or skill-bundles archive <bundle> --folder-path <p> --destination <file>.zip [--version <v>]` |
| One file's content | `uip or skill-bundles file <bundle> --folder-path <p> --path <file> [--version <v>] [--destination <file>]` |
| One file across versions | `uip or skill-bundles history <bundle> --folder-path <p> --path <file> [--version <v>] [--limit <n>] [--offset <n>]` |
| What I changed since download | `uip or skill-bundles status [--input <dir>]` |
| What a workspace needs to match a version | `uip or skill-bundles sync <bundle> --folder-path <p> [--input <dir>] [--version <v>]` |
| List tags | `uip or skill-bundles tags list <bundle> --folder-path <p>` |
| Create or move a tag | `uip or skill-bundles tags set <tag> --bundle <bundle> --folder-path <p> --version <n> [--immutable]` |
| Delete a mutable tag | `uip or skill-bundles tags delete <tag> --bundle <bundle> --folder-path <p> --yes` |

`<v>` is a version number, a tag, a `sha256:` tree digest, or `latest` (the default). On `tags set` and `tags delete` the tag is positional and the bundle is `--bundle`; `tags set --version` takes a number only. Add `--output json` when you parse the result; it is separate from `--destination`, which is where a command writes files. Skill bundles are not shared between folders from the CLI — there is no `share` command.

## Reading a bundle

```bash
uip or skill-bundles download <bundle> --folder-path <p> --destination ./skills --version <v>
```

`--destination` must be an empty directory or a new path. The command pins the selector to one version number first, so a tag that moves mid-download cannot mix two versions, and writes `./skills/.okf/workspace.json`, the marker recording the bundle, the version and its manifest. Read the files straight from disk. Do not write or edit the marker by hand: it is the base the next `publish` diffs against.

To see whether a workspace is current, `sync` it (against `latest` unless `--version` says otherwise). The report is **pull-direction**: `Changed` is what to download to match that version, `Deleted` what it no longer carries. Only files the marker lists are compared, so your own extra files never show. There is no apply command — `download` into a fresh directory.

## Publishing

```bash
uip or skill-bundles download <bundle> --folder-path <p> --destination ./skills
# ...edit files under ./skills...
uip or skill-bundles status --input ./skills            # offline: every path you are about to publish
uip or skill-bundles publish <bundle> --folder-path <p> --input ./skills -m "<what changed>"
```

- **The base comes from the marker.** In a downloaded workspace, `publish` diffs against the marker's version and sends only what changed, with every base file missing from the directory as a deletion (`DeletedPaths` in the result lists them; check it against what you meant to remove). A directory without a marker is accepted only for the first version: on a bundle with content it is refused with `This bundle already has content.` — download a workspace instead.
- **Run `status` first and account for every path.** `Kind: Added`, `Modified` or `Deleted` per path, computed offline. A path you did not touch — command output, an archive, an editor backup — would be published. Remove it from the workspace or tell the user; never publish a path you cannot explain. Write command output outside the workspace.
- **`--base-version <n>`** sets the base of a directory without a marker. Use it only when the user names the base explicitly; every file of version `<n>` the directory lacks is deleted. In a workspace it must equal the marker's version — to publish against another version, download that version into a fresh workspace.
- **Read `WorkspaceUpdated` after a publish.** `true`: the workspace's marker now records the new version, and it is ready for the next edit. `false`: the version was published, but the server's tree differs from your copy (someone else's disjoint edit landed with it), the marker could not be written, or the directory was never a workspace (a plain directory never gets one) — follow `NextStep` and `download` a fresh workspace before editing again.
- **What the walk skips.** Dot-prefixed files unless `--include-hidden`; `.okf/`, `.git/` and `_refs/` always.
- **`create --input` creates the record, then publishes v1** from a plain directory. A directory that is already a workspace, or holds no files, is refused before the record is created. If the publish half fails, the empty bundle remains: finish with `publish` on that bundle, not another `create` (the name is taken, 409).

`Objects` is how many distinct objects the change set named, `Inlined` how many travelled in the commit, `Uploaded` how many needed their own request (files past the 16 MiB inline limit). A non-zero `Uploaded` is a fact about size, not a problem.

## Tags

A tag names one version; every read accepts it in place of a number. Names: up to 128 letters, digits, `_`, `.` or `-`, not starting with `.` or `-`, not digits alone, not `latest`.

1. `tags list` to see what exists and whether each is `Immutable`.
2. `versions` to confirm the version the user means.
3. `tags set <tag> --bundle <bundle> --version <n>` creates or moves it; either needs skill-bundle content edit permission.
4. A 409 on `tags set` or `tags delete` means the tag is immutable. Stop and report it; do not delete the tag or pick another name without being asked.

## Failures worth recognizing

`Failure` envelopes carry `ErrorCode` and `Context.HttpStatus`.

| Answer | Meaning | Do |
|---|---|---|
| 409 on `create` | Name already used in this folder | Pick another name; give a generated bundle a distinguishing suffix |
| `This bundle already has content.` | Plain directory, bundle has versions | Download a workspace and publish from it |
| 409 on later `publish` | A file you touched changed after your base | Download `latest`, re-apply, publish again (Rule 4) |
| 409 on `tags set` / `tags delete` | Tag is immutable | Stop and report |
| `There are no content changes to publish.` | Directory equals the base | Nothing to do; say so |
| `The workspace belongs to another bundle.` | Marker names a different bundle | Download this bundle into its own directory |
| `--base-version must match this workspace's base.` | Workspace marker disagrees with `--base-version` | Drop the flag, or download that version into a fresh workspace |
| `The source is already a workspace.` | `create --input` on a downloaded workspace | Copy the content into a plain directory first |
| 404 `BundleDto does not exist.` | Content hidden from you, or a wrong key or folder | Step 0: run `get` and branch on its answer |
| `invalid_argument` before any request | Bad version selector, path, or missing folder | Fix the argument; retrying unchanged will not help |

## Not available

No `share` (the server's share route is not exposed to the CLI), no `build` (skill bundles have no build artifacts), no change proposals or review comments (knowledge bundles only), and no command that applies a `sync` report in place.
