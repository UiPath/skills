# Skill Flavor Test Matrix

Read this reference completely when adding a flavor or changing the composer, package builder, publishing path, or CI gate.

## Decision Matrix

| Situation | Canonical source | Flavor source | Result |
|---|---|---|---|
| Shared correction | Edit normal prose | No edit | Every flavor inherits it. |
| One host-specific instruction | Add the smallest complete marked block | Add the matching replacement block at the mirrored path | That passage differs only in the target flavor. |
| Reviewed pass-through skill | No marker needed | No override needed | The complete skill is included automatically. |
| Unsafe canonical instruction | Keep the default complete | Add the smallest matching replacement | The custom package remains complete and host-correct. |
| New flavor | No edit unless a real difference exists | Create at least one real sparse override | Generic discovery creates its complete package. |

## Path and Block Closure

For each override, verify all four mappings:

```text
canonical: skills/<skill>/<relative-path>.md
override:  skill-flavors/<flavor>/<skill>/<relative-path>.md
block:     canonical name == override name
inclusion: every canonical skill is present in every flavor
```

Every marker boundary uses the compact
`<!--skill-flavor:<name>:start|end-->` form at column 1, with no internal,
leading, or trailing whitespace. Indented Markdown content stays indented
inside those column-one boundaries.
The override may contain multiple complete blocks separated by whitespace. Canonical block order controls the built file; override order must not affect it.

When splitting an existing broad block into smaller sibling blocks, capture
the built output for every existing flavor first. Update each affected sparse
override, rebuild, and compare complete files; boundary refactoring must not
change existing consumer text.

## Discovery Cases

Test discovery with temporary flavors created in reverse lexical order.

- No custom flavor: build only `default`.
- `alpha-host` and `zeta-host`: build `default`, `alpha-host`, `zeta-host` in stable order.
- Skills without overrides pass through in every custom flavor.
- New `future-host` with one sparse override: automatically create `build/skills/future-host`, `build/packages/future-host`, and `@uipath/skills-future-host`.
- Reject uppercase, underscore, whitespace, path-like, or reserved `default` names.
- Reject flavor-directory symlinks and empty flavor directories.
- Reject a derived npm package name longer than npm's 214-character limit.

## Composition Cases

- Default contains every canonical skill.
- Each flavor contains every canonical skill.
- Two flavors can replace the same canonical block independently.
- A skill without overrides passes through byte-for-byte except marker removal.
- An empty canonical extension block emits nothing in the default and lets a flavor add content without replacing the adjacent shared section.
- New canonical content outside an additive extension block appears in every flavor without an override edit.
- Binary assets copy byte-for-byte.
- Canonical and sparse source files remain unchanged after builds.
- Leading-whitespace, malformed, nested, duplicate, unmatched, or unmarked override boundaries fail before output replacement.

## Package Cases

Inspect staged directories and real `.tgz` archives.

- Default package name is `@uipath/skills`.
- Flavor package name is `@uipath/skills-<flavor>`.
- Every package version exactly matches the root manifest, including preview or dev suffixes.
- Default preserves the current non-skill payload but reads `skills/` from the built default tree.
- Custom packages contain their complete built `skills/`, generated manifest/README, license, and version metadata only.
- The default manifest retains the safe package lifecycle and ships only its small lifecycle driver; custom manifests contain no repository lifecycle scripts or `package.json.repository` field and pin both the default and `@uipath` scoped registry to GitHub Packages in `publishConfig`.
- A missing or extra custom `publishConfig` key, npmjs registry, public access, or inherited `package.json.repository` field is rejected by final tarball selection.
- Tarball `package/skills/**` bytes equal the staged `skills/**` bytes.
- No built tree, stage, or tarball contains marker tokens, sparse override sources, tests, or composer source.
- Root `npm pack` creates exactly one default `@uipath/skills` tarball, regardless of how many custom flavors exist.
- Root `npm publish --dry-run` selects only `@uipath/skills` and restores canonical sources before returning.
- Root `npm pack` and the generated default tarball have identical SHA-512 digests.
- A generated default package can be repacked safely even though composer source is intentionally absent.

## Replacement and Failure Cases

- A second generic build succeeds and replaces only generated directories.
- Removing a flavor removes its prior tree, package, and tarball on the next successful run.
- Removing the final override removes that flavor source directory/package once the directory no longer exists.
- A validation or packing failure leaves the last successful outputs unchanged.
- A symlinked build root or generated output target fails safely.
- Legacy explicit-flavor output commands still refuse non-empty arbitrary destinations.
- Successful root pack and publish lifecycles restore the exact canonical tree and remove transaction state.
- Root preflight pack failures happen before canonical sources are swapped.
- A failed or interrupted root lifecycle is recoverable with `npm run skills:recover`; truly simultaneous preparations leave exactly one active transaction and one failure.
- Unexpected edits made to the temporary packaging tree are preserved for review while canonical sources are restored.

## Workflow Cases

- Generic build validation discovers every flavor without a flavor-specific build loop; release guards may name an explicitly published flavor to enforce its registry boundary.
- CI runs real `npm pack` and uploads every tarball for inspection.
- The default jobs retain root `npm publish` and never iterate over generated flavor tarballs.
- `publish-skill-flavor.yml` accepts only `flavor` and `channel`, validates the lowercase kebab-case flavor, derives its package name, and rejects `default`, missing directories, symlinks, and unsupported channels.
- The generic publisher requires exactly one matching name/flavor/version tarball, scans that exact tarball for markers, and publishes only the selected path.
- The generic publisher has `packages: write` but no npmjs registry, OIDC permission, provenance flag, or access flag; it validates and explicitly supplies the GitHub Packages registry and supports only `dev` and `preview`. Omitting access preserves the existing Internal visibility.
- Custom publication is skipped unless `ENABLE_SKILL_FLAVOR_PUBLISH` equals exactly `true`; the default GitHub Packages and npmjs jobs are never gated by that variable.
- Treat the variable as an operator enablement switch, not a live visibility check. Before enabling it, confirm every explicit flavor caller has an Internal package, does not inherit access from the public source repository, and grants Actions write access. Registry pinning does not establish GitHub visibility.
- Studio Web callers pass `flavor: studioweb` after stamping the same channel and caller `github.run_number` used by the default path.
- Publish concurrency is normalized by effective channel: a `main` push shares a group with manual `dev`, and a `release/v*` push shares a group with manual `preview`.
- A new flavor remains automatically buildable but needs an explicit caller of the generic publisher before it becomes registry-available.
- Local tarball, Studio Web GitHub Packages `dev`/`preview`, default GitHub Packages `dev`, and default npmjs `preview`/`latest` are distinct availability targets; confirm which one the change requires.
