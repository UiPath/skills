// Test-only preload (`node --import <this file> script.mjs`). Lets a test run a
// script that hard-codes its repo root or its remote endpoints against local
// fixtures, without editing the script:
//
//   REDIRECT_FS_FROM / REDIRECT_FS_TO   fs calls on paths under FROM act on TO
//   REDIRECT_FETCH_ORIGIN               fetch() to any URL goes to this origin
//                                       (path and query are kept)
//   REDIRECT_FAST_TIME                  see the bottom of this file
import fs from "node:fs";
import path from "node:path";
import { syncBuiltinESMExports } from "node:module";

const from = process.env.REDIRECT_FS_FROM && path.resolve(process.env.REDIRECT_FS_FROM);
const to = process.env.REDIRECT_FS_TO && path.resolve(process.env.REDIRECT_FS_TO);

if (from && to) {
  const remap = (arg) => {
    if (typeof arg !== "string") return arg;
    const resolved = path.resolve(arg);
    if (resolved === from) return to;
    return resolved.startsWith(from + path.sep) ? path.join(to, resolved.slice(from.length + 1)) : arg;
  };
  for (const name of [
    "readFileSync", "writeFileSync", "appendFileSync", "existsSync", "lstatSync", "statSync",
    "readdirSync", "mkdirSync", "mkdtempSync", "rmSync", "renameSync", "copyFileSync",
    "readlinkSync", "symlinkSync", "utimesSync", "chmodSync", "openSync",
    "unlinkSync", "rmdirSync", "cpSync", "accessSync",
  ]) {
    const original = fs[name];
    if (typeof original !== "function") continue;
    const twoPaths = ["renameSync", "copyFileSync", "cpSync", "symlinkSync"].includes(name);
    fs[name] = (first, second, ...rest) => original(remap(first), twoPaths ? remap(second) : second, ...rest);
  }
  syncBuiltinESMExports();
}

const origin = process.env.REDIRECT_FETCH_ORIGIN;
if (origin) {
  const realFetch = globalThis.fetch;
  globalThis.fetch = (input, init) => {
    const url = new URL(input instanceof Request ? input.url : String(input));
    return realFetch(`${origin}${url.pathname}${url.search}`, init);
  };
}

// REDIRECT_FAST_TIME=1: timers of a second or more fire after 1ms and Date.now()
// advances a minute per call, so a script's polling deadline passes quickly.
if (process.env.REDIRECT_FAST_TIME) {
  const realSetTimeout = globalThis.setTimeout;
  globalThis.setTimeout = (fn, ms, ...rest) => realSetTimeout(fn, ms >= 1000 ? 1 : ms, ...rest);
  const realNow = Date.now.bind(Date);
  let calls = 0;
  Date.now = () => realNow() + 60_000 * calls++;
}
