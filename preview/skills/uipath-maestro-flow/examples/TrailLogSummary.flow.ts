/**
 * CAPABILITY: the three `transform` VARIANTS — filter, map, group-by — chained.
 *
 *   Filter  → keep the rows you want
 *   Map     → reshape each row (`keepOriginalFields: false` drops the rest)
 *   Group by→ one row per key, with aggregations
 *
 * Each variant node carries EXACTLY ONE operation of the matching type
 * (`variant: 'group-by'` ⇢ `type: 'groupBy'` — node type hyphenated, operation
 * camelCase). Each step's `collection` is the previous step's `out(...)`, which
 * is a path — which is what `collection` wants.
 *
 * Generic scenario: a season of hiking-trail logs → miles walked per difficulty
 * band. Static data lives in a variable default because `collection` is a path.
 */
import { flow, transform, v, out, types } from '@uipath/flow-sdk';

export default flow('trail-log-summary')
  .name('TrailLogSummary')
  .version('1.0.0')
  .output({ perBand: types.array })

  .var('logs', types.array, [
    { trail: 'Cedar Ridge', band: 'moderate', status: 'open', miles: 7 },
    { trail: 'Fern Gully', band: 'easy', status: 'open', miles: 3 },
    { trail: 'Granite Spine', band: 'hard', status: 'closed', miles: 11 },
    { trail: 'Otter Creek', band: 'easy', status: 'open', miles: 4 },
    { trail: 'Storm Pass', band: 'hard', status: 'open', miles: 9 },
    { trail: 'Willow Bend', band: 'moderate', status: 'open', miles: 5 },
  ])

  // 1. Filter — one rule, so the node IS a filter.
  .step('walkable', transform({
    variant: 'filter',
    collection: v('logs'),
    operations: [
      { type: 'filter', operation: 'and', filters: [{ field: 'status', condition: 'equals', value: 'open' }] },
    ],
  }))

  // 2. Map — keep only what step 3 needs. `keepOriginalFields: false` drops the rest.
  .step('summaryFields', transform({
    variant: 'map',
    collection: out('walkable'),
    operations: [
      {
        type: 'map',
        keepOriginalFields: false,
        mappings: [
          { field: 'band', transformation: 'uppercase', renameTo: 'grade' },
          { field: 'miles' },
        ],
      },
    ],
  }))

  // 3. Group by — one row per grade. `count` is the only aggregation with no `field`.
  .step('perBand', transform({
    variant: 'group-by',
    collection: out('summaryFields'),
    operations: [
      {
        type: 'groupBy',
        groupByField: 'grade',
        aggregations: [
          { operation: 'count', alias: 'trails' },
          { operation: 'sum', field: 'miles', alias: 'totalMiles' },
        ],
      },
    ],
  }))

  .return({ perBand: out('perBand') })

  .build();
