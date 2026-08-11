---
name: manage-skill-flavors
description: "Maintain build-time skill flavors in the UiPath skills repository. Use when adding or editing skill-flavor marker blocks, sparse flavor overrides, generic flavor discovery, marker-free default or custom npm packages, package inspection, flavor CI, or composer/package tests. Preserve SKILL.md as the complete default, keep overrides exceptional, and validate finished trees and tarballs."
---

# Manage Skill Flavors

Maintain one complete canonical skill while building reviewed host-specific exceptions before packaging. Consumers receive finished files and never interpret markers.

## Start With the Complete Context

1. Confirm the repository root contains `skills/`, `skill-flavors/`, and `scripts/compose-skill-flavor.mjs`.
2. Read the complete canonical file being changed.
3. Read the matching relative file under every existing `skill-flavors/<flavor>/` directory, when present. No override means that flavor intentionally inherits the canonical file.
4. Read [references/flavor-test-matrix.md](references/flavor-test-matrix.md) completely when adding a flavor or changing discovery, composition, packaging, publishing, or CI.

## Classify the Change

| Change | Correct source edit |
|---|---|
| Behavior is valid in every host | Edit only the canonical file. |
| A host capability changes one instruction | Mark the smallest complete canonical passage and add one sparse replacement block. |
| An existing skill is safe unchanged for a flavor | Make no flavor edit; it is included automatically. |
| A new canonical skill is added | Review it against every flavor; add sparse overrides only where canonical guidance is unsafe. |
| A new flavor is added | Add its first real sparse override under `skill-flavors/<flavor>/`; generic build and CI must discover it without another registry edit. |

Do not create an exception merely to reword shared guidance.

## Author the Smallest Exception

Keep the canonical `SKILL.md` or reference complete. Put standalone boundaries around only the passage that differs:

```markdown
<!--skill-flavor:project-creation:start-->
Create the project with the default local workflow.
<!--skill-flavor:project-creation:end-->
```

Mirror the canonical path below the flavor root and write only complete replacement blocks plus whitespace:

```text
skills/uipath-example/references/setup.md
skill-flavors/studioweb/uipath-example/references/setup.md
```

```markdown
<!--skill-flavor:project-creation:start-->
Create the project with the host project-creation tool.
<!--skill-flavor:project-creation:end-->
```

Marker names must be lowercase kebab-case, unique within a file, unnested, and identical in canonical and override files. An override cannot add an unmarked introduction, heading, or note.

Use the compact marker form with no whitespace inside the HTML comment, and
start every boundary at column 1 with no leading or trailing spaces or tabs.
Keep the Markdown indentation on the content inside the block instead. For
example, wrap a nested list item like this:

```markdown
<!--skill-flavor:connector-registration:start-->
    - Nested host-specific instruction.
<!--skill-flavor:connector-registration:end-->
```

If a new flavor needs a smaller exception than an existing multi-paragraph
block, split that block into adjacent sibling blocks. Update every existing
override that used the old block, and compare its complete built file before
and after the refactor—the existing flavor's consumer text must remain
unchanged. Never nest a narrower block inside the old one.

## Prefer Additive Extension Points

Do not replace a complete shared table, list, or navigation section merely to
add host guidance. A replacement freezes that whole passage for the flavor, so
later canonical additions inside it no longer propagate. Keep the shared
content unmarked and put an empty extension block next to it:

```markdown
| Shared reference | Shared purpose |
|---|---|
| references/common.md | Used by every host |
<!--skill-flavor:reference-navigation-extra:start-->

<!--skill-flavor:reference-navigation-extra:end-->
```

Fill only that extension in the sparse override. The default emits nothing at
the extension point; the flavor receives the complete shared section plus its
addition. If one existing row genuinely differs, mark only that row instead
of copying the whole table. Whenever a canonical marked passage changes, read
every override for that block because those flavors do not inherit the edit.

## Treat Missing Overrides as Intentional Inheritance

Every custom flavor package contains every canonical skill. Sparse files only
replace passages that differ for that host.

- Add no flavor file when canonical guidance is correct for the host.
- Add the smallest replacement block when canonical guidance is wrong for the host.
- Review every new or materially changed canonical skill against every existing flavor because inclusion is automatic. Update or add the smallest necessary sparse override wherever the canonical guidance is not correct for that flavor.
- Do not create an empty flavor. If a host has no exceptions, it should consume the default package.

## Preserve Generic Discovery and Package Naming

Every direct lowercase kebab-case directory under `skill-flavors/` is a flavor. Never hardcode `studioweb` in the composer, npm build scripts, generic validation loop, or reusable flavor publisher. Publication is intentionally different: each released flavor must opt in through an explicit reviewed caller so its registry policy cannot expand implicitly.

Package names derive mechanically from the root package:

| Variant | Package |
|---|---|
| `default` | `@uipath/skills` |
| `studioweb` | `@uipath/skills-studioweb` |
| `<flavor>` | `@uipath/skills-<flavor>` |

Do not add an allowlist, `skill.build.json`, a flavor registry, or per-flavor package metadata. The directory name and sparse overrides are the source contract.

## Validate the Consumer Artifacts

Run the repository commands in order:

```bash
npm run skills:validate
npm run skills:build
npm run skills:pack
npm run skills:test
git diff --check
```

`skills:build` must produce complete marker-free trees under `build/skills/`. `skills:pack` must rebuild those trees, stage packages under `build/packages/`, run real `npm pack`, and verify tarballs under `build/npm/`. Flavor publishing jobs must select one verified `.tgz` by manifest identity and publish only that exact path; they must never publish a wildcard containing the default or another flavor.

Normal `npm pack` and `npm publish` at the repository root remain backward
compatible default-package commands. Their `prepack` lifecycle transactionally
activates a marker-free default `skills/` tree, and `postpack` restores the
exact canonical source tree before the command finishes. They produce or
publish only `@uipath/skills`; they do not replace `npm run skills:pack`, which
builds every discovered flavor. If npm fails or is interrupted between those
lifecycle steps and `build/.root-pack-transaction` remains, first confirm the
original npm process has ended, then run `npm run skills:recover` before
retrying. Recovery restores canonical sources; if it finds unexpected overlay
edits, it preserves them under `build/.root-pack-recovery-*` and exits nonzero
so they cannot be missed. Never use `--ignore-scripts` for root source
packaging because it intentionally bypasses this composition lifecycle.

Inspect the final package contract, not only sparse sources:

- The default contains every canonical skill and retains canonical block bodies without marker boundaries.
- Each custom package contains every canonical skill and its flavor replacements.
- Every staged manifest uses the root version and the derived package name.
- Custom manifests contain no repository lifecycle scripts or `package.json.repository` field. They pin both `publishConfig.registry` and `publishConfig["@uipath:registry"]` to `https://npm.pkg.github.com/`; the scoped pin prevents an ambient `@uipath` npmjs configuration from winning. The publisher still validates the effective scoped registry and supplies the reviewed `dev` or `preview` tag. Do not set an access value during normal publishing because the existing Internal visibility must remain unchanged.
- No built tree, staged package, or tarball contains `skill-flavor:` comments, `skill-flavors/`, repository tests, or composer source.
- Binary and template assets remain byte-identical.

Clarify what "available" means before release work: a successful
`skills:pack` makes a local tarball available; registry availability requires
an explicit publisher. When publication is in scope, read `docs/RELEASE.md`
completely and confirm the target registry and channel. Keep `publish.yml`'s
established default jobs root-only. Give each published flavor an isolated,
reviewed caller that passes its flavor and channel to
`publish-skill-flavor.yml`. The reusable workflow validates the flavor,
derives its package name, and publishes one selected tarball to GitHub Packages
only. Studio Web callers pass `flavor: studioweb`; never add Studio Web to the
default npmjs path. A future flavor is automatically buildable, not
automatically publishable, until an explicit caller is added. The reusable
publisher also requires the repository variable
`ENABLE_SKILL_FLAVOR_PUBLISH=true`; leave it absent or false until an operator
has confirmed that every explicitly published custom package has been
bootstrapped as Internal, does not inherit access from the public repository,
and grants `UiPath/skills` Actions write access. Registry routing and GitHub
package visibility are separate controls, and this variable is an enablement
switch rather than a live visibility check. Follow the one-time procedure in
`docs/RELEASE.md`, and disable the global gate again before adding a caller for
another not-yet-bootstrapped flavor.

## Critical Rules

1. **Keep canonical files complete.** Default/local consumers must understand `SKILL.md` without a build manifest.
2. **Build files before packages.** Packages consume complete `build/skills/<variant>` trees, never canonical and sparse sources directly.
3. **Make additions automatic.** A valid new flavor directory must receive a tree and package without code, npm-script, or workflow edits.
4. **Preserve root command compatibility.** Normal root `npm pack` and `npm publish` must compose only the marker-free default package and restore canonical sources; `npm run skills:pack` remains the all-flavor command.
5. **Never edit generated output.** Change canonical files, sparse overrides, or the composer; do not modify or commit `build/`.
6. **Fail before replacement.** Validate every flavor and inspect every tarball before replacing the last successful generated artifacts.
7. **Recover without data loss.** Keep root packaging transactional, reject overlapping transactions, and preserve unexpected overlay edits before restoring canonical sources.
8. **Isolate publication.** Keep default root publishing separate from flavor publishing; registry-lock and select one exact flavor tarball, and keep operator enablement off until every called flavor package is confirmed Internal.
9. **Keep shared evolution automatic.** Prefer empty additive extension points for host-only additions; never copy a shared table or list into a broad replacement that can silently hide later canonical changes.

## What Not to Do

- Do not copy an entire skill into a flavor to change a few paragraphs.
- Do not introduce JSON tags, fragment manifests, or runtime composition.
- Do not add one npm build command or generic validation-CI branch per flavor; an explicitly published flavor still needs a reviewed caller of the correct publisher.
- Do not ship default plugin hooks or manifests in a minimal host package.
- Do not validate only `studioweb`; enumerate every discovered flavor.
- Do not trust a source-tree scan as proof of package safety; inspect the actual tarballs.
- Do not remove or bypass the root `prepack`/`postpack` lifecycle; source markers must never reach the default npm package.
- Do not make the default publisher iterate over `build/npm/*.tgz`, and do not publish a flavor through an unreviewed registry wildcard.
- Do not configure npmjs credentials, OIDC trusted publishing, provenance, or public access for a custom flavor package.
