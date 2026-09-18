// Shared Slack posting for workflow scripts: chat.postMessage as the Skills
// Buddy bot. Slack returns HTTP 200 even on logical failure, so `ok` is the
// only success signal — both callers relied on that quirk being handled once.

const SLACK_URL = "https://slack.com/api/chat.postMessage";

/**
 * Posts one message and returns Slack's response payload (`ts`, `channel`).
 * Pass `thread_ts` in `body` to reply in a thread.
 */
export async function postMessage(token, body) {
  const res = await fetch(SLACK_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify({ unfurl_links: false, ...body }),
  });
  const data = await res.json();
  if (!res.ok || data.ok !== true) {
    throw new Error(`Slack post failed: ${data.error || `${res.status} ${res.statusText}`}`);
  }
  return data;
}

export function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing ${name} environment variable.`);
  return v;
}
