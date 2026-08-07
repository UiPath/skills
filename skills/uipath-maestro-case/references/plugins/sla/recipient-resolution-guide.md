# SLA Recipient Resolution

Read only for a non-UUID `User` email or `UserGroup` name, immediately before its Phase-1 escalation T-entry.

## Session State and Positive Cache

Keep an in-memory Phase-1 group array, positive cache, and session-wide skip flag. Check skip first: use the unresolved sentinel without cache or directory access, then audit `cli-failed-skipped` with previously observed candidates for that recipient or `[]`.

Key cache by `(kind, trim-and-case-fold SDD input)`, with kind `user` or `group`. A hit reuses the UUID without CLI/prompt, preserves the current SDD display value, and audits its retained candidates, search term, and original rationale—never invent `cache-hit`.

Cache only successful `auto-exact-email`, `auto-exact-name`, or `user-picked-from-N` UUID resolutions. Never cache a decline, unresolved sentinel, failure, skip, or abort; repeat an uncached recipient's normal route unless skip is active.

## Resolve `User`

1. On a cache miss, run `uip admin users list --search "<email>" --output json`.
2. Auto-accept only when the response has one entry and its observed `email` case-insensitively equals the SDD email. Preserve its `id` and the SDD display value; rationale `auto-exact-email`.
3. Otherwise, if the SDD has a display name, run `uip admin users list --search "<display-name>" --output json`; merge responses in order and deduplicate by `id`.
4. Present at most three observed candidates plus `Keep as <UNRESOLVED>`; never fuzzy-pick or first-pick a partial. Label with observed `displayName`; describe as `<email> · id=<uuid-first-8>...`. Selection: `user-picked-from-N`; decline: `user-declined-keep-unresolved`, `selected: null`.
5. With none, offer `Keep as <UNRESOLVED>` and `Abort planning`, never one option. Abort stops before the T-entry and cache write.

## Resolve `UserGroup`

1. On a cache miss without a session group array, run `uip admin groups list --output json`—there is no search flag. Reuse the array for Phase 1 and filter locally.
2. Exactly one entry whose observed `name` or `displayName` case-insensitively equals the SDD name auto-resolves; rationale `auto-exact-name`.
3. Otherwise take case-insensitive substring matches on those fields, deduplicate by `id`, and sort by case-folded `name` (fallback `displayName`), case-folded `displayName`, then `id`. Present at most three plus unresolved. Selection: `user-picked-from-N`; decline: `user-declined-keep-unresolved`, `selected: null`.
4. With none, offer `Keep as <UNRESOLVED>` and `Abort planning`; never one option or fuzzy candidates. Abort stops before the T-entry and cache write.

Write `User: <id> / <original-email>` or `UserGroup: <id> / "<original-group-name>"`; declines use the corresponding `<UNRESOLVED: user-uuid for <email>>` or `<UNRESOLVED: group-uuid for <name>>`.

## Bounded CLI Failure

Any nonzero directory-read exit presents:

```text
Question: Identity resolution failed (<stderr first line>). How should we proceed?
Header: Resolver failed
Options: Retry | Skip resolution for this build | Abort planning
```

- **Retry:** rerun the same read, at most twice after the initial failure. After retry one fails, show all three controls once more; retry-two failure routes once to session skip without another prompt/loop.
- **Skip resolution for this build:** set skip; current and later non-UUID recipients remain unresolved, make no directory call, audit `cli-failed-skipped`, and bypass cache.
- **Abort planning:** halt before the current T-entry; cache nothing.

On skip, send one `SKIPPED` SLA issue through the [logging owner](../logging/impl-json.md) to `tasks/build-issues.md`; the completion warning lists every affected recipient. A successful retry resumes the decision with observed candidates retained.

## Recipient Audit — `tasks/recipients-resolved.json`

Initialize `[]` if absent. Before every append, Read then incrementally Edit; never replace records. Write one exact six-key object per completed non-UUID resolution, cache hit, decline, or skip:

```json
{
  "sddInput": "manager@corp.com",
  "kind": "user",
  "searchTerm": "manager@corp.com",
  "allCandidates": [
    {"id": "a1b2c3d4-0000-0000-0000-000000000000", "email": "manager@corp.com", "displayName": "Anne Manager"}
  ],
  "selected": "a1b2c3d4-0000-0000-0000-000000000000",
  "rationale": "auto-exact-email"
}
```

Set `sddInput` to the exact SDD recipient; `kind` to `user` or `group`; `searchTerm` to the initial email/group term; `allCandidates` to every deduplicated observed candidate considered before truncation; and unresolved `selected` to `null`. Fabricate nothing. Rationale is only `auto-exact-email`, `auto-exact-name`, `user-picked-from-N`, `user-declined-keep-unresolved`, or `cli-failed-skipped`; [planning](planning.md#audit--tasksrecipients-resolvedjson) owns UUID `uuid-pass-through`.
