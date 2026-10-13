// Is the actor an owner of skills/<skill>/? Used by optimize-skill.yml so only a skill's
// CODEOWNERS can queue its optimization — this script is that workflow's only authorization
// check (tests: tests/scripts/codeowners-check.test.mjs).
//
// usage: node codeowners-check.mjs <CODEOWNERS> <skill> <actor>
// env:   GH_TOKEN (optional) — used to check membership of team owners (@org/team)
//        ALSO_ALLOWED (optional) — handles allowed for every skill, space- or comma-separated,
//        @ optional (the optimizer's maintainers; OPTIMIZER_MAINTAINERS in optimize-skill.yml)
// exit:  0 owner · 1 not an owner (or unverifiable) · 2 bad input
//
// CODEOWNERS semantics (the LAST matching rule wins) are applied to skills/<skill>/SKILL.md.
// A team owner counts only when the actor is an ACTIVE member, which needs a token that can
// read org membership: optimize-skill.yml passes one from the skill-trimming-optimizer GitHub
// App, narrowed to Members: read, when its key is configured. github.token cannot read teams — GitHub answers 404 for "not a
// member" and for "may not look" alike — so without the App team owners fail closed, and the
// refusal says whom to ask (a listed user owner or an optimizer maintainer).
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

/** The skill-name format; optimize-skill.yml's "Validate the run form" step uses the same one. */
export const SKILL_RE = /^[a-z0-9][a-z0-9-]*$/;

const escape = (s) => s.replace(/[.+^${}()|[\]\\]/g, "\\$&");

/**
 * A CODEOWNERS pattern as a RegExp over repo-relative paths, following GitHub's documented
 * matching: a literal path also covers everything under it; `dir/` covers only what is under
 * it; a glob in the LAST segment matches that segment alone (`docs/*` is docs' direct
 * children, not docs/sub/file); `/**\/` spans zero or more directories; a pattern without a
 * slash before its end matches at any depth. The global `*` is handled by the caller.
 */
export function toRegex(pattern) {
  let p = pattern;
  const dirOnly = p.endsWith("/");
  if (dirOnly) p = p.slice(0, -1);
  const anchored = p.startsWith("/") || p.includes("/");
  p = p.replace(/^\//, "");
  const last = p.slice(p.lastIndexOf("/") + 1);
  const body = p
    .split(/(\/\*\*\/|^\*\*\/|\/\*\*$|\*\*|\*|\?)/)
    .map((t) => {
      if (t === "/**/") return "(?:/.*)?/";
      if (t === "**/") return "(?:.*/)?";
      if (t === "/**") return "/.*";
      if (t === "**") return ".*";
      if (t === "*") return "[^/]*";
      if (t === "?") return "[^/]";
      return escape(t);
    })
    .join("");
  const tail = dirOnly ? "/.*" : /[*?]/.test(last) && last !== "**" ? "" : "(?:/.*)?";
  return new RegExp(`^${anchored ? "" : "(?:.*/)?"}${body}${tail}$`);
}

/** Owners of `path`: the last matching rule wins. `matched` is false when no rule covers it. */
export function resolveOwners(codeownersText, path) {
  let matched = false;
  let owners = [];
  for (const raw of codeownersText.split("\n")) {
    const line = raw.replace(/\s+#.*$/, "").trim();
    if (!line || line.startsWith("#")) continue;
    const [pattern, ...who] = line.split(/\s+/);
    if (pattern === "*" || toRegex(pattern).test(path)) {
      matched = true;
      owners = who;
    }
  }
  return { matched, owners };
}

/** ALSO_ALLOWED / OPTIMIZER_MAINTAINERS: space- or comma-separated handles, @ optional. */
export function parseMaintainers(value) {
  return (value ?? "").split(/[\s,]+/).filter(Boolean).map((h) => h.replace(/^@/, ""));
}

/** GitHub's team-membership endpoint. Slugs are lowercase; CODEOWNERS may write them mixed-case. */
export async function fetchMembership(org, team, actor, token) {
  const url = `https://api.github.com/orgs/${encodeURIComponent(org)}/teams/${encodeURIComponent(team.toLowerCase())}/memberships/${encodeURIComponent(actor)}`;
  const res = await fetch(url, {
    headers: { Accept: "application/vnd.github+json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  let state = null;
  if (res.status === 200) {
    try {
      state = (await res.json()).state ?? null;
    } catch {
      state = null;
    }
  }
  return { status: res.status, state };
}

/**
 * Decide whether `actor` may run the optimizer on `skill`. Pure apart from `membership`
 * (org, team, actor) -> {status, state}, which tests replace. Returns {code, lines}: lines are
 * {level: "notice" | "error", text}; every refusal is an error, so the run page shows why.
 */
export async function checkActor({ skill, owners, matched, actor, maintainers, membership }) {
  const lc = (s) => s.toLowerCase();
  const dir = `skills/${skill}/`;
  if (maintainers.some((m) => lc(m) === lc(actor))) {
    return { code: 0, lines: [{ level: "notice", text: `@${actor} is an optimizer maintainer (OPTIMIZER_MAINTAINERS).` }] };
  }
  if (!matched) return { code: 1, lines: [{ level: "error", text: `No CODEOWNERS rule covers ${dir}SKILL.md.` }] };
  if (owners.length === 0) {
    return { code: 1, lines: [{ level: "error", text: `${dir} is explicitly unowned in CODEOWNERS (its last matching rule lists no owners).` }] };
  }
  const users = owners.filter((o) => o.startsWith("@") && !o.includes("/")).map((o) => o.slice(1));
  const teams = owners.filter((o) => o.startsWith("@") && o.includes("/")).map((o) => o.slice(1));
  if (users.some((u) => lc(u) === lc(actor))) {
    return { code: 0, lines: [{ level: "notice", text: `@${actor} is a CODEOWNER of ${dir}.` }] };
  }
  const unverifiable = [];
  for (const t of teams) {
    const [org, slug] = t.split("/");
    try {
      const { status, state } = await membership(org, slug, actor);
      if (status === 200 && state === "active") {
        return { code: 0, lines: [{ level: "notice", text: `@${actor} is a member of @${t}, a CODEOWNER of ${dir}.` }] };
      }
      // A token without org read access gets 404 (not 403) here, the same answer as "not a
      // member", so anything short of an active membership leaves the team unverified.
      unverifiable.push(status === 404 ? `@${t}` : `@${t} (HTTP ${status}${state ? `, ${state}` : ""})`);
    } catch (e) {
      unverifiable.push(`@${t} (network error: ${e?.message ?? e})`);
    }
  }
  const lines = [{ level: "error", text: `@${actor} is not a CODEOWNER of ${dir}. Owners: ${owners.join(" ")}` }];
  if (unverifiable.length) {
    const who = [...users.map((u) => `@${u}`), ...maintainers.map((m) => `@${m}`)].join(" ") || "an optimizer maintainer";
    lines.push({
      level: "error",
      text: `Not an active member of ${unverifiable.join(", ")} as far as GitHub tells this token (GitHub hides membership from tokens that cannot read teams); if you are in one, ask ${who} to run it.`,
    });
  }
  return { code: 1, lines };
}

async function main(argv) {
  const [file, skill, actor] = argv;
  if (!file || !SKILL_RE.test(skill ?? "") || !actor) {
    console.log("::error::usage: codeowners-check.mjs <CODEOWNERS> <skill> <actor> (skill: lowercase letters, digits, hyphens)");
    return 2;
  }
  let text;
  try {
    text = readFileSync(file, "utf8");
  } catch (e) {
    console.log(`::error::cannot read ${file}: ${e.message}`);
    return 2;
  }
  const { matched, owners } = resolveOwners(text, `skills/${skill}/SKILL.md`);
  const token = process.env.GH_TOKEN;
  const { code, lines } = await checkActor({
    skill,
    owners,
    matched,
    actor,
    maintainers: parseMaintainers(process.env.ALSO_ALLOWED),
    membership: (org, team, who) => fetchMembership(org, team, who, token),
  });
  for (const { level, text: t } of lines) console.log(level === "error" ? `::error::${t}` : t);
  return code;
}

// run as a CLI only (process.argv[1] is unset under `node -e` / a REPL import)
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(await main(process.argv.slice(2)));
}
