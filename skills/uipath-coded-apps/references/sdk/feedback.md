# Agent Feedback — Traps

Signatures/params/examples: `dist/feedback/index.d.ts` (JSDoc documents the required `folderKey` option, default categories, and `createCategory` flag defaults). Per-method scopes: shipped `docs/oauth-scopes.md`. This file covers only what neither can express.

> **Scope warning:** every Feedback method — reads, writes, category management — uses the Traces bundle (`Traces.Api`), not an OR.* or Agents scope. A 403 here means the External App lacks the Traces bundle; check the shipped table.

`getAll()` returns one page — cursor-loop per [pagination.md](pagination.md) when the source may exceed the server's default cap.
