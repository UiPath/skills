#!/usr/bin/env node
/**
 * Run the Azure DevOps release gate and bring its signed hooks back.
 *
 * Publishing stays in GitHub Actions because npm mints provenance
 * attestations only for GitHub Actions and GitLab CI identities. Signing has to
 * happen in Azure DevOps because UiPath's code-signing certificate is reachable
 * only through an ARM service connection's service principal and is never
 * exported. This script is the seam: it starts `.pipelines/release-gate.yml`,
 * waits for it, and overlays the signed `hooks/*.ps1` onto the working tree so
 * the publish job can pack and sign the tarball with `--provenance`.
 *
 * Authentication is OIDC end to end -- no stored credential. GitHub issues an
 * id-token for this workflow run, Entra exchanges it for an Azure DevOps access
 * token through a federated credential scoped to this repository.
 *
 * Usage:
 *   node scripts/fetch-signed-hooks.mjs
 *
 * Environment:
 *   AZURE_TENANT_ID     Entra tenant of the federated application (required)
 *   AZURE_CLIENT_ID     Application (client) ID of that application (required)
 *   ADO_ORGANIZATION    Azure DevOps organization           (default: uipath)
 *   ADO_PROJECT         Azure DevOps project                (default: skills)
 *   ADO_PIPELINE_ID     Numeric definition ID of the gate pipeline (required)
 *   GATE_CHANNEL        `preview` or `latest`                       (required)
 *   GATE_REF            Ref to run the gate against, e.g. refs/heads/main
 *   GATE_COMMIT         Commit SHA being published; asserted end to end
 *   GATE_TIMEOUT_MS     Give up after this long           (default: 2700000)
 *   GATE_POLL_MS        Poll interval                        (default: 15000)
 *
 * Exits non-zero on any failure. The caller decides whether that is fatal:
 * while the repository variable REQUIRE_HOOK_SIGNING is unset, publish.yml warns
 * and ships unsigned hooks; once it is `true`, the same failure stops the
 * publish.
 */

import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { pathToFileURL } from "node:url";

/** Azure DevOps' fixed Entra application ID. Not a tenant-specific value. */
const AZURE_DEVOPS_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798";
const ARTIFACT_NAME = "signed-hooks";
const BEGIN_MARKER = "# SIG # Begin signature block";
const END_MARKER = "# SIG # End signature block";

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not set`);
  return value;
}

function integer(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  const value = Number.parseInt(raw, 10);
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${name} must be a positive integer`);
  return value;
}

/**
 * Read an error body without ever printing a token. Azure DevOps answers an
 * unauthenticated API call with a 203 and an HTML sign-in page rather than a
 * 401, so the status alone is not enough to explain a failure.
 */
async function describeFailure(response) {
  let body = "";
  try {
    body = (await response.text()).slice(0, 400).replace(/\s+/g, " ").trim();
  } catch {
    body = "<unreadable>";
  }
  return `${response.status} ${response.statusText}: ${body}`;
}

/** Exchange this workflow run's GitHub id-token for an Azure DevOps token. */
async function acquireAzureDevOpsToken() {
  const requestUrl = required("ACTIONS_ID_TOKEN_REQUEST_URL");
  const requestToken = required("ACTIONS_ID_TOKEN_REQUEST_TOKEN");
  const tenantId = required("AZURE_TENANT_ID");
  const clientId = required("AZURE_CLIENT_ID");

  const audience = "api://AzureADTokenExchange";
  const idTokenResponse = await fetch(`${requestUrl}&audience=${encodeURIComponent(audience)}`, {
    headers: { Authorization: `Bearer ${requestToken}` },
  });
  if (!idTokenResponse.ok) {
    throw new Error(`could not obtain a GitHub id-token: ${await describeFailure(idTokenResponse)}`);
  }
  const { value: assertion } = await idTokenResponse.json();
  if (!assertion) throw new Error("GitHub returned an empty id-token");

  const form = new URLSearchParams({
    client_id: clientId,
    grant_type: "client_credentials",
    scope: `${AZURE_DEVOPS_RESOURCE}/.default`,
    client_assertion_type: "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    client_assertion: assertion,
  });
  const tokenResponse = await fetch(
    `https://login.microsoftonline.com/${encodeURIComponent(tenantId)}/oauth2/v2.0/token`,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    },
  );
  if (!tokenResponse.ok) {
    throw new Error(
      `Entra rejected the federated credential: ${await describeFailure(tokenResponse)}. ` +
        "Confirm the app registration has a federated credential for this repository and ref.",
    );
  }
  const { access_token: accessToken } = await tokenResponse.json();
  if (!accessToken) throw new Error("Entra returned no access_token");
  return accessToken;
}

class AzureDevOps {
  constructor({ organization, project, token }) {
    this.base = `https://dev.azure.com/${encodeURIComponent(organization)}/${encodeURIComponent(project)}/_apis`;
    this.token = token;
  }

  async request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: {
        Authorization: `Bearer ${this.token}`,
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
    if (!response.ok) throw new Error(await describeFailure(response));
    return response;
  }

  async json(url, options) {
    return (await this.request(url, options)).json();
  }

  /** Queue a run of `pipelineId` and return it. */
  startRun(pipelineId, { ref, templateParameters }) {
    return this.json(`${this.base}/pipelines/${pipelineId}/runs?api-version=7.1`, {
      method: "POST",
      body: JSON.stringify({
        resources: { repositories: { self: { refName: ref } } },
        templateParameters,
      }),
    });
  }

  getRun(pipelineId, runId) {
    return this.json(`${this.base}/pipelines/${pipelineId}/runs/${runId}?api-version=7.1`);
  }

  async getArtifact(runId, name) {
    const artifacts = await this.json(
      `${this.base}/build/builds/${runId}/artifacts?api-version=7.1`,
    );
    const artifact = (artifacts.value ?? []).find((entry) => entry.name === name);
    if (!artifact) {
      const found = (artifacts.value ?? []).map((entry) => entry.name).join(", ") || "none";
      throw new Error(`run ${runId} published no ${quote(name)} artifact (found: ${found})`);
    }
    return artifact;
  }

  /**
   * Download one file out of an artifact. Per-file `subPath` downloads avoid
   * pulling and unpacking a zip, for which Node has no built-in reader.
   */
  async downloadArtifactFile(artifact, fileName) {
    const url = artifactFileUrl(artifact.resource.downloadUrl, fileName);
    const response = await this.request(url, { headers: { Accept: "*/*" } });
    return Buffer.from(await response.arrayBuffer());
  }
}

/**
 * URL that downloads a single file out of a pipeline artifact.
 *
 * `downloadUrl` already carries `format=zip`. Appending another `format`
 * leaves two, and the service honours the first -- returning a zip and
 * ignoring `subPath` -- so these must be set, never concatenated.
 */
export function artifactFileUrl(downloadUrl, fileName) {
  const url = new URL(downloadUrl);
  url.searchParams.set("format", "file");
  url.searchParams.set("subPath", `/${fileName}`);
  return url.toString();
}

function quote(value) {
  return `"${value}"`;
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

/** Wait for a queued run to finish. Throws on failure, cancellation, timeout. */
async function waitForRun(client, pipelineId, runId, { timeoutMs, pollMs }) {
  const deadline = Date.now() + timeoutMs;
  let lastState = "";
  for (;;) {
    const run = await client.getRun(pipelineId, runId);
    if (run.state !== lastState) {
      console.log(`  run ${runId} is ${run.state}`);
      lastState = run.state;
    }
    if (run.state === "completed") {
      if (run.result !== "succeeded") {
        throw new Error(`gate run ${runId} completed with result ${quote(run.result)}: ${run._links?.web?.href ?? ""}`);
      }
      return run;
    }
    if (Date.now() >= deadline) {
      throw new Error(
        `gate run ${runId} still ${run.state} after ${Math.round(timeoutMs / 1000)}s: ${run._links?.web?.href ?? ""}`,
      );
    }
    await sleep(pollMs);
  }
}

function localHookScripts(hooksDir) {
  if (!fs.existsSync(hooksDir)) throw new Error(`hooks directory not found: ${hooksDir}`);
  return fs
    .readdirSync(hooksDir)
    .filter((name) => name.endsWith(".ps1"))
    .sort();
}

/**
 * Overlay the signed scripts, asserting the gate signed exactly the set this
 * commit ships. A mismatch means the gate ran against a different tree -- the
 * failure mode that is otherwise invisible, because the signatures would all be
 * valid, just over bytes nobody released.
 */
export function overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit }) {
  if (manifest.commit !== expectedCommit) {
    throw new Error(
      `gate signed commit ${manifest.commit}, but this run is publishing ${expectedCommit}`,
    );
  }

  const expected = localHookScripts(hooksDir);
  const signed = manifest.scripts.map((entry) => entry.name).sort();
  const missing = expected.filter((name) => !signed.includes(name));
  const extra = signed.filter((name) => !expected.includes(name));
  if (missing.length || extra.length) {
    const parts = [];
    if (missing.length) parts.push(`not signed: ${missing.join(", ")}`);
    if (extra.length) parts.push(`signed but not in this tree: ${extra.join(", ")}`);
    throw new Error(`hook script set does not match the gate (${parts.join("; ")})`);
  }

  for (const entry of manifest.scripts) {
    const content = artifactFiles.get(entry.name);
    const digest = sha256(content);
    if (digest !== entry.sha256) {
      throw new Error(`${entry.name} was altered in transit (expected ${entry.sha256}, got ${digest})`);
    }
    const text = content.toString("utf8");
    if (!text.includes(BEGIN_MARKER) || !text.includes(END_MARKER)) {
      throw new Error(`${entry.name} carries no signature block`);
    }
    // Byte-for-byte, no newline translation: an Authenticode signature covers
    // the exact bytes, so rewriting a single line ending invalidates it.
    fs.writeFileSync(path.join(hooksDir, entry.name), content);
    console.log(`  ${entry.name}: signed by ${entry.subject}`);
  }
}

function emitOutput(name, value) {
  const file = process.env.GITHUB_OUTPUT;
  if (file) fs.appendFileSync(file, `${name}=${value}\n`);
}

async function main() {
  const organization = process.env.ADO_ORGANIZATION || "uipath";
  const project = process.env.ADO_PROJECT || "skills";
  const pipelineId = required("ADO_PIPELINE_ID");
  const channel = required("GATE_CHANNEL");
  const ref = required("GATE_REF");
  const commit = required("GATE_COMMIT");
  const timeoutMs = integer("GATE_TIMEOUT_MS", 45 * 60 * 1000);
  const pollMs = integer("GATE_POLL_MS", 15 * 1000);

  if (!/^[0-9a-f]{40}$/.test(commit)) {
    throw new Error(`GATE_COMMIT must be a full 40-character commit SHA, got ${quote(commit)}`);
  }
  if (channel !== "preview" && channel !== "latest") {
    throw new Error(`GATE_CHANNEL must be "preview" or "latest", got ${quote(channel)}`);
  }

  const token = await acquireAzureDevOpsToken();
  const client = new AzureDevOps({ organization, project, token });

  console.log(`Starting the release gate for ${commit} (${channel}) on ${ref}`);
  const run = await client.startRun(pipelineId, {
    ref,
    templateParameters: { channel, sourceCommit: commit },
  });
  console.log(`Queued run ${run.id}: ${run._links?.web?.href ?? ""}`);

  await waitForRun(client, pipelineId, run.id, { timeoutMs, pollMs });

  const artifact = await client.getArtifact(run.id, ARTIFACT_NAME);
  const manifest = JSON.parse(
    (await client.downloadArtifactFile(artifact, "manifest.json")).toString("utf8"),
  );
  if (!Array.isArray(manifest.scripts) || manifest.scripts.length === 0) {
    throw new Error("gate manifest lists no signed scripts");
  }

  const artifactFiles = new Map();
  for (const entry of manifest.scripts) {
    artifactFiles.set(entry.name, await client.downloadArtifactFile(artifact, entry.name));
  }

  const hooksDir = path.join(process.cwd(), "hooks");
  overlaySignedScripts({ manifest, artifactFiles, hooksDir, expectedCommit: commit });

  console.log(`Overlaid ${manifest.scripts.length} signed hook script(s) from run ${run.id}`);
  emitOutput("signed", "true");
  emitOutput("run-id", String(run.id));
}

// Guarded so the pure helpers above can be imported by tests without the
// module trying to reach Azure DevOps on import.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`fetch-signed-hooks: ${error.message}`);
    emitOutput("signed", "false");
    process.exitCode = 1;
  });
}
