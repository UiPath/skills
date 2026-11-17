# `.git-studioweb` Repository Layout

How to run git, VS Code, or any local tool against a solution folder whose repository Studio Web keeps in a `.git-studioweb` folder instead of a `.git` folder.

<!--skill-flavor:git-studioweb-host-extra:start-->
<!--skill-flavor:git-studioweb-host-extra:end-->

## What and Why

Chrome 159 and later refuse to let a web page create any entry named `.git` (folder or file) in a folder opened through the File System Access API. Studio Web therefore creates a new local repository in a `.git-studioweb` folder at the solution root. An existing `.git` folder keeps working and always wins.

Three different things, never interchangeable:

| Term | What it is |
|---|---|
| the `.git` folder | A normal git repository. |
| the `.git` file | A one-line text file at the solution root containing exactly `gitdir: .git-studioweb` plus a line ending (LF, CRLF, or none). Native git, VS Code, and GitHub Desktop follow it into `.git-studioweb` (the mechanism submodules and worktrees use). Only a tool outside the browser can create it. |
| the `.git-studioweb` folder | Holds what a `.git` folder holds (`HEAD`, `objects/`, `refs/`, `index`, `info/exclude`). Studio Web adds `.git-studioweb/` to `.git-studioweb/info/exclude`, so `git add .` skips it. |

Without the `.git` file, native git and VS Code see no repository in the folder. Creating the `.git` file is called **linking**.

## Detect the State

Check the solution root (the folder holding the `.uipx`):

| On disk | State | Action |
|---|---|---|
| `.git` folder only | Native repository | Nothing to do. |
| `.git-studioweb` folder, no `.git` entry | Unlinked: git reports `not a git repository` | Link ([Link With the CLI](#link-with-the-cli)); for read-only work see [Read Without Linking](#read-without-linking). |
| `.git-studioweb` folder + `.git` file containing exactly `gitdir: .git-studioweb` | Linked | Nothing to do. |
| `.git-studioweb` folder + `.git` file with any other content | Broken: native git fails or opens another repository; Studio Web refuses it (`GitPointerError`) | Show the user the file content. Rewrite it only with their consent (`--force`). |
| `.git` folder AND `.git-studioweb` folder | Split: `.git` folder wins in git, VS Code and Studio Web; Studio Web's commits stay only in `.git-studioweb`. The CLI reports `NativeRepository` plus a `Data.Warnings` entry and changes nothing | Leave both alone. Follow [When a `.git` Folder and `.git-studioweb` Both Exist](#when-a-git-folder-and-git-studioweb-both-exist). |
| `.git-studioweb` is a symlink, not a real folder | Unsupported | Do not link. Tell the user. |
| `.git-studioweb` folder holds unexpected entries (see [Unexpected Entries](#unexpected-entries)) | Refused: `git-link` (with or without `--force`) fails with `configuration_error`, `Data.Problem` `UnexpectedRepositoryEntries` | Stop. Show the user the listed entries. Never delete them or bypass the refusal yourself. |
| `.git` is a symlink or any other entry that is neither a regular file nor a folder | Unsupported; `git-link` refuses it, even with `--force` | Leave it. Tell the user. |

```bash
ls -la <SOLUTION_DIR>
uip solution git-link --check <SOLUTION_DIR> --output json
```

`ls -la` lists the `.git` entry and shows whether it is a folder (`d`), a file, or a symlink (`l`); in PowerShell use `Get-ChildItem -Force <SOLUTION_DIR>`. `--check` is read-only and exits non-zero unless the folder is linked or holds a `.git` folder. Read the state from `Data.State`, not from the exit code alone:

| `Data.State` | Meaning |
|---|---|
| `Linked` | Valid `.git` file; nothing to do |
| `NativeRepository` | `.git` folder; nothing to do, unless `Data.Warnings` reports a `.git-studioweb` beside it (split; see the section below) |
| `NotLinked` | `.git-studioweb` folder, no `.git` entry; link it |
| `Invalid` | `.git` file with other content, or an unsupported entry; ask the user |
| `NoRepository` | No `.git` and no `.git-studioweb`; not a git solution |

## Unexpected Entries

Studio Web never writes these into `.git-studioweb`. Once linked, native git would run hooks or config planted there, so `git-link` refuses to link when any is present:

- `config`, `config.worktree`, `commondir`, `gitdir`, `modules`, `worktrees`, `rebase-merge`, `rebase-apply`, `sequencer`;
- a non-empty `hooks/` or `objects/info/`;
- anything in `info/` other than `exclude`.

List them before any manual link:

```bash
ls -A <SOLUTION_DIR>/.git-studioweb <SOLUTION_DIR>/.git-studioweb/hooks <SOLUTION_DIR>/.git-studioweb/objects/info <SOLUTION_DIR>/.git-studioweb/info
```

If any listed entry exists (by the CLI's `Data` or by this listing): stop, show the user the entries, and ask how to proceed. Never delete them, never write the `.git` file around the refusal.

## Link With the CLI

```bash
uip solution git-link <SOLUTION_DIR>
```

| Flag | Purpose |
|---|---|
| `[solution-path]` | Solution root. Optional; defaults to the current folder. |
| `--check` | Report the state only; write nothing. Non-zero exit unless linked or native. |
| `--force` | Rewrite an invalid `.git` file. Use only after the user agreed. Never replaces a `.git` folder. |

`git-link` writes the `.git` file only when no `.git` entry exists. If the CLI answers `unknown command 'git-link'`, the installed `uip` predates it: use the manual fallback below, or update the CLI.

**Automatic linking.** Current CLIs link the folder on their own: every `uip solution` command that takes a solution path, a `.uipx` file, a solution name, `--solution-folder` or `--solution-file` first links a real `.git-studioweb` folder that has no `.git` entry at all, and prints one notice line on stderr.

- Same safety checks as `git-link`. A refusal or a failed write only warns; the command continues unlinked.
- Skipped for `--dry-run`, `--check` and archives. `UIPATH_AUTO_GIT_LINK_DISABLED=1` turns it off.

After a `uip solution` command, an explicit `git-link` is usually unnecessary. Before running git yourself, still run `uip solution git-link --check <SOLUTION_DIR> --output json` and act on `Data.State`: a skipped or refused auto-link leaves the folder `NotLinked` or `Invalid`.

## Manual Fallback

Run in the solution root, only when there is no `.git` entry at all and the [Unexpected Entries](#unexpected-entries) listing found none. The file must contain exactly `gitdir: .git-studioweb` — ASCII, no trailing space, no BOM, optional line ending.

| OS / shell | Command |
|---|---|
| macOS / Linux (sh, bash, zsh) | `printf 'gitdir: .git-studioweb\n' > .git` |
| Windows cmd | `echo gitdir: .git-studioweb>.git` (no space before `>`) |
| Windows PowerShell (5.1 and 7) | `Set-Content -Path .git -Value 'gitdir: .git-studioweb' -Encoding ascii` |

Broken forms — never use:

| Form | Why it breaks |
|---|---|
| cmd `echo gitdir: .git-studioweb >.git` (space before `>`) | Writes a trailing space; git cannot find `.git-studioweb ` |
| PowerShell `echo gitdir: .git-studioweb > .git`, or `Out-File` with default encoding | PowerShell 5.1 writes UTF-16 with BOM; git cannot parse it |
| cmd form `echo gitdir: .git-studioweb>.git` pasted into PowerShell 5.1 | PowerShell redirection writes UTF-16; the cmd form is for cmd only |
| `git init --separate-git-dir=.git-studioweb` | Writes an absolute path into the `.git` file; Studio Web cannot follow it, and it re-initializes the repository |

## Read Without Linking

A read-only task (review, report, summary) must not write the `.git` file. Point git at the folder explicitly, with `--no-optional-locks` so `status` does not rewrite `.git-studioweb/index`. Use only read commands (`status`, `log`, `diff`, `rev-parse`), and only after the [Unexpected Entries](#unexpected-entries) listing found none: a planted `config` or hook runs under `--git-dir` too.

```bash
git --no-optional-locks --git-dir=<SOLUTION_DIR>/.git-studioweb --work-tree=<SOLUTION_DIR> status --short
```

## Verify

```bash
git rev-parse --git-dir
git status
```

- `git rev-parse --git-dir` prints a path ending in `.git-studioweb` (git prints it absolute).
- `git status` lists the solution's files with the expected branch; `.git-studioweb/` does not appear as untracked.
- `fatal: not a git repository` → the `.git` file is missing or malformed. Read it byte for byte (`od -c .git` on macOS/Linux, `Format-Hex .git` in PowerShell) and compare with the exact content above.

## When a `.git` Folder and `.git-studioweb` Both Exist

How it happens: Studio Web creates `.git-studioweb`; the folder is not linked yet, so `git status` says `not a git repository`; someone runs `git init`, which creates a `.git` folder that takes over. Studio Web's commits seem gone but are still in `.git-studioweb`. `git clone <URL> .` cannot cause it (the folder is not empty). Once linked, `git init` only re-initializes `.git-studioweb`.

The CLI reports this as `NativeRepository` with a `Data.Warnings` entry and changes nothing. Never delete either folder, and never run the merge below unless the user explicitly asks. Show the user the situation and these commands, run from the solution folder (double quotes work in cmd, PowerShell and POSIX shells):

```bash
git fetch ./.git-studioweb "+refs/heads/*:refs/remotes/studioweb/*"
git log studioweb/main
git merge --allow-unrelated-histories studioweb/main
```

1. `fetch` copies Studio Web's branches into `studioweb/*`. Keep the `./`: a bare `.git-studioweb` is read as a remote name.
2. `log` shows Studio Web's history; use the branch name `fetch` printed if it is not `main`.
3. Before `merge`, add the line `.git-studioweb/` to `.git/info/exclude` (else `git add -A` commits the folder into `.git`), then commit or stash local changes: untracked files that Studio Web's branch also holds abort the merge.

## Hazards

1. **Never `git init` or `git clone` in a solution folder that has `.git-studioweb`, linked or not.** Unlinked, it creates a `.git` folder that then wins everywhere, splitting history from what Studio Web sees; linked, it re-initializes or overwrites the repository Studio Web uses. Link instead when unlinked.
2. **Never delete, move, or replace a `.git` folder**, even when `.git-studioweb` also exists.
3. **Never overwrite an existing `.git` file without the user's consent.** Show its content first; rewrite with `uip solution git-link --force` or the manual fallback only after they agree.
4. **Do not write into `.git-studioweb` beyond what git itself does** — no hand-added hooks, no `config` edits, no deleting it to "clean up".
5. **Do not link through a symlinked `.git-studioweb`.** It must be a real folder.

## Packaging and Sync

Treat the `.git-studioweb` folder and the `.git` file like the `.git` folder: they never belong in a package or upload.

- `uip solution upload` and `uip codedapp push` leave out the `.git/` folder on their own. On a CLI that does not also leave out `.git-studioweb/` and the `.git` file, add both to the solution-root `.uipignore`:

  ```gitignore
  .git-studioweb/
  .git
  ```

- `uip solution pack` does not read `.uipignore`. If a packed `.zip` contains `.git-studioweb` entries, report it as a CLI defect instead of working around it.

## VS Code (Optional)

To hide the folder and stop the file watcher from scanning it, add to `.vscode/settings.json` (or user settings):

```json
{
  "files.exclude": { "**/.git-studioweb": true },
  "files.watcherExclude": { "**/.git-studioweb/**": true }
}
```
