import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chmodSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const skill = resolve(here, '../../skills/uipath-platform');
const { plan, apply, check, FIELD_TYPES, KINDS, ROLES } = await import(join(skill, 'scripts/entities-compile.mjs'));
const fixture = readFileSync(resolve(here, '../fixtures/df-entities/club.entities.json'), 'utf8');
const club = () => JSON.parse(fixture);
const refusedBy = (mutate) => {
  const s = club();
  mutate(s);
  return plan(JSON.stringify(s)).refused.join('\n');
};

test('the club fixture compiles, and twice to the same bytes', () => {
  const a = plan(fixture);
  assert.deepEqual(a.refused, []);
  assert.equal(JSON.stringify(a), JSON.stringify(plan(fixture)));
});

test('choice sets first, each relationship target before its referrer, federated last', () => {
  const s = club();
  s.entities.club_view = {
    kind: 'federated', realizes: [{ class: 'Member', role: 'view' }],
    primary: { entity: 'club_member', fields: { memberId: 'memberId' } },
    sources: [{ entity: 'club_attendance', join: 'memberId', fields: {} }],
  };
  s.entities.club_attendance.fields.memberId = { type: 'STRING', length: 12 };
  s.entities.club_view.sources[0].fields = { memberId: 'attendanceMemberId' };
  const { order, refused } = plan(JSON.stringify(s));
  assert.deepEqual(refused, []);
  assert.equal(order[0], 'choiceSet EventType');
  assert.ok(order.indexOf('entity club_member') < order.indexOf('entity club_attendance'));
  assert.ok(order.indexOf('entity club_event') < order.indexOf('entity club_attendance'));
  assert.equal(order.at(-1), 'entity club_view');
});

test('relationship and choice-set bodies carry placeholders on a folder, names on --local', () => {
  const folder = plan(fixture).steps.find((s) => s.name === 'club_attendance').body.fields[0];
  assert.equal(folder.referenceEntityId, '{{entity club_member.id}}');
  assert.equal(folder.referenceFolderKey, '{{folderKey}}');
  const local = plan(fixture, { local: true }).steps.find((s) => s.name === 'club_event').body.fields.find((f) => f.name === 'type');
  assert.equal(local.choiceSetName, 'EventType');
});

const REFUSALS = {
  'a C# keyword field': [(s) => { s.entities.club_member.fields.virtual = { type: 'BOOLEAN' }; }, 'C# or VB keyword'],
  'a system field': [(s) => { s.entities.club_member.fields.Id = { type: 'BOOLEAN' }; }, 'already has a field'],
  'a choice-set name with _': [(s) => { s.choiceSets.Event_Type = s.choiceSets.EventType; }, 'letters and digits only'],
  'a value name with a symbol': [(s) => { s.choiceSets.EventType.values.push({ name: 'X-Large' }); }, 'starting with a letter'],
  'a STRING with no length': [(s) => { delete s.entities.club_member.fields.email.length; }, 'needs a length'],
  'a DECIMAL with no precision': [(s) => { delete s.entities.club_event.fields.budget.precision; }, 'needs a precision'],
  'an unknown choice set': [(s) => { s.entities.club_event.fields.type.choiceSet = 'Nope'; }, 'is not in choiceSets'],
  'a relationship to an unknown entity': [(s) => { s.entities.club_attendance.fields.member.target = 'club_ghost'; }, 'not in the file'],
  'a relationship to a federated entity': [(s) => {
    s.entities.club_view = { kind: 'federated', realizes: [{ class: 'Member', role: 'view' }], primary: { entity: 'club_member', fields: { memberId: 'memberId' } }, sources: [] };
    s.entities.club_attendance.fields.member.target = 'club_view';
  }, 'a federated entity'],
  'a junction with one relationship': [(s) => { delete s.entities.club_attendance.fields.eventRef; }, 'it has 1'],
  'a relationship cycle': [(s) => { s.entities.club_member.fields.lastEvent = { type: 'RELATIONSHIP', target: 'club_attendance' }; }, 'form a cycle'],
  'kind review': [(s) => { s.entities.club_member.kind = 'review'; }, 'still "review"'],
  'an unknown key': [(s) => { s.entities.club_member.fields.email.maxLength = 3; }, 'unknown key "maxLength"'],
  'a federated source that is not native': [(s) => {
    s.entities.club_view = { kind: 'federated', realizes: [{ class: 'Member', role: 'view' }], primary: { entity: 'club_member', fields: { memberId: 'memberId' } }, sources: [{ entity: 'club_other', join: 'memberId', fields: { memberId: 'm2' } }] };
  }, 'is not a native entity'],
  'the same name selected from two sources': [(s) => {
    s.entities.club_attendance.fields.memberId = { type: 'STRING', length: 12 };
    s.entities.club_view = { kind: 'federated', realizes: [{ class: 'Member', role: 'view' }], primary: { entity: 'club_member', fields: { memberId: 'memberId' } }, sources: [{ entity: 'club_attendance', join: 'memberId', fields: { memberId: 'memberId' } }] };
  }, 'selected from both'],
  'a join field not selected': [(s) => {
    s.entities.club_attendance.fields.memberId = { type: 'STRING', length: 12 };
    s.entities.club_view = { kind: 'federated', realizes: [{ class: 'Member', role: 'view' }], primary: { entity: 'club_member', fields: { email: 'email' } }, sources: [{ entity: 'club_attendance', join: 'memberId', fields: { memberId: 'm2' } }] };
  }, 'the primary must select the join field'],
};
for (const [name, [mutate, reason]] of Object.entries(REFUSALS)) {
  test(`refuses ${name}`, () => assert.match(refusedBy(mutate), new RegExp(reason.replace(/[.*+?^${}()|[\]\\"]/g, '\\$&'))));
}

test('a refused plan has no steps', () => {
  const p = plan('{ not json');
  assert.equal(p.steps.length, 0);
  assert.match(p.refused[0], /not JSON/);
});

test('the documented format and the compiler agree on kinds, roles and field types', () => {
  const schema = JSON.parse(readFileSync(join(skill, 'references/data-fabric/entities.schema.json'), 'utf8'));
  const ent = schema.properties.entities.additionalProperties.properties;
  assert.deepEqual(ent.kind.enum, KINDS);
  assert.deepEqual(ent.realizes.items.properties.role.enum, ROLES);
  assert.deepEqual(ent.fields.additionalProperties.properties.type.enum, FIELD_TYPES);
  assert.deepEqual(Object.keys(ent.fields.additionalProperties.properties).sort(),
    ['choiceSet', 'displayName', 'length', 'precision', 'property', 'required', 'target', 'type', 'unique']);
  assert.deepEqual(check(club()), []);
});

// ---- apply against a fake uip -----------------------------------------------------------------------------

function fakeUip(dir, { failOn, storeRequired } = {}) {
  const log = join(dir, 'calls.log');
  const bin = join(dir, 'uip');
  writeFileSync(bin, `#!/usr/bin/env node
const fs = require('node:fs');
const a = process.argv.slice(2);
fs.appendFileSync(${JSON.stringify(log)}, JSON.stringify(a) + '\\n');
const n = fs.readFileSync(${JSON.stringify(log)}, 'utf8').trim().split('\\n').length;
const id = (k) => (k.toString(16).padStart(8, '0') + '-0000-0000-0000-000000000000');
const out = (o) => { process.stdout.write(JSON.stringify(o)); process.exit(0); };
if (${JSON.stringify(failOn ?? '')} && a.includes(${JSON.stringify(failOn ?? '')}) && a[2] === 'create')
  out({ Result: 'Failure', Message: 'Error creating entity', Instructions: 'Failed to open all connection(s)', Retry: 'RetryWillNotFix' });
if (a[1] === 'entities' && a[2] === 'get') {
  const store = JSON.parse(fs.readFileSync(${JSON.stringify(join(dir, 'store.json'))}, 'utf8'))[a[3]];
  out({ Result: 'Success', Data: { Fields: [{ Name: 'Id', Id: 'idf-' + a[3] }, ...store] } });
}
if (a[1] === 'entities' && a[2] === 'create') {
  const body = JSON.parse(a[a.indexOf('--body') + 1]);
  const p = ${JSON.stringify(join(dir, 'store.json'))};
  const store = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : {};
  store[id(n)] = (body.fields ?? []).map((f) => ({ Name: f.name, IsRequired: ${storeRequired === undefined ? 'f.isRequired' : JSON.stringify(storeRequired)}, IsUnique: !!f.isUnique,
    FieldDataType: { Name: f.type, LengthLimit: f.lengthLimit, DecimalPrecision: f.decimalPrecision },
    ReferenceEntity: f.referenceEntityId ? { Id: f.referenceEntityId } : null, ChoiceSetId: f.choiceSetId }));
  fs.writeFileSync(p, JSON.stringify(store));
  out({ Result: 'Success', Data: { Id: id(n) } });
}
out({ Result: 'Success', Data: { Id: id(n) } });
`);
  chmodSync(bin, 0o755);
  return log;
}

function withFake(opts, run) {
  const dir = mkdtempSync(join(tmpdir(), 'df-entities-'));
  const log = fakeUip(dir, opts);
  const path = process.env.PATH;
  process.env.PATH = `${dir}:${path}`;
  try { return run(dir, log); } finally { process.env.PATH = path; }
}

const calls = (log) => readFileSync(log, 'utf8').trim().split('\n').map((l) => JSON.parse(l));

test('apply creates in order, fills ids from earlier responses, and reads back with no differences', { skip: process.platform === 'win32' }, () => {
  withFake({}, (dir, log) => {
    const state = { path: join(dir, 'state.json'), created: {} };
    const { result, code } = apply(plan(fixture), { state, folderKey: 'fk-1' });
    assert.equal(code, 0, JSON.stringify(result.failed));
    const creates = calls(log).filter((a) => a[2] === 'create' && a[1] === 'entities');
    assert.deepEqual(creates.map((a) => a[3]), ['club_member', 'club_event', 'club_attendance']);
    const attendance = JSON.parse(creates[2][creates[2].indexOf('--body') + 1]);
    assert.equal(attendance.fields[0].referenceEntityId, result.created['entity club_member'].id);
    assert.equal(attendance.fields[0].referenceFieldId, `idf-${result.created['entity club_member'].id}`);
    assert.equal(attendance.fields[0].referenceFolderKey, 'fk-1');
    assert.deepEqual(result.readBack['entity club_event'].differences, []);
  });
});

test('a rerun with the same state skips what exists', { skip: process.platform === 'win32' }, () => {
  withFake({}, (dir, log) => {
    const state = { path: join(dir, 'state.json'), created: {} };
    apply(plan(fixture), { state, folderKey: 'fk-1' });
    const before = calls(log).length;
    const again = apply(plan(fixture), { state: { path: state.path, created: JSON.parse(readFileSync(state.path, 'utf8')).created }, folderKey: 'fk-1' });
    assert.equal(again.code, 0);
    assert.equal(calls(log).length, before);
  });
});

test('a platform failure stops the run and is passed through as returned', { skip: process.platform === 'win32' }, () => {
  withFake({ failOn: 'club_event' }, (dir, log) => {
    const { result, code } = apply(plan(fixture), { state: { path: join(dir, 'state.json'), created: {} }, folderKey: 'fk-1' });
    assert.equal(code, 1);
    assert.equal(result.failed.step, 'entity club_event');
    assert.equal(result.failed.platform.Retry, 'RetryWillNotFix');
    assert.ok(!calls(log).some((a) => a[3] === 'club_attendance'));
  });
});

test('a stored value that differs from the body is reported and exits 1', { skip: process.platform === 'win32' }, () => {
  withFake({ storeRequired: false }, (dir) => {
    const { result, code } = apply(plan(fixture), { state: { path: join(dir, 'state.json'), created: {} }, folderKey: 'fk-1' });
    assert.equal(code, 1);
    assert.match(result.readBack['entity club_member'].differences.join('\n'), /memberId: required false, sent true/);
  });
});

test('a plan compiled for a folder is refused by a local apply', () => {
  const { code, result } = apply(plan(fixture), { state: { path: '/dev/null', created: {} }, local: true, solution: '/nowhere' });
  assert.equal(code, 2);
  assert.match(result.failed.refused, /compiled for folder/);
});
