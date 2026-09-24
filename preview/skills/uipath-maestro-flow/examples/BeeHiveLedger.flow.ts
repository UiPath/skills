/**
 * CAPABILITY: native Data Fabric CRUD — query, create, update, delete.
 *
 * `core.datafabric.*` covers all four verbs, so entity CRUD needs no connector
 * and no connection binding. "Data Service" is the SAME product under its
 * connector name (`uipath-uipath-dataservice`); route there only for what the
 * native family lacks — get-by-id, a query with a row limit, file record
 * fields, and Record Created / Updated events.
 *
 * `record` is exactly one of `{ byId }` or `{ fromRead: '<read step name>' }`.
 * Chaining a write off the read — as here — avoids carrying an id by hand.
 * Filters default to `operator: '='`; `or: true` joins a row with OR.
 *
 * `resultMode: 'multiple'` publishes the matches under `output.results` and
 * selects the read node's 1.4 definition; omit it and the step stays on 1.0 and
 * reads ONE record. A delete publishes NOTHING — take what you need off the
 * read step that found the record, before the delete.
 *
 * Nothing here is checked against the real entity: a column name that does not
 * exist is DROPPED rather than rejected, so the flow validates, runs green, and
 * writes nothing. Resolve columns with `uip df entities get` before trusting a
 * write, and never write a system column (`Id`, `CreateTime`, `CreatedBy`,
 * `UpdateTime`, `UpdatedBy`) — Data Fabric assigns those.
 *
 * Generic scenario: find a hive by its tag, record today's inspection, log it,
 * and clear the stale draft the inspection replaces.
 */
import {
  flow, dataFabricRead, dataFabricCreate, dataFabricUpdate, dataFabricDelete,
  script, input, out, types,
} from '@uipath/maestro-builder-sdk';

export default flow('bee-hive-ledger')
  .name('BeeHiveLedger')
  .version('1.0.0')
  .input({ hiveTag: types.string, inspectedOn: types.string, draftId: types.string })
  .output({ ledgerNote: types.string })
  .step('findHive', dataFabricRead({
    entity: 'Hives',
    filters: [{ field: 'HiveTag', value: input('hiveTag') }],
  }))
  .step('recordInspection', dataFabricUpdate({
    entity: 'Hives',
    record: { fromRead: 'findHive' },
    set: { LastInspectedOn: input('inspectedOn'), Status: 'Inspected' },
  }))
  .step('logInspection', dataFabricCreate({
    entity: 'HiveInspections',
    values: { HiveTag: input('hiveTag'), InspectedOn: input('inspectedOn') },
  }))
  .step('dropDraft', dataFabricDelete({
    entity: 'HiveInspectionDrafts',
    record: { byId: input('draftId') },
  }))
  .step('noteLedger', script({
    code:
      'return "hive " + $vars.start.output.hiveTag'
      + ' + " inspected on " + $vars.start.output.inspectedOn;',
  }))
  .return({ ledgerNote: out('noteLedger') })
  .build();
