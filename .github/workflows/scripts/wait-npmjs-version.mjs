// Blocks until npmjs serves a given @uipath/skills version, or fails after a
// deadline. `npm publish` returns success as soon as the registry ACCEPTS the
// tarball ("Your package is being processed and may take a few minutes to
// become available"); the version becomes installable minutes later, or never
// if the registry holds it for review. A green publish step therefore proves
// only acceptance — this is the step that proves availability.

const PACKUMENT_URL = "https://registry.npmjs.org/@uipath%2Fskills";
const DEADLINE_MS = 15 * 60_000;
const POLL_MS = 15_000;

const version = process.env.VERSION;
if (!version) throw new Error("Missing VERSION environment variable.");
const deadline = Date.now() + DEADLINE_MS;

while (true) {
  if (await isServed(version)) {
    console.log(`npmjs serves @uipath/skills@${version}.`);
    process.exit(0);
  }
  if (Date.now() >= deadline) {
    console.error(`::error::npmjs is not serving @uipath/skills@${version} after ${DEADLINE_MS / 60_000} minutes.`);
    process.exit(1);
  }
  await new Promise((resolve) => setTimeout(resolve, POLL_MS));
}

async function isServed(v) {
  try {
    // Cache-busting query: the registry CDN can serve a stale packument.
    const res = await fetch(`${PACKUMENT_URL}?t=${Date.now()}`, { signal: AbortSignal.timeout(POLL_MS) });
    if (!res.ok) return false;
    const packument = await res.json();
    return Boolean(packument.versions?.[v]);
  } catch (err) {
    console.log(`registry poll failed, retrying: ${err instanceof Error ? err.message : String(err)}`);
    return false;
  }
}
