/**
 * ContractRegistry — the Data Fabric (Data Service) record lifecycle, written with
 * `.dataService()`.
 *
 * One entity, five operations: create a record, query it two ways, replace it, read
 * it back by id, and map the results onto process outputs. Every node is an
 * Integration Service connector activity on `uipath-uipath-dataservice`, emitted in
 * the exact shape Studio Web and the Flow→BPMN converter write — create and update in
 * the ENTITY form (`POST /ContractRegistry`, `PUT /ContractRegistry/{id}`), query and
 * get in the CURATED form (`entityName` as a path parameter, a curated `objectName`) —
 * so it needs no connector library to compile.
 *
 * The connection and its folder are two bindings the process declares once. The
 * folder binding is the connection's COMPANION: the serializer keys it by the
 * connection it is read beside, which is what the platform resolves it through.
 *
 * Every `.dataService()` writes its response to `<id>_response` and the error payload
 * to `<id>_Error`, both declared for you, so the next node reads
 * `=vars.create_response.Id` with nothing more written.
 */
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

// The keys the tenant gave you — `uip is connections list --output json` for the
// connection, the folder it lives in for the folder.
const CONNECTION = '00000000-0000-4000-8000-00000000c0de';
const FOLDER = '00000000-0000-4000-8000-0000000f01de';

const df = { entity: 'ContractRegistry', connection: 'dataFabric', folder: 'dataFabricFolder' } as const;

export default bpmn('ContractRegistry')
  .name('Contract Registry lifecycle')
  .flowMode('sequence')
  .binding('dataFabric', { name: 'Data Fabric connection', resource: 'Connection', propertyAttribute: 'ConnectionId', value: CONNECTION })
  .binding('dataFabricFolder', { name: 'Data Fabric folder', resource: 'Connection', propertyAttribute: 'folderKey', value: FOLDER })
  .var('contractTitle', 'string')
  .output('createdRecord', 'json')
  .output('dueSoon', 'json')
  .output('untitled', 'json')
  .output('retrievedRecord', 'json')
  .startEvent('start', { name: 'Start' })
  .scriptTask('generateTitle', {
    name: 'Generate a contract title',
    script: 'return "Contract-" + Math.random().toString(36).slice(2, 10);',
    outputs: { contractTitle: '=result.response' },
  })
  // ENTITY form: objectName is the entity, the record is the one json body row.
  .dataService('create', {
    ...df,
    op: 'create',
    record: { contractTitle: '=vars.contractTitle', status: 'Open', priority: 2, dueDate: '2026-08-01', value: 12500.5, isUrgent: true },
  })
  // CURATED form: the filter is a query parameter; `start`/`limit` default to 0/100.
  .dataService('queryDue', { ...df, op: 'query', where: "dueDate < '2026-08-04'", limit: 100 })
  .dataService('queryUntitled', { ...df, op: 'query', where: 'contractTitle IS NULL', limit: 100 })
  .dataService('update', {
    ...df,
    op: 'update',
    id: '=vars.create_response.Id',
    record: { contractTitle: '=vars.contractTitle', status: 'Open', priority: 1, dueDate: '2026-08-01', value: 12500.5, isUrgent: true },
  })
  .dataService('get', { ...df, op: 'get', recordId: '=vars.update_response.Id', expansionLevel: 3 })
  .endEvent('done', {
    name: 'Done',
    payload: {
      type: 'BPMN.Variables',
      outputRows: [
        { name: 'createdRecord', type: 'json', var: 'createdRecord', source: '=vars.create_response' },
        { name: 'dueSoon', type: 'json', var: 'dueSoon', source: '=vars.queryDue_response' },
        { name: 'untitled', type: 'json', var: 'untitled', source: '=vars.queryUntitled_response' },
        { name: 'retrievedRecord', type: 'json', var: 'retrievedRecord', source: '=vars.get_response' },
      ],
    },
  })
  .build();
