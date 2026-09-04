/**
 * CAPABILITY: read and update a native Data Fabric entity.
 *
 * Use `dataFabricRead` / `dataFabricUpdate` (`core.datafabric.read` /
 * `.update`) only when the scenario names DATA FABRIC. "Data Service" names the
 * `uipath-uipath-dataservice` connector instead, which routes to `connector(...)`.
 *
 * `record` is exactly one of `{ byId }` or `{ fromRead: '<read step name>' }`.
 * Chaining the update off the read — as here — avoids carrying an id by hand.
 * Filters default to `operator: '='`; `or: true` joins a row with OR.
 *
 * Generic scenario: find a hive by its tag and record today's inspection.
 */
import { flow, dataFabricRead, dataFabricUpdate, script, input, out, types } from '@uipath/flow-sdk';

export default flow('bee-hive-ledger')
  .name('BeeHiveLedger')
  .version('1.0.0')
  .input({ hiveTag: types.string, inspectedOn: types.string })
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
  .step('noteLedger', script({
    code:
      'return "hive " + $vars.start.output.hiveTag'
      + ' + " inspected on " + $vars.start.output.inspectedOn;',
  }))
  .return({ ledgerNote: out('noteLedger') })
  .build();
