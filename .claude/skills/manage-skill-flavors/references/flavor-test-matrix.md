# Skill Flavor Test Matrix

Read this reference completely when adding a flavor or changing the composer, package builder, publishing path, or CI gate.

## Decision Matrix

| Situation | Canonical source | Flavor source | Allowlist |
|---|---|---|---|
| Shared correction | Edit normal prose | No edit | No edit unless review status changed |
| One host-specific instruction | Add the smallest complete marked block | Add the matching replacement block at the mirrored path | Skill must be listed |
| Reviewed pass-through skill | No marker needed | No override needed | Add the skill |
| Unsafe or unreviewed skill | Keep default complete | No override required | Keep the skill out |
| New flavor | No edit unless a real difference exists | Create sparse overrides only where needed | Create the required file |

## Path and Block Closure

For each override, verify all four mappings:

```text
canonical: skills/<skill>/<relative-path>.md
override:  skill-flavors/<flavor>/<skill>/<relative-path>.md
block:     canonical name == override name
review:    <skill> appears in skill-flavors/<flavor>/skills.allowlist
```

The override may contain multiple complete blocks separated by whitespace. Canonical block order controls the built file; override order must not affect it.

When splitting an existing broad block into smaller sibling blocks, capture
the built output for every existing flavor first. Update each affected sparse
override, rebuild, and compare complete files; boundary refactoring must not
change existing consumer text.

## Discovery Cases

Test discovery with temporary flavors created in reverse lexical order.

- No custom flavor: build only `default`.
- `alpha-host` and `zeta-host`: build `default`, `alpha-host`, `zeta-host` in stable order.
- Allowlist with no override: build a complete pass-through flavor.
- New `future-host`: automatically create `build/skills/future-host`, `build/packages/future-host`, and `@uipath/skills-future-host`.
- Reject uppercase, underscore, whitespace, path-like, or reserved `default` names.
- Reject flavor-directory symlinks and missing or empty allowlists.
- Reject a derived npm package name longer than npm's 214-character limit.

## Composition Cases

- Default contains every canonical skill.
- Each flavor contains exactly its allowlisted skills.
- Two flavors can replace the same canonical block independently.
- An allowlisted skill without overrides passes through byte-for-byte except marker removal.
- Non-allowlisted skills never appear in that flavor.
- Binary assets copy byte-for-byte.
- Canonical and sparse source files remain unchanged after builds.
- Malformed, nested, duplicate, unmatched, or unmarked override content fails before output replacement.

## Package Cases

Inspect staged directories and real `.tgz` archives.

- Default package name is `@uipath/skills`.
- Flavor package name is `@uipath/skills-<flavor>`.
- Every package version exactly matches the root manifest, including preview or dev suffixes.
- Default preserves the current non-skill payload but reads `skills/` from the built default tree.
- Custom packages contain their complete built `skills/`, generated manifest/README, license, and version metadata only.
- Generated manifests contain no repository lifecycle scripts.
- Tarball `package/skills/**` bytes equal the staged `skills/**` bytes.
- No built tree, stage, or tarball contains marker tokens, sparse override sources, tests, or composer scripts.

## Replacement and Failure Cases

- A second generic build succeeds and replaces only generated directories.
- Removing a flavor removes its prior tree, package, and tarball on the next successful run.
- Removing an allowlist entry removes that skill from the next custom package.
- A validation or packing failure leaves the last successful outputs unchanged.
- A symlinked build root or generated output target fails safely.
- Legacy explicit-flavor output commands still refuse non-empty arbitrary destinations.

## Workflow Cases

- Validation CI contains no flavor-specific path or loop.
- CI runs real `npm pack` and uploads every tarball for inspection.
- Release packaging happens after version stamping.
- Publishing uses the verified `build/npm/*.tgz` artifacts, never the repository root or a release-time repack.
- Exact package versions already present in the target registry are skipped only when registry and local tarball integrity match; a collision must fail.
- Custom flavors publish before default; an unregistered npmjs flavor is warned and skipped until its trusted-publisher bootstrap is complete.
- Only a confirmed package-not-found response may trigger that bootstrap skip; registry, network, or authentication failures must fail the release.
- Each new npmjs flavor package has its trusted publisher configured before first publication.
- Local tarball, GitHub Packages `dev`, npmjs `preview`, and npmjs `latest` are distinct availability targets; confirm which one the change requires.
