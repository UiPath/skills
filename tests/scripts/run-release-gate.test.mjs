import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, "..", "..", "scripts", "run-release-gate.mjs");
const PRELOAD = pathToFileURL(join(HERE, "support", "redirect-preload.mjs")).href;
const COMMIT = "a".repeat(40);

/**
 * Starts a local stand-in for GitHub's id-token endpoint, Entra and Azure
 * DevOps. `routes` maps "METHOD /path-prefix" to (requestCount, body) => [status, json|text].
 */
async function withServer(routes, body) {
  const requests = [];
  const server = createServer((req, res) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      const text = Buffer.concat(chunks).toString("utf8");
      requests.push({ method: req.method, url: req.url, headers: req.headers, body: text });
      const key = Object.keys(routes).find((k) => `${req.method} ${req.url}`.startsWith(k));
      const [status, payload] = key ? routes[key](requests.length, text) : [404, "no route"];
      res.writeHead(status, { "Content-Type": typeof payload === "string" ? "text/html" : "application/json" });
      res.end(typeof payload === "string" ? payload : JSON.stringify(payload));
    });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    return await body(`http://127.0.0.1:${server.address().port}`, requests);
  } finally {
    server.close();
  }
}

function runGate(origin, env) {
  const dir = mkdtempSync(join(tmpdir(), "gate-"));
  const output = join(dir, "github-output");
  const childEnv = {
    PATH: process.env.PATH,
    SystemRoot: process.env.SystemRoot,
    REDIRECT_FETCH_ORIGIN: origin,
    ACTIONS_ID_TOKEN_REQUEST_URL: "https://token.actions.example/idtoken?api=1",
    ACTIONS_ID_TOKEN_REQUEST_TOKEN: "request-secret",
    AZURE_TENANT_ID: "tenant-1",
    AZURE_CLIENT_ID: "client-1",
    ADO_PIPELINE_ID: "42",
    GATE_CHANNEL: "preview",
    GATE_REF: "refs/heads/main",
    GATE_COMMIT: COMMIT,
    GATE_POLL_MS: "10",
    GITHUB_OUTPUT: output,
    ...env,
  };
  if (process.env.NODE_V8_COVERAGE) childEnv.NODE_V8_COVERAGE = process.env.NODE_V8_COVERAGE;
  const child = spawn(process.execPath, ["--import", PRELOAD, SCRIPT], {
    env: childEnv,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (c) => (stdout += c));
  child.stderr.on("data", (c) => (stderr += c));
  return new Promise((resolve) =>
    child.on("close", (status) => {
      const githubOutput = existsSync(output) ? readFileSync(output, "utf8") : "";
      rmSync(dir, { recursive: true, force: true });
      resolve({ status, stdout, stderr, githubOutput });
    }),
  );
}

const idToken = () => [200, { value: "gh-id-token" }];
const entra = () => [200, { access_token: "ado-token" }];
const queued = () => [200, { id: 7, _links: { web: { href: "https://ado/run/7" } } }];

// Requests 1-3 are the id-token, Entra and queue calls; polls start at 4.
const happyRoutes = (states) => ({
  "GET /idtoken": idToken,
  "POST /tenant-1/oauth2/v2.0/token": entra,
  "POST /uipath/skills/_apis/pipelines/42/runs": queued,
  "GET /uipath/skills/_apis/pipelines/42/runs/7": (n) => [200, states[Math.min(n - 4, states.length - 1)]],
});

test("passing gate: exchanges OIDC for an ADO token, queues the run against the commit and emits run-id", async () => {
  await withServer(
    happyRoutes([{ state: "inProgress" }, { state: "completed", result: "succeeded" }]),
    async (origin, requests) => {
      const result = await runGate(origin, {});
      assert.equal(result.status, 0, result.stderr);
      assert.match(result.stdout, /Starting the release gate for a{40} \(preview\) on refs\/heads\/main/);
      assert.match(result.stdout, /Queued run 7: https:\/\/ado\/run\/7/);
      assert.match(result.stdout, /run 7 is inProgress/);
      assert.match(result.stdout, /Release gate passed for a{40} \(run 7\)/);
      assert.equal(result.githubOutput, "run-id=7\n");

      const idRequest = requests[0];
      assert.match(idRequest.url, /&audience=api%3A%2F%2FAzureADTokenExchange$/);
      assert.equal(idRequest.headers.authorization, "Bearer request-secret");

      const form = new URLSearchParams(requests[1].body);
      assert.equal(form.get("client_id"), "client-1");
      assert.equal(form.get("client_assertion"), "gh-id-token");
      assert.equal(form.get("scope"), "499b84ac-1321-427f-aa17-267ca6975798/.default");

      const start = requests[2];
      assert.equal(start.headers.authorization, "Bearer ado-token");
      assert.deepEqual(JSON.parse(start.body), {
        resources: { repositories: { self: { refName: "refs/heads/main" } } },
        templateParameters: { channel: "preview", sourceCommit: COMMIT },
      });
    },
  );
});

test("gate that completes with a non-success result fails the publish and names the run", async () => {
  await withServer(
    happyRoutes([{ state: "completed", result: "failed", _links: { web: { href: "https://ado/run/7" } } }]),
    async (origin) => {
      const result = await runGate(origin, {});
      assert.equal(result.status, 1);
      assert.match(result.stderr, /run-release-gate: gate run 7 completed with result "failed": https:\/\/ado\/run\/7/);
      assert.equal(result.githubOutput, "");
    },
  );
});

test("gate that outlives GATE_TIMEOUT_MS fails with the last state", async () => {
  await withServer(happyRoutes([{ state: "inProgress" }]), async (origin) => {
    const result = await runGate(origin, { GATE_TIMEOUT_MS: "50" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /gate run 7 still inProgress after 0s/);
  });
});

test("a failed id-token request is reported with a compact body and without leaking tokens", async () => {
  await withServer({ "GET /idtoken": () => [401, "  denied\n  by   policy "] }, async (origin) => {
    const result = await runGate(origin, {});
    assert.equal(result.status, 1);
    assert.match(result.stderr, /could not obtain a GitHub id-token: 401 .*: denied by policy/);
    assert.ok(!result.stderr.includes("request-secret"));
  });
});

test("an empty GitHub id-token is rejected", async () => {
  await withServer({ "GET /idtoken": () => [200, { value: "" }] }, async (origin) => {
    const result = await runGate(origin, {});
    assert.equal(result.status, 1);
    assert.match(result.stderr, /GitHub returned an empty id-token/);
  });
});

test("Entra rejecting the federated credential points at the app registration", async () => {
  await withServer(
    { "GET /idtoken": idToken, "POST /tenant-1/": () => [400, { error: "invalid_client" }] },
    async (origin) => {
      const result = await runGate(origin, {});
      assert.equal(result.status, 1);
      assert.match(result.stderr, /Entra rejected the federated credential: 400/);
      assert.match(result.stderr, /federated credential for this repository and ref/);
    },
  );
});

test("an Entra response without an access_token is rejected", async () => {
  await withServer({ "GET /idtoken": idToken, "POST /tenant-1/": () => [200, {}] }, async (origin) => {
    const result = await runGate(origin, {});
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Entra returned no access_token/);
  });
});

test("an Azure DevOps error when queueing the run fails the gate with its status and body", async () => {
  await withServer(
    {
      "GET /idtoken": idToken,
      "POST /tenant-1/": entra,
      "POST /uipath/skills/_apis/pipelines/42/runs": () => [500, "<html>Boom</html>"],
    },
    async (origin) => {
      const result = await runGate(origin, {});
      assert.equal(result.status, 1);
      assert.match(result.stderr, /run-release-gate: 500 .*<html>Boom<\/html>/);
    },
  );
});

test("ADO_ORGANIZATION and ADO_PROJECT select the pipeline URL", async () => {
  await withServer(
    {
      "GET /idtoken": idToken,
      "POST /tenant-1/": entra,
      "POST /org%20x/proj/_apis/pipelines/42/runs": queued,
      "GET /org%20x/proj/_apis/pipelines/42/runs/7": () => [200, { state: "completed", result: "succeeded" }],
    },
    async (origin) => {
      const result = await runGate(origin, { ADO_ORGANIZATION: "org x", ADO_PROJECT: "proj" });
      assert.equal(result.status, 0, result.stderr);
    },
  );
});

for (const [name, env, message] of [
  ["a short commit SHA", { GATE_COMMIT: "abc123" }, /GATE_COMMIT must be a full 40-character commit SHA, got "abc123"/],
  ["an unknown channel", { GATE_CHANNEL: "beta" }, /GATE_CHANNEL must be "preview" or "latest", got "beta"/],
  ["a missing pipeline id", { ADO_PIPELINE_ID: "" }, /ADO_PIPELINE_ID is not set/],
  ["a non-numeric timeout", { GATE_TIMEOUT_MS: "soon" }, /GATE_TIMEOUT_MS must be a positive integer/],
  ["a zero poll interval", { GATE_POLL_MS: "0" }, /GATE_POLL_MS must be a positive integer/],
  ["a missing token request URL", { ACTIONS_ID_TOKEN_REQUEST_URL: "" }, /ACTIONS_ID_TOKEN_REQUEST_URL is not set/],
]) {
  test(`rejects ${name} before contacting any service`, async () => {
    await withServer({}, async (origin, requests) => {
      const result = await runGate(origin, env);
      assert.equal(result.status, 1);
      assert.match(result.stderr, message);
      assert.equal(requests.length, 0);
    });
  });
}
