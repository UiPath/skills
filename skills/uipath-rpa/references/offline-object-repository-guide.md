# Offline Object Repository registration and linking

Use for accepted recorded or inferred targets supplied by a migration or
another caller. Read [uia-starter-guide.md § UIA Prerequisites](uia-starter-guide.md#uia-prerequisites),
the installed UIA core guide and its Object Repository, target-configuration
and target-attachment references. This is the recorded-target exception to
capture-first, not permission to capture, launch the application, heal
selectors or run workflows. Validate/build remain required; runtime matching
remains unverified unless separately measured.

## Choose the implementation

Own the outcome, not a particular importer command. Use the current supported
RPA/UIA workflow or importer when it can preserve the caller's requirements
on this project's frozen pins and backend. Discover it through this invoked
skill and installed package documentation; do not guess hidden verbs or read
sibling skill files. Small jobs can use documented commands directly.

When suitable orchestration is absent, generate **one non-Python helper per
run**, outside every deliverable project, taking the project and request as
parameters. Use an available host runtime (for example Node.js or PowerShell
7), with the documented argument transport. Reuse it across parts/projects;
never generate a tool per workflow or per author. Read
[offline-definition-workarounds-guide.md](offline-definition-workarounds-guide.md)
when constructing definitions or using relay commands. It records measured
compatibility cases; reconcile them with the current pinned documentation and
readback rather than carrying obsolete workarounds into a new implementation.

Before writes, review the helper, record its path/hash and check its argument
transport, response grading and mutation logic with saved transcripts or a
small representative offline case. Check an unchanged rerun: stable references
and no duplicate creation. Record the scope of this check; it is not proof of
live matching. Freeze the chosen route/helper and backend/tool/package identity
for the execution. On resume reuse these artifacts. Reconcile any identity or
input change before continuing; do not silently switch implementations.

An invoked importer failing or partially writing is **not** evidence that no
importer exists. Preserve its records and actual state, reconcile store and
workflow readback, then resume safely or report work owed. Never try a generated
replacement on top of an ambiguous partial write. Missing CLI, package, backend,
licence or runtime is NOT RUN with a remedy; generation cannot supply them.
Never install/upgrade dependencies without the consent this skill requires.

## Request and result artifacts

Accept the caller's format when it already specifies these facts; do not make
the caller reverse-engineer a particular tool's private schema. For an artifact
handoff, use this versioned envelope (`schema: uipath-or/1`; a caller may add an attempt identity):

| Request field | Meaning |
|---|---|
| `project`, `project_sha256` | Absolute project directory and hash of the exact `project.json` bytes; verify before writes. |
| `producer`, `key_marker` | Caller namespace and external-key description marker; keys are authoritative within this project. |
| `entities` | App/screen/element rows: `key`, `kind`, `parent`, desired `name`, complete `description`, accepted `definition`, and existing-reference hints. Hints require store verification. |
| `links` | Rows keyed by relative workflow file: `activity_id`, entity `key`, `kind`, exact `property` and current `linked_to`. |
| `files` | Each workflow's byte `sha256` before execution; reject changed inputs before writes. |
| `screenshots`, optional `screenshot_sha256` | Key→prepared image name and name→byte hash in the project's `.screenshots/`; preserve the definition and linked target's image. |
| `registry`, `legacy_registry` | Project-scoped state path and optional old registry to reconcile with the actual store, never copy blindly. |
| `artifact_dir`, `result_path`, `link`, `constraints` | Immutable attempt-scoped evidence directory, current result path, whether links are requested, and immutable caller constraints. |

`definition.attributes` contains accepted target members, not a selector to
re-derive. Optional `template`, `fuzzy_template`, `scope_template` are the CLI's
`{{variable}}` forms of the corresponding accepted members. Use the UIA tools
to normalize/compile these into the project's expression language, preserving
the accepted search steps. A window element may deliberately have an empty
child selector and a nonempty scope. Unsupported configurations are unsatisfied
work before unsafe writes, never approximated selectors.

Return `schema`, absolute `project`, SHA-256 of the **request file bytes** as
`request_sha256`, `owner` (skill identity and version/revision if exposed),
`execution` (`method`, CLI/backend/package identity, selected route, `helper: {path, sha256}` when generated, checks performed), `registry`, and:

- `entities`: one row per requested key, with `status` (`created`, `reused`,
  `replaced`, `unsupported`, `failed`, `not_run`), stable `reference` on success,
  a reason on unsatisfied work, and `records` paths for operations/readback.
  Successful screen/element rows also return `readback: {path, sha256}`: a
  namespace-complete XML inspection copy of the actual CLI-exported target.
  The exported target must carry the row's `Reference`; preserve exported member values (including expression nodes), adding only
  namespace declarations if needed to parse it; retain the raw export too.
  This allows the caller to compare accepted members with stored definitions.
- `links`: one row per requested slot (`file`, `activity_id`, `property`, `key`),
  with `status` (`linked`, `already_linked`, `failed`, `omitted`, `not_run`),
  the verified `reference`, reason where owed, and `records` paths.
- `records`: paths to whole raw command records, including `command`, absolute `project`, `request_sha256`, full `stdout` and
  `stderr`, integer `returncode`, and interpreted `outcome`. Return a
  `record_sha256` map of these paths to their byte hashes. Keep references traceable
  per entity and slot; do not return counts alone. Keep records and exported
  readbacks inside `artifact_dir`, never reuse their paths for another attempt.
  Keep the selected helper immutable too (for example a content-named file);
  archiving result JSON alone does not preserve overwritten evidence.
- `pending_relink`: keys/slots still requiring synchronization; preserve them
  in the registry before linking. `not_run` names an execution blocker, or is
  null. Record partial work even when returning an error.

The caller may independently inspect artifacts and reject completion. Do not
modify its request or baseline files. Keep an earlier result/history before a
rerun; never erase successful work or unresolved failures to make counts green.

## Reconciliation and writes

One registration writer per project; serialize workflow mutations with the
caller's integration lock when supplied. Reuse an already-held lock rather
than reacquiring it, and never wait on another author while holding it. Every
project has a separate registry even when a run's helper is shared.

- Read the store before creating. An unreadable store is not an empty store.
  Validate each key's kind, parent and reference; reject ambiguous duplicate
  keys rather than choosing the first. Adopt existing marker-bearing entries
  (including legacy caller markers) with their references intact. Never merge
  caller keys by selector similarity or delete entries the request omits.
- Fingerprint every field actually pushed: definition, search steps, name,
  description, screenshots and launch/input settings. Keep desired state
  separate from confirmed state. A missing registry requires store verification;
  it does not authorize recreating entries or declaring them synchronized.
- Construct only temporary definition artifacts from accepted inputs; let UIA
  create `.objects`, references, metadata and content hashes. Never fabricate
  repository internals. Use the documented create/replace/link operations.
  Captured `create-app` output is the AppVersion reference required by
  `create-screen`, distinct from its parent App reference. Read and validate
  both identities rather than passing the App reference as an AppVersion.
  Replacement preserves identity. If an existing screen or another field cannot
  be updated safely by the current surface, return unsupported/review work on
  every rerun until resolved; never delete/recreate it or advance its confirmed
  fingerprint. A failed replacement retains the last confirmed fingerprint.
- Persist successful replacements and relink debt **before** linking. Screens
  precede elements. Resolve workflow paths inside the project and preserve
  the exact target property (`TargetApp`, `Target`, `FilterTarget`,
  `VerifyOptions.Target`, etc.). Bound batches for the host's payload limits;
  count and read back each requested slot, including partial batches.
- Snapshot activity identities and annotations before mutation and verify them
  afterward. Preserve unrelated workflow behavior. A success line is insufficient:
  inspect actual references and definitions, screenshots, selector variables
  and search steps. Never clear relink debt until the corresponding slots were
  verified. Stop on lineage damage and retain before/after files and records.
- Validate affected workflows and build the project per this skill. A clean
  validation is not evidence that every `Reference` resolves or that selectors
  match the application. Keep those claims separate.

## Host and compatibility limits

Full raw output matters: UIA relay commands on measured versions reject
`--output` and can exit zero with failure text. Use JSON for commands that
support it; grade relay output per its documented surface and retain the whole
response. Confirm actual store and file changes after apparent success.

Preserve names/descriptions/selector text byte for byte through host transport;
never sanitize quotes, percent signs or punctuation to get a command through.
Use the measured Windows transport in the workarounds guide only where its
runtime is available. If no exact transport is available, report the blocker.

A long-lived host can serve stale workflow content. Validate the final files
before linking and verify readback afterward. Diagnose only the confirmed
project-owned host; never kill broad process groups or reset unrelated projects.
Carry per-slot outcomes across truncated payloads, host failures and retries.
