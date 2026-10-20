#!/usr/bin/env node
/**
 * Run the Azure DevOps release gate and wait for its verdict.
 *
 * The gate (.pipelines/release-gate.yml) runs the blocking per-release FOSSA
 * scan — the one thing that cannot be done from GitHub Actions, because the
 * FOSSA secrets are reachable only through an Azure DevOps service
 * connection. Publishing stays in GitHub Actions because npm mints provenance
 * attestations only for GitHub Actions and GitLab CI identities. This script
 * is the seam: it starts the gate pipeline against the exact commit being
 * published and fails the publish when the gate fails.
 *
 * (Until the hooks migrated from PowerShell to Node — see hooks/*.mjs — the
 * gate also Authenticode-signed `hooks/*.ps1` and this script, then named
 * fetch-signed-hooks.mjs, overlaid the signed files before packing. Node hook
 * scripts have no interpreter-enforced signature format; package integrity is
 * carried by the npm provenance attestation instead.)
 *
 * Authentication is OIDC end to end -- no stored credential. GitHub issues an
 * id-token for this workflow run, Entra exchanges it for an Azure DevOps access
 * token through a federated credential scoped to this repository.
 *
 * Usage:
 *   node scripts/run-release-gate.mjs
 *
 * Environment:
 *   AZURE_TENANT_ID     Entra tenant of the federated application (required)
 *   AZURE_CLIENT_ID     Application (client) ID of that application (required)
 *   ADO_ORGANIZATION    Azure DevOps organization           (default: uipath)
 *   ADO_PROJECT         Azure DevOps project                (default: skills)
 *   ADO_PIPELINE_ID     Numeric definition ID of the gate pipeline (required)
 *   GATE_CHANNEL        `preview` or `latest`                       (required)
 *   GATE_REF            Ref to run the gate against, e.g. refs/heads/main
 *   GATE_COMMIT         Commit SHA being published; recorded on the run
 *   GATE_TIMEOUT_MS     Give up after this long           (default: 2700000)
 *   GATE_POLL_MS        Poll interval                        (default: 15000)
 *
 * Exits non-zero on any failure; publish.yml treats that as fatal.
 */

import fs from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { pathToFileURL } from "node:url";

/** Azure DevOps' fixed Entra application ID. Not a tenant-specific value. */
const AZURE_DEVOPS_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798";

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
}

function quote(value) {
  return `"${value}"`;
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

  console.log(`Release gate passed for ${commit} (run ${run.id})`);
  emitOutput("run-id", String(run.id));
}

// Guarded so importing this module never reaches Azure DevOps.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(`run-release-gate: ${error.message}`);
    process.exitCode = 1;
  });
}
