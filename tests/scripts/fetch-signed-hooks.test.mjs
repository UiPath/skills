import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { artifactFileUrl, overlaySignedScripts } from "../../scripts/fetch-signed-hooks.mjs";

const COMMIT = "a".repeat(40);
const OTHER_COMMIT = "b".repeat(40);
const SIGNATURE = [
  "# SIG # Begin signature block",
  `# ${"Q".repeat(600)}`,
  "# SIG # End signature block",
].join("\n");

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

/** A hooks/ directory holding `names`, plus signed replacements for them. */
function scenario(names, { signedNames = names } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "fetch-signed-hooks-"));
  const hooksDir = path.join(root, "hooks");
  fs.mkdirSync(hooksDir);
  for (const name of names) {
    fs.writeFileSync(path.join(hooksDir, name), `Write-Host 'unsigned ${name}'\n`);
  }

  const artifactFiles = new Map();
  const scripts = [];
  for (const name of signedNames) {
    const content = Buffer.from(`Write-Host 'signed ${name}'\n${SIGNATURE}\n`, "utf8");
    artifactFiles.set(name, content);
    scripts.push({
      name,
      sha256: sha256(content),
      thumbprint: "0".repeat(40),
      subject: "CN=UiPath",
    });
  }

  return { hooksDir, artifactFiles, manifest: { commit: COMMIT, scripts } };
}

test("overlays every signed script over the unsigned checkout", () => {
  const { hooksDir, artifactFiles, manifest } = scenario(["a.ps1", "b.ps1"]);

  overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: COMMIT });

  for (const name of ["a.ps1", "b.ps1"]) {
    const written = fs.readFileSync(path.join(hooksDir, name), "utf8");
    assert.match(written, /signed/, `${name} should have been replaced`);
    assert.match(written, /# SIG # Begin signature block/);
  }
});

test("rejects a gate run that signed a different commit", () => {
  const { hooksDir, artifactFiles, manifest } = scenario(["a.ps1"]);

  assert.throws(
    () => overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: OTHER_COMMIT }),
    /gate signed commit a{40}, but this run is publishing b{40}/,
  );
});

test("rejects a script the gate did not sign", () => {
  // The tree ships two hooks; the gate signed only one. Publishing here would
  // ship one signed and one unsigned script.
  const { hooksDir, artifactFiles, manifest } = scenario(["a.ps1", "b.ps1"], {
    signedNames: ["a.ps1"],
  });

  assert.throws(
    () => overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: COMMIT }),
    /not signed: b\.ps1/,
  );
});

test("rejects a signed script that is not in this tree", () => {
  const { hooksDir, artifactFiles, manifest } = scenario(["a.ps1"], {
    signedNames: ["a.ps1", "gone.ps1"],
  });

  assert.throws(
    () => overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: COMMIT }),
    /signed but not in this tree: gone\.ps1/,
  );
});

test("rejects content that does not match the manifest digest", () => {
  const { hooksDir, artifactFiles, manifest } = scenario(["a.ps1"]);
  artifactFiles.set("a.ps1", Buffer.from(`tampered\n${SIGNATURE}\n`, "utf8"));

  assert.throws(
    () => overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: COMMIT }),
    /a\.ps1 was altered in transit/,
  );
});

test("rejects a downloaded script with no signature block", () => {
  const { hooksDir, artifactFiles, manifest } = scenario(["a.ps1"]);
  const unsigned = Buffer.from("Write-Host 'nope'\n", "utf8");
  artifactFiles.set("a.ps1", unsigned);
  manifest.scripts[0].sha256 = sha256(unsigned);

  assert.throws(
    () => overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: COMMIT }),
    /a\.ps1 carries no signature block/,
  );
});

test("writes bytes verbatim, without newline translation", () => {
  // An Authenticode signature covers exact bytes: a rewritten line ending
  // invalidates it. This is also why .gitattributes marks hooks/* as -text.
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "fetch-signed-hooks-crlf-"));
  const hooksDir = path.join(root, "hooks");
  fs.mkdirSync(hooksDir);
  fs.writeFileSync(path.join(hooksDir, "a.ps1"), "unsigned\n");

  const content = Buffer.from(`Write-Host 'x'\r\n${SIGNATURE}\r\n`, "utf8");
  const manifest = {
    commit: COMMIT,
    scripts: [{ name: "a.ps1", sha256: sha256(content), thumbprint: "0", subject: "CN=UiPath" }],
  };

  overlaySignedScripts({
    manifest,
    artifactFiles: new Map([["a.ps1", content]]),
    hooksDir,
    expectedCommit: COMMIT,
  });

  assert.deepEqual(fs.readFileSync(path.join(hooksDir, "a.ps1")), content);
});

// The artifact downloadUrl arrives with `format=zip` already set. Two `format`
// parameters means the service honours the first, returns a zip and ignores
// `subPath`, so the manifest parse fails on the zip header.
test("artifact file URL replaces the existing format instead of appending", () => {
  const url = artifactFileUrl(
    "https://artprod.example.com/_apis/artifact/abc123/content?format=zip",
    "manifest.json",
  );
  const params = new URL(url).searchParams;

  assert.deepEqual(params.getAll("format"), ["file"]);
  assert.equal(params.get("subPath"), "/manifest.json");
});

test("artifact file URL preserves unrelated query parameters", () => {
  const url = artifactFileUrl(
    "https://artprod.example.com/content?format=zip&api-version=7.1",
    "send-telemetry.ps1",
  );
  const params = new URL(url).searchParams;

  assert.equal(params.get("api-version"), "7.1");
  assert.deepEqual(params.getAll("format"), ["file"]);
  assert.equal(params.get("subPath"), "/send-telemetry.ps1");
});
