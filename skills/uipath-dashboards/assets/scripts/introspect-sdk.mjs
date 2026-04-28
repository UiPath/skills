#!/usr/bin/env node
/**
 * SDK introspection — generate a manifest of every service, class, method,
 * and signature the installed @uipath/uipath-typescript package exposes.
 *
 * Uses the TypeScript Compiler API to correctly handle:
 *   - re-exports (`export { JobService as Jobs }`)
 *   - barrel files (`export * from './internal/job-service'`)
 *   - selective re-exports (`export { Jobs } from './jobs'`)
 *   - aliased class names that differ from the implementation file
 *
 * Two run modes:
 *
 *   1. PREFLIGHT (Plan phase, before any project exists):
 *      node introspect-sdk.mjs --root=<cwd>/.uipath-dashboards/.cache/sdk
 *      Reads SDK from <root>/node_modules/@uipath/uipath-typescript
 *      Writes manifest to <root>/sdk-manifest.json
 *
 *   2. PER-PROJECT (after project's npm install, on version drift):
 *      cd <project> && node <skill>/assets/scripts/introspect-sdk.mjs
 *      Reads SDK from <cwd>/node_modules/@uipath/uipath-typescript
 *      Writes manifest to <cwd>/.dashboard/sdk-manifest.json
 *
 * --root flag overrides cwd for both the SDK lookup and the output path:
 *   - SDK at <root>/node_modules/@uipath/uipath-typescript
 *   - manifest at <root>/sdk-manifest.json (preflight) or <root>/.dashboard/sdk-manifest.json
 *     (per-project; --root acts like cwd).
 *
 * Manifest shape:
 *   {
 *     sdkVersion: "1.3.2",
 *     generatedAt: "...",
 *     services: [
 *       {
 *         subpath: "jobs",
 *         dtsPath: "node_modules/@uipath/uipath-typescript/dist/jobs/index.d.ts",
 *         exports: {
 *           classes:    [{ name: "Jobs", aliasOf: "JobService" }, ...],
 *           interfaces: [{ name: "JobGetResponse" }, ...],
 *           types:      [{ name: "JobState" }, ...],
 *         },
 *         methods: [
 *           { class: "Jobs", name: "getAll", params: "options?: JobGetAllOptions", returnType: "Promise<...>" },
 *           ...
 *         ],
 *       },
 *       ...
 *     ]
 *   }
 *
 * Requires `typescript` in cwd's node_modules. Our scaffold's package.json
 * includes it as a devDep, so it's always available after npm install.
 */
import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname, relative } from 'node:path';
import { createRequire } from 'node:module';

// --root=<dir> overrides cwd for SDK lookup AND manifest output location.
// Lets the preflight Plan-phase introspection write to a cache dir without a project.
const rootArg = process.argv.find((a) => a.startsWith('--root='));
const cwd = rootArg ? resolve(rootArg.slice('--root='.length)) : process.cwd();
const sdkRoot = resolve(cwd, 'node_modules/@uipath/uipath-typescript');
const sdkPkgPath = resolve(sdkRoot, 'package.json');

if (!existsSync(sdkPkgPath)) {
  console.error(`[introspect-sdk] No SDK at ${sdkRoot}. Run \`npm install\` first.`);
  process.exit(2);
}

const require = createRequire(cwd + '/');
let ts;
try {
  ts = require('typescript');
} catch (err) {
  console.error(
    `[introspect-sdk] typescript not found in ${cwd}/node_modules. ` +
    `Add "typescript" to devDependencies and run npm install.`,
  );
  console.error(err?.message ?? err);
  process.exit(2);
}

const sdkPkg = JSON.parse(readFileSync(sdkPkgPath, 'utf-8'));
const exportsField = sdkPkg.exports ?? {};

const compilerOptions = {
  target: ts.ScriptTarget.ESNext,
  module: ts.ModuleKind.ESNext,
  moduleResolution: ts.ModuleResolutionKind.NodeNext,
  declaration: true,
  emitDeclarationOnly: true,
  skipLibCheck: true,
  noResolve: false,
  strict: false,
  allowJs: false,
};

function extractMethods(checker, classSymbol, exportName) {
  const methods = [];
  const decl = classSymbol.declarations?.find((d) => ts.isClassDeclaration(d));
  if (!decl || !decl.members) return methods;

  for (const member of decl.members) {
    if (!ts.isMethodDeclaration(member) && !ts.isMethodSignature(member)) continue;
    if (!member.name) continue;

    const name = member.name.getText();
    if (name === 'constructor') continue;

    const modifiers = ts.canHaveModifiers?.(member) ? ts.getModifiers?.(member) : undefined;
    const isPrivate = modifiers?.some(
      (m) =>
        m.kind === ts.SyntaxKind.PrivateKeyword ||
        m.kind === ts.SyntaxKind.ProtectedKeyword,
    );
    if (isPrivate) continue;

    const params = (member.parameters ?? [])
      .map((p) => p.getText().replace(/\s+/g, ' '))
      .join(', ');
    const returnType = member.type
      ? member.type.getText().replace(/\s+/g, ' ')
      : checker.typeToString(checker.getTypeAtLocation(member));

    methods.push({ class: exportName, name, params, returnType });
  }
  return methods;
}

const allDtsPaths = [];
const subpathByDts = new Map();

for (const [exportPath] of Object.entries(exportsField)) {
  if (exportPath === '.' || exportPath === './core') continue;
  const subpath = exportPath.replace('./', '');
  const dtsPath = resolve(sdkRoot, 'dist', subpath, 'index.d.ts');
  if (!existsSync(dtsPath)) continue;
  allDtsPaths.push(dtsPath);
  subpathByDts.set(dtsPath, subpath);
}

if (allDtsPaths.length === 0) {
  console.error('[introspect-sdk] No .d.ts entry points found under SDK exports.');
  process.exit(3);
}

const program = ts.createProgram(allDtsPaths, compilerOptions);
const checker = program.getTypeChecker();

const services = [];

for (const dtsPath of allDtsPaths) {
  const subpath = subpathByDts.get(dtsPath);
  const sourceFile = program.getSourceFile(dtsPath);
  if (!sourceFile) {
    services.push({ subpath, dtsPath: relative(cwd, dtsPath).replace(/\\/g, '/'), error: 'no source file' });
    continue;
  }

  const moduleSymbol = checker.getSymbolAtLocation(sourceFile);
  if (!moduleSymbol) {
    services.push({ subpath, dtsPath: relative(cwd, dtsPath).replace(/\\/g, '/'), error: 'no module symbol' });
    continue;
  }

  const moduleExports = checker.getExportsOfModule(moduleSymbol);

  const classes = [];
  const interfaces = [];
  const types = [];
  const methods = [];

  for (const exp of moduleExports) {
    const exportName = exp.getName();

    let target = exp;
    if (target.flags & ts.SymbolFlags.Alias) {
      try {
        target = checker.getAliasedSymbol(exp);
      } catch {
        continue;
      }
    }

    const targetDecl = target.declarations?.[0];
    if (!targetDecl) continue;

    const aliasOf = exportName !== target.getName() ? target.getName() : undefined;

    if (target.flags & ts.SymbolFlags.Class) {
      classes.push(aliasOf ? { name: exportName, aliasOf } : { name: exportName });
      methods.push(...extractMethods(checker, target, exportName));
    } else if (target.flags & ts.SymbolFlags.Interface) {
      interfaces.push(aliasOf ? { name: exportName, aliasOf } : { name: exportName });
    } else if (target.flags & ts.SymbolFlags.TypeAlias) {
      types.push(aliasOf ? { name: exportName, aliasOf } : { name: exportName });
    } else if (target.flags & ts.SymbolFlags.Enum) {
      types.push({ name: exportName, kind: 'enum', ...(aliasOf ? { aliasOf } : {}) });
    }
  }

  services.push({
    subpath,
    dtsPath: relative(cwd, dtsPath).replace(/\\/g, '/'),
    exports: { classes, interfaces, types },
    methods,
  });
}

const manifest = {
  sdkVersion: sdkPkg.version,
  generatedAt: new Date().toISOString(),
  cwd: cwd.replace(/\\/g, '/'),
  services: services.sort((a, b) => a.subpath.localeCompare(b.subpath)),
};

const outIdx = process.argv.indexOf('--out');
const outPath =
  outIdx >= 0
    ? process.argv[outIdx + 1]
    : resolve(cwd, '.dashboard/sdk-manifest.json');

mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(outPath, JSON.stringify(manifest, null, 2));

const summary = manifest.services
  .map((s) => {
    if (s.error) return `  ${s.subpath}: (${s.error})`;
    const cnames = s.exports.classes
      .map((c) => (c.aliasOf ? `${c.name}=${c.aliasOf}` : c.name))
      .join(', ');
    return `  ${s.subpath}: ${cnames || '(no classes)'} — ${s.methods.length} methods, ${s.exports.interfaces.length} interfaces, ${s.exports.types.length} types`;
  })
  .join('\n');

console.log(`SDK ${manifest.sdkVersion} — ${manifest.services.length} services`);
console.log(summary);
console.log(`\nFull manifest: ${outPath}`);
