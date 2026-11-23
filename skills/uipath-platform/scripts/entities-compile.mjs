#!/usr/bin/env node
// Compiles an approved entity schema (entities.json) into Data Fabric creates, and runs them.
//
//   node entities-compile.mjs plan  --schema entities.json --out plan.json [--local]
//   node entities-compile.mjs apply --plan plan.json --state state.json --out result.json --folder-key <key> [--profile <p>]
//   node entities-compile.mjs apply --plan plan.json --state state.json --out result.json --local --solution <dir>
//
// plan reads one file and touches no network. apply runs `uip df` in the plan's order.
// Exit codes: 0 ok; 1 the platform failed or stored something other than what was sent; 2 refused.
// The format, the gates and both responses: references/data-fabric/entities-from-schema.md.

import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export const FIELD_TYPES = ['STRING', 'DECIMAL', 'BOOLEAN', 'DATE', 'DATETIME_WITH_TZ', 'CHOICE_SET_SINGLE', 'RELATIONSHIP'];
export const KINDS = ['native', 'federated', 'review'];
export const ROLES = ['owner', 'part', 'copy', 'junction', 'view'];
const FIELD_KEYS = ['type', 'displayName', 'length', 'precision', 'required', 'unique', 'choiceSet', 'target', 'property'];
const ENTITY_KEYS = ['kind', 'displayName', 'realizes', 'fields', 'primary', 'sources'];
// Fields every entity already has.
const SYSTEM_FIELDS = ['Id', 'CreateTime', 'UpdateTime', 'CreatedBy', 'UpdatedBy', 'RecordOwner'];
// Data Fabric refuses C# and VB keywords as field names, in any letter case (RESERVED_LANGUAGE_KEYWORDS).
export const LANGUAGE_KEYWORDS = new Set(`abstract as base bool break byte case catch char checked class const continue decimal default
delegate do double else enum event explicit extern false finally fixed float for foreach goto if implicit in int interface internal is
lock long namespace new null object operator out override params private protected public readonly ref return sbyte sealed short sizeof
stackalloc static string struct switch this throw true try typeof uint ulong unchecked unsafe ushort using virtual void volatile while
addhandler addressof alias and andalso ansi auto boolean byref byval call cbool cbyte cchar cdate cdbl cdec cint clng cobj csbyte cshort
csng cstr ctype cuint culng cushort date declare dim directcast each elseif end endif erase error exit friend function get gettype
getxmlnamespace global gosub handles implements imports inherits integer let lib like loop me mod module mustinherit mustoverride mybase
myclass narrowing next not nothing notinheritable notoverridable of on option optional or orelse overloads overridable overrides
paramarray partial property raiseevent redim rem removehandler resume select set shadows shared single step stop sub synclock then to
trycast until variant wend when widening with withevents writeonly xor`.split(/\s+/));
const FIELD_NAME = /^[A-Za-z][A-Za-z0-9_]{0,99}$/;
const CHOICE_SET_NAME = /^[A-Za-z0-9]+$/;
const VALUE_NAME = /^[A-Za-z][A-Za-z0-9]*$/;

const hash = (text) => createHash('sha256').update(text).digest('hex').slice(0, 16);
const isObj = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const names = (o) => Object.keys(o).sort();

// ---- plan -------------------------------------------------------------------------------------------------

/** Checks a parsed entities.json. Returns the reasons it is refused; empty when it can be compiled. */
export function check(schema) {
  const why = [];
  if (!isObj(schema)) return ['the file is not a JSON object'];
  for (const k of Object.keys(schema)) if (!['version', 'choiceSets', 'entities'].includes(k)) why.push(`unknown key "${k}"`);
  if (schema.version !== 1) why.push('version must be 1');
  const sets = schema.choiceSets ?? {};
  const ents = schema.entities;
  if (!isObj(sets)) why.push('choiceSets must be an object');
  if (!isObj(ents) || !Object.keys(ents).length) return [...why, 'entities must be an object with at least one entity'];

  for (const [name, cs] of Object.entries(isObj(sets) ? sets : {})) {
    if (!CHOICE_SET_NAME.test(name)) why.push(`choice set ${name}: a choice-set name is letters and digits only`);
    if (!isObj(cs) || !Array.isArray(cs.values) || !cs.values.length) { why.push(`choice set ${name}: needs values`); continue; }
    for (const k of Object.keys(cs)) if (!['displayName', 'values'].includes(k)) why.push(`choice set ${name}: unknown key "${k}"`);
    const seen = new Set();
    for (const v of cs.values) {
      if (!isObj(v) || typeof v.name !== 'string') { why.push(`choice set ${name}: each value needs a name`); continue; }
      if (!VALUE_NAME.test(v.name)) why.push(`choice set ${name}.${v.name}: a value name is letters and digits, starting with a letter`);
      if (seen.has(v.name.toLowerCase())) why.push(`choice set ${name}.${v.name}: the value is listed twice`);
      seen.add(v.name.toLowerCase());
    }
  }

  const kindOf = (e) => (isObj(ents[e]) ? ents[e].kind : undefined);
  for (const [name, e] of Object.entries(ents)) {
    const at = `entity ${name}`;
    if (!isObj(e)) { why.push(`${at}: must be an object`); continue; }
    for (const k of Object.keys(e)) if (!ENTITY_KEYS.includes(k)) why.push(`${at}: unknown key "${k}"`);
    if (!KINDS.includes(e.kind)) { why.push(`${at}: kind must be one of ${KINDS.join(', ')}`); continue; }
    if (e.kind === 'review') why.push(`${at}: kind is still "review"; the review settles native or federated before anything is created`);
    if (!Array.isArray(e.realizes) || !e.realizes.length) why.push(`${at}: realizes names no class`);
    for (const r of Array.isArray(e.realizes) ? e.realizes : []) {
      if (!isObj(r) || typeof r.class !== 'string' || !ROLES.includes(r.role)) why.push(`${at}: each realizes entry needs a class and a role (${ROLES.join(', ')})`);
    }
    if (e.kind === 'federated') { checkFederated(name, e, ents, why); continue; }
    if (e.primary !== undefined || e.sources !== undefined) why.push(`${at}: primary and sources belong to a federated entity`);
    if (!isObj(e.fields) || !Object.keys(e.fields).length) { why.push(`${at}: has no fields`); continue; }
    let relationships = 0;
    for (const [fname, f] of Object.entries(e.fields)) {
      const fat = `${name}.${fname}`;
      if (!FIELD_NAME.test(fname)) why.push(`${fat}: a field name starts with a letter and holds letters, digits and _`);
      if (SYSTEM_FIELDS.includes(fname)) why.push(`${fat}: every entity already has a field of this name`);
      if (LANGUAGE_KEYWORDS.has(fname.toLowerCase())) why.push(`${fat}: a C# or VB keyword, not a usable field name`);
      if (!isObj(f)) { why.push(`${fat}: must be an object`); continue; }
      for (const k of Object.keys(f)) if (!FIELD_KEYS.includes(k)) why.push(`${fat}: unknown key "${k}"`);
      if (!FIELD_TYPES.includes(f.type)) { why.push(`${fat}: type must be one of ${FIELD_TYPES.join(', ')}`); continue; }
      if (f.type === 'STRING' && !(Number.isInteger(f.length) && f.length > 0)) why.push(`${fat}: a STRING needs a length; none is defaulted`);
      if (f.type === 'DECIMAL' && !(Number.isInteger(f.precision) && f.precision >= 0)) why.push(`${fat}: a DECIMAL needs a precision; none is defaulted`);
      if (f.type !== 'STRING' && f.length !== undefined) why.push(`${fat}: length belongs to a STRING`);
      if (f.type !== 'DECIMAL' && f.precision !== undefined) why.push(`${fat}: precision belongs to a DECIMAL`);
      if (f.type === 'CHOICE_SET_SINGLE' && !(isObj(sets) && sets[f.choiceSet])) why.push(`${fat}: choice set "${f.choiceSet}" is not in choiceSets`);
      if (f.type !== 'CHOICE_SET_SINGLE' && f.choiceSet !== undefined) why.push(`${fat}: choiceSet belongs to a CHOICE_SET_SINGLE`);
      if (f.type === 'RELATIONSHIP') {
        relationships += 1;
        if (kindOf(f.target) !== 'native') why.push(`${fat}: a relationship must point at a native entity of this file; "${f.target}" is ${kindOf(f.target) ? `a ${kindOf(f.target)} entity` : 'not in the file'}`);
      } else if (f.target !== undefined) why.push(`${fat}: target belongs to a RELATIONSHIP`);
      for (const b of ['required', 'unique']) if (f[b] !== undefined && typeof f[b] !== 'boolean') why.push(`${fat}: ${b} is true or false`);
    }
    if ((e.realizes ?? []).some((r) => r?.role === 'junction') && relationships < 2) {
      why.push(`${at}: a junction holds a relationship to each side; it has ${relationships}`);
    }
  }
  const cycle = findCycle(ents);
  if (cycle) why.push(`relationships form a cycle (${cycle.join(' → ')}): each target must exist before the field that points at it`);
  return why;
}

function checkFederated(name, e, ents, why) {
  const at = `entity ${name}`;
  if (e.fields !== undefined) why.push(`${at}: a federated entity selects fields from its sources; it has no fields of its own`);
  const parts = [];
  if (!isObj(e.primary)) why.push(`${at}: needs primary: { entity, fields }`);
  else parts.push({ ...e.primary, role: 'primary' });
  if (!Array.isArray(e.sources) || !e.sources.length) why.push(`${at}: needs at least one source`);
  else parts.push(...e.sources.map((s) => ({ ...s, role: 'source' })));
  const selected = new Map();
  for (const p of parts) {
    const src = ents[p.entity];
    if (!isObj(src) || src.kind !== 'native') { why.push(`${at}: source "${p.entity}" is not a native entity of this file`); continue; }
    if (!isObj(p.fields) || !Object.keys(p.fields).length) { why.push(`${at}: selects no fields from ${p.entity}`); continue; }
    for (const [from, as] of Object.entries(p.fields)) {
      if (!(src.fields && from in src.fields)) why.push(`${at}: ${p.entity} has no field "${from}"`);
      if (typeof as !== 'string' || !FIELD_NAME.test(as)) why.push(`${at}: ${p.entity}.${from} needs a usable name in the view`);
      // The tenant refuses a view where two sources select a field under the same name.
      if (selected.has(as)) why.push(`${at}: "${as}" is selected from both ${selected.get(as)} and ${p.entity}; rename one`);
      selected.set(as, p.entity);
    }
    if (p.role === 'source') {
      if (typeof p.join !== 'string') why.push(`${at}: source ${p.entity} needs join: the field it shares with the primary`);
      else {
        // The server joins only on fields its sources select.
        if (!(isObj(p.fields) && p.join in p.fields)) why.push(`${at}: ${p.entity} must select its join field "${p.join}"`);
        if (!(isObj(e.primary?.fields) && p.join in e.primary.fields)) why.push(`${at}: the primary must select the join field "${p.join}"`);
      }
    }
  }
}

function findCycle(ents) {
  const edges = (e) => Object.values(isObj(ents[e]?.fields) ? ents[e].fields : {})
    .filter((f) => f?.type === 'RELATIONSHIP' && ents[f.target]).map((f) => f.target).sort();
  const state = {};
  const visit = (e, path) => {
    if (state[e] === 'done') return null;
    if (state[e] === 'open') return [...path.slice(path.indexOf(e)), e];
    state[e] = 'open';
    for (const t of edges(e)) { const c = visit(t, [...path, e]); if (c) return c; }
    state[e] = 'done';
    return null;
  };
  for (const e of names(ents)) { const c = visit(e, []); if (c) return c; }
  return null;
}

/** Choice sets by name, natives with each relationship target first, federated entities last. */
export function createOrder(schema) {
  const ents = schema.entities;
  const natives = [];
  const seen = new Set();
  const visit = (e) => {
    if (seen.has(e)) return;
    seen.add(e);
    for (const f of Object.values(ents[e].fields)) if (f.type === 'RELATIONSHIP') visit(f.target);
    natives.push(e);
  };
  names(ents).filter((e) => ents[e].kind === 'native').forEach(visit);
  return [
    ...names(schema.choiceSets ?? {}).map((n) => `choiceSet ${n}`),
    ...natives.map((n) => `entity ${n}`),
    ...names(ents).filter((e) => ents[e].kind === 'federated').map((n) => `entity ${n}`),
  ];
}

const realizesText = (e) => [...new Set(e.realizes.map((r) => `:${r.class}`))].sort().join(', ');

function fieldBody(name, f, local) {
  const b = { name, type: f.type, displayName: f.displayName ?? name, isRequired: f.required === true };
  if (f.unique) b.isUnique = true;
  if (f.type === 'STRING') b.lengthLimit = f.length;
  if (f.type === 'DECIMAL') b.decimalPrecision = f.precision;
  if (f.type === 'CHOICE_SET_SINGLE') {
    if (local) b.choiceSetName = f.choiceSet;
    else b.choiceSetId = `{{choiceSet ${f.choiceSet}.id}}`;
  }
  if (f.type === 'RELATIONSHIP') {
    if (local) b.referenceEntityName = f.target;
    else Object.assign(b, { referenceEntityId: `{{entity ${f.target}.id}}`, referenceFieldId: `{{entity ${f.target}.idField}}`, referenceFolderKey: '{{folderKey}}' });
  }
  return b;
}

function federatedBody(name, e, local) {
  const parts = [e.primary, ...e.sources];
  const pick = (p) => Object.entries(p.fields).map(([from, as]) => (from === as ? from : { source: from, name: as }));
  const srcNames = parts.map((p) => p.entity).join(', ');
  return {
    displayName: e.displayName ?? name,
    description: `Federated view over ${srcNames}.`,
    externalFields: parts.map((p) => (local
      ? { entityName: p.entity, fields: pick(p) }
      : { entityId: `{{entity ${p.entity}.id}}`, folderKey: '{{folderKey}}', fields: pick(p) })),
    joins: e.sources.map((s) => ({
      source: e.primary.entity, relatedSource: s.entity, sourceField: s.join, relatedField: s.join,
      ...(local
        ? { sourceConnectionName: e.primary.entity, relatedConnectionName: s.entity }
        : { sourceConnectionId: `{{entity ${e.primary.entity}.id}}`, relatedConnectionId: `{{entity ${s.entity}.id}}` }),
    })),
  };
}

function traceOf(schema) {
  const rows = [];
  const ents = schema.entities;
  const roleFor = (e, property) => {
    const cls = property.split('.')[0];
    return ents[e].realizes.find((r) => r.class === cls)?.role ?? null;
  };
  for (const e of names(ents)) {
    const ent = ents[e];
    if (ent.kind === 'native') {
      for (const [f, d] of Object.entries(ent.fields)) if (d.property) rows.push({ property: d.property, entity: e, field: f, role: roleFor(e, d.property) });
    } else {
      for (const p of [ent.primary, ...ent.sources]) {
        for (const [from, as] of Object.entries(p.fields)) {
          const property = ents[p.entity].fields[from].property;
          if (property) rows.push({ property, entity: e, field: as, role: 'view', from: `${p.entity}.${from}` });
        }
      }
    }
  }
  return rows;
}

/** Compiles entities.json text into the plan response. Never throws on bad input: refusals come back in `refused`. */
export function plan(text, { local = false } = {}) {
  const response = { schemaHash: hash(text), target: local ? 'local' : 'folder', order: [], steps: [], trace: [], refused: [] };
  let schema;
  try { schema = JSON.parse(text); } catch (err) { response.refused.push(`not JSON: ${err.message}`); return response; }
  response.refused = check(schema);
  if (response.refused.length) return response;
  response.order = createOrder(schema);
  for (const id of response.order) {
    const [kind, name] = id.split(' ');
    if (kind === 'choiceSet') {
      const cs = schema.choiceSets[name];
      response.steps.push({ id, kind, name, displayName: cs.displayName ?? name, values: cs.values.map((v) => [v.name, v.displayName ?? v.name]) });
      continue;
    }
    const e = schema.entities[name];
    const dependsOn = e.kind === 'native'
      ? [...new Set(Object.values(e.fields).flatMap((f) => (f.type === 'RELATIONSHIP' ? [`entity ${f.target}`] : f.type === 'CHOICE_SET_SINGLE' ? [`choiceSet ${f.choiceSet}`] : [])))].sort()
      : [...new Set([e.primary, ...e.sources].map((p) => `entity ${p.entity}`))].sort();
    const body = e.kind === 'native'
      ? { displayName: e.displayName ?? name, description: `Realizes ${realizesText(e)} (native).`, fields: Object.entries(e.fields).map(([f, d]) => fieldBody(f, d, local)) }
      : federatedBody(name, e, local);
    response.steps.push({ id, kind: 'entity', entityKind: e.kind, name, dependsOn, body });
  }
  response.trace = traceOf(schema);
  return response;
}

// ---- apply ------------------------------------------------------------------------------------------------

const ENV = { UIPATH_CLI_DISABLE_VERSION_SYNC: '1', UIPATH_CLI_DISABLE_AUTOINSTALL: '1', UIPATH_CLI_DISABLE_TOOL_LINE_CHECK: '1' };

function uip(args, { cwd, profile }) {
  const full = [...args, '--output', 'json', ...(profile ? ['--profile', profile] : [])];
  const r = spawnSync('uip', full, { cwd, encoding: 'utf8', env: { ...process.env, ...ENV } });
  const out = r.stdout ?? '';
  try {
    const parsed = JSON.parse(out.slice(out.indexOf('{')));
    return { ok: parsed.Result === 'Success', response: parsed };
  } catch {
    return { ok: false, response: { Result: 'Failure', Message: `uip gave no JSON (exit ${r.status})`, Output: `${out}${r.stderr ?? ''}`.slice(-600) } };
  }
}

function findId(data) {
  if (!isObj(data)) return null;
  for (const k of ['ID', 'Id', 'id', 'EntityId', 'ChoiceSetId']) {
    if (typeof data[k] === 'string' && /^[0-9a-fA-F-]{36}$/.test(data[k])) return data[k];
  }
  for (const v of Object.values(data)) { const got = findId(v); if (got) return got; }
  return null;
}

function fill(value, ctx) {
  if (Array.isArray(value)) return value.map((v) => fill(v, ctx));
  if (isObj(value)) return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, fill(v, ctx)]));
  if (typeof value !== 'string') return value;
  const m = /^\{\{(.+)\}\}$/.exec(value);
  if (!m) return value;
  if (m[1] === 'folderKey') return ctx.folderKey;
  const [, step, key] = /^(.+)\.(id|idField)$/.exec(m[1]) ?? [];
  const got = ctx.created[step]?.[key];
  if (!got) throw new Error(`placeholder {{${m[1]}}} has no value: ${step} was not created first`);
  return got;
}

/** Field-by-field differences between what was sent and what the platform stored. */
export function compare(body, stored, { local }) {
  const diffs = [];
  const byName = new Map((stored ?? []).map((f) => [f.Name, f]));
  for (const want of body.fields ?? []) {
    const have = byName.get(want.name);
    if (!have) { diffs.push(`${want.name}: not stored`); continue; }
    const t = have.FieldDataType ?? {};
    const sql = have.SqlType ?? {};
    // A local read-back gives the SQL type (NVARCHAR, DECIMAL, …), not the field type, so the type is compared only on a tenant.
    if (!local && t.Name !== want.type) diffs.push(`${want.name}: type ${t.Name}, sent ${want.type}`);
    if (want.type === 'STRING' && (t.LengthLimit ?? sql.LengthLimit) !== want.lengthLimit) diffs.push(`${want.name}: length ${t.LengthLimit ?? sql.LengthLimit}, sent ${want.lengthLimit}`);
    if (want.type === 'DECIMAL' && (t.DecimalPrecision ?? sql.DecimalPrecision) !== want.decimalPrecision) diffs.push(`${want.name}: precision ${t.DecimalPrecision ?? sql.DecimalPrecision}, sent ${want.decimalPrecision}`);
    if (Boolean(have.IsRequired) !== Boolean(want.isRequired)) diffs.push(`${want.name}: required ${Boolean(have.IsRequired)}, sent ${Boolean(want.isRequired)}`);
    if (Boolean(have.IsUnique) !== Boolean(want.isUnique)) diffs.push(`${want.name}: unique ${Boolean(have.IsUnique)}, sent ${Boolean(want.isUnique)}`);
    if (want.referenceEntityId && have.ReferenceEntity?.Id !== want.referenceEntityId) diffs.push(`${want.name}: points at ${have.ReferenceEntity?.Id}, sent ${want.referenceEntityId}`);
    if (want.referenceEntityName && have.ReferenceEntity?.Name !== want.referenceEntityName) diffs.push(`${want.name}: points at ${have.ReferenceEntity?.Name}, sent ${want.referenceEntityName}`);
    if (want.choiceSetId && have.ChoiceSetId !== want.choiceSetId) diffs.push(`${want.name}: choice set ${have.ChoiceSetId}, sent ${want.choiceSetId}`);
  }
  for (const ext of body.externalFields ?? []) {
    for (const f of ext.fields) {
      const name = typeof f === 'string' ? f : f.name;
      if (!byName.has(name)) diffs.push(`${name}: not stored`);
    }
  }
  return diffs;
}

/** Runs a plan. Returns the result response and the exit code. */
export function apply(planned, { state, folderKey, profile, local, solution }) {
  const target = local ? 'local' : 'folder';
  const result = { planHash: hash(JSON.stringify(planned)), target, ...(local ? { solution } : { folderKey }), created: state.created, readBack: {}, failed: null };
  if (planned.target !== target) return { result: { ...result, failed: { step: null, refused: `the plan was compiled for ${planned.target}; apply was asked for ${target}` } }, code: 2 };
  if (planned.refused?.length) return { result: { ...result, failed: { step: null, refused: 'the plan was refused; nothing to apply' } }, code: 2 };
  const where = local ? ['--local'] : ['--folder-key', folderKey];
  const opts = { cwd: local ? solution : undefined, profile: local ? undefined : profile };
  const save = () => writeFileSync(state.path, `${JSON.stringify({ target, folderKey, solution, created: state.created }, null, 2)}\n`);
  let differences = 0;
  for (const step of planned.steps) {
    const done = state.created[step.id];
    if (step.kind === 'choiceSet') {
      if (done && done.values.length === step.values.length) continue;
      if (!done) {
        const r = uip(['df', 'choice-sets', 'create', step.name, '--display-name', step.displayName, ...where], opts);
        if (!r.ok) return { result: { ...result, failed: { step: step.id, platform: r.response } }, code: 1 };
        state.created[step.id] = { id: local ? step.name : findId(r.response.Data), values: [] };
        save();
      }
      const made = state.created[step.id];
      for (const [vname, vdisplay] of step.values) {
        if (made.values.includes(vname)) continue;
        const r = uip(['df', 'choice-set-values', 'create', local ? step.name : made.id, vname, '--display-name', vdisplay, ...where], opts);
        if (!r.ok) return { result: { ...result, failed: { step: `${step.id} value ${vname}`, platform: r.response } }, code: 1 };
        made.values.push(vname);
        save();
      }
      continue;
    }
    if (done) continue;
    let body;
    try { body = fill(step.body, { folderKey, created: state.created }); } catch (err) {
      return { result: { ...result, failed: { step: step.id, refused: err.message } }, code: 2 };
    }
    const r = uip(['df', 'entities', 'create', step.name, '--body', JSON.stringify(body), ...where], opts);
    if (!r.ok) return { result: { ...result, failed: { step: step.id, platform: r.response } }, code: 1 };
    const id = local ? step.name : findId(r.response.Data);
    const got = uip(['df', 'entities', 'get', id, ...where], opts);
    if (!got.ok) return { result: { ...result, failed: { step: `${step.id} read back`, platform: got.response } }, code: 1 };
    const fields = got.response.Data?.Fields ?? [];
    state.created[step.id] = { id, idField: fields.find((f) => f.Name === 'Id')?.Id ?? null };
    save();
    const diffs = compare(body, fields, { local });
    differences += diffs.length;
    result.readBack[step.id] = { fields: (body.fields ?? body.externalFields.flatMap((x) => x.fields)).length, differences: diffs };
  }
  if (local) {
    const v = uip(['df', 'entities', 'validate', '--local'], opts);
    result.validate = v.response;
    if (!v.ok || v.response.Data?.Valid === false) return { result: { ...result, failed: { step: 'validate', platform: v.response } }, code: 1 };
  }
  return { result, code: differences ? 1 : 0 };
}

// ---- command line -----------------------------------------------------------------------------------------

function args(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (!a.startsWith('--')) out._.push(a);
    else if (a === '--local') out.local = true;
    else out[a.slice(2)] = argv[(i += 1)];
  }
  return out;
}

function main(argv) {
  const a = args(argv);
  const usage = 'usage: entities-compile.mjs plan --schema <entities.json> --out <plan.json> [--local]\n'
    + '       entities-compile.mjs apply --plan <plan.json> --state <state.json> --out <result.json> (--folder-key <key> [--profile <p>] | --local --solution <dir>)';
  if (a._[0] === 'plan' && a.schema && a.out) {
    const response = plan(readFileSync(a.schema, 'utf8'), { local: a.local });
    writeFileSync(a.out, `${JSON.stringify(response, null, 2)}\n`);
    process.stdout.write(`${JSON.stringify({ out: a.out, steps: response.steps.length, refused: response.refused })}\n`);
    return response.refused.length ? 2 : 0;
  }
  if (a._[0] === 'apply' && a.plan && a.state && a.out && (a.local ? a.solution : a['folder-key'])) {
    const prior = existsSync(a.state) ? JSON.parse(readFileSync(a.state, 'utf8')) : null;
    if (prior && (prior.target !== (a.local ? 'local' : 'folder') || (a.local ? prior.solution !== a.solution : prior.folderKey !== a['folder-key']))) {
      process.stderr.write(`${a.state} belongs to another target; use a new state file\n`);
      return 2;
    }
    const { result, code } = apply(JSON.parse(readFileSync(a.plan, 'utf8')), {
      state: { path: a.state, created: prior?.created ?? {} }, folderKey: a['folder-key'], profile: a.profile, local: a.local, solution: a.solution,
    });
    writeFileSync(a.out, `${JSON.stringify(result, null, 2)}\n`);
    process.stdout.write(`${JSON.stringify({ out: a.out, created: Object.keys(result.created).length, failed: result.failed })}\n`);
    return code;
  }
  process.stderr.write(`${usage}\n`);
  return 2;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) process.exit(main(process.argv.slice(2)));
