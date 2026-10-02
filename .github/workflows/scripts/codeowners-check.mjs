// Is the actor an owner of skills/<skill>/? Used by optimize-skill.yml so only a skill's
// CODEOWNERS can queue its optimization.
//
// usage: node codeowners-check.mjs <CODEOWNERS> <skill> <actor>
// env:   GH_TOKEN (optional) — used to check membership of team owners (@org/team)
//        ALSO_ALLOWED (optional) — comma/space-separated handles allowed for every skill
//        (the optimizer's maintainers; the repo variable SKILL_OPTIMIZER_MAINTAINERS)
// exit:  0 owner · 1 not an owner (or unverifiable) · 2 bad input
//
// CODEOWNERS semantics (gitignore-style patterns, the LAST matching rule wins) are applied to
// skills/<skill>/SKILL.md. A team owner counts when the actor is an active member; the
// workflow's token may not be allowed to read team membership, in which case the check fails
// closed and says which owners to ask.
import { readFileSync } from "node:fs";

const [file, skill, actor] = process.argv.slice(2);
if (!file || !/^[a-z0-9][a-z0-9-]*$/.test(skill ?? "") || !actor) {
  console.error("usage: codeowners-check.mjs <CODEOWNERS> <skill> <actor>");
  process.exit(2);
}

export function toRegex(pattern) {
  let p = pattern;
  const dirOnly = p.endsWith("/");
  if (dirOnly) p = p.slice(0, -1);
  const anchored = p.startsWith("/") || p.includes("/");
  p = p.replace(/^\//, "");
  const body = p
    .split(/(\*\*|\*|\?)/)
    .map((t) => (t === "**" ? ".*" : t === "*" ? "[^/]*" : t === "?" ? "[^/]" : t.replace(/[.+^${}()|[\]\\]/g, "\\$&")))
    .join("");
  // a pattern matches the path itself or anything under it (a directory rule)
  const tail = dirOnly ? "/.*" : "(/.*)?";
  return new RegExp(`^${anchored ? "" : "(.*/)?"}${body}${tail}$`);
}

const path = `skills/${skill}/SKILL.md`;
let owners = null;
for (const raw of readFileSync(file, "utf8").split("\n")) {
  const line = raw.replace(/\s+#.*$/, "").trim();
  if (!line || line.startsWith("#")) continue;
  const [pattern, ...who] = line.split(/\s+/);
  if (pattern === "*" || toRegex(pattern).test(path)) owners = who;   // last match wins
}
if (!owners || owners.length === 0) {
  console.log(`No CODEOWNERS rule covers ${path}.`);
  process.exit(1);
}

const lc = (s) => s.toLowerCase();
const maintainers = (process.env.ALSO_ALLOWED ?? "").split(/[\s,]+/).filter(Boolean).map((h) => h.replace(/^@/, ""));
if (maintainers.some((m) => lc(m) === lc(actor))) {
  console.log(`@${actor} is an optimizer maintainer (SKILL_OPTIMIZER_MAINTAINERS).`);
  process.exit(0);
}
const users = owners.filter((o) => o.startsWith("@") && !o.includes("/")).map((o) => o.slice(1));
const teams = owners.filter((o) => o.startsWith("@") && o.includes("/")).map((o) => o.slice(1));
if (users.some((u) => lc(u) === lc(actor))) {
  console.log(`@${actor} is a CODEOWNER of skills/${skill}/.`);
  process.exit(0);
}

const token = process.env.GH_TOKEN;
let unverifiable = [];
for (const t of teams) {
  const [org, slug] = t.split("/");
  const res = await fetch(`https://api.github.com/orgs/${org}/teams/${slug}/memberships/${actor}`, {
    headers: { Accept: "application/vnd.github+json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (res.status === 200 && (await res.json()).state === "active") {
    console.log(`@${actor} is a member of @${t}, a CODEOWNER of skills/${skill}/.`);
    process.exit(0);
  }
  if (res.status !== 404) unverifiable.push(`@${t}`);   // 403/401: the token cannot read the team
}

console.log(`@${actor} is not a CODEOWNER of skills/${skill}/. Owners: ${owners.join(" ")}`);
if (unverifiable.length) {
  console.log(`(Could not read membership of ${unverifiable.join(", ")}; if you are in one, ask a listed owner to run it.)`);
}
process.exit(1);
