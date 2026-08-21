/**
 * CAPABILITY: call a CONNECTOR and read its LIST output as a TYPED COLLECTION.
 *
 *   connector('<connector-key>', '<operation>', { …params }, { connection, folder })
 *
 * The operation is resolved from the curated library at compile — a typo'd
 * operation or field is caught there. A LIST output is a typed collection, so:
 *
 *     $vars.groups.output[0].displayName   // index an element, then a field
 *     $vars.groups.output.length           // a member of the collection
 *     $vars.each.currentItem.displayName   // the loop item, typed from the collection
 *
 * Reading a field off the collection WITHOUT indexing is refused (FC510) — it is
 * undefined at run time. `connection` / `folder` are `bindings.json` ids (see
 * that file). Narrow a call with the operation's own `where` / `pageSize`
 * parameters — one call is one page.
 *
 * Generic scenario: build a community board of the org's interest groups.
 */
import { flow, connector, out, script, js, types } from '@uipath/flow-sdk';

const DIRECTORY = { connection: 'entra', folder: 'shared' } as const;

export default flow('club-directory')
  .name('ClubDirectory')
  .output({ headline: types.string, firstContact: types.string })

  // The list call — one page of groups.
  .step('groups', connector(
    'uipath-microsoft-azureactivedirectory', 'list-groups',
    {},
    DIRECTORY,
  ))

  // An ELEMENT's field and the collection's LENGTH, in one expression site.
  .step('headline', script({
    code: `
      return { text: $vars.groups.output.length + ' clubs; first up: '
                   + $vars.groups.output[0].displayName };
    `,
  }))

  // Iterate the collection — `currentItem` is typed from what it holds, so the
  // body's field reads are CHECKED. A loop runs for effect: its results are not
  // readable after it, so what gates the read below is `check`/`flow-check`.
  .loop('eachClub', out('groups'), (body) =>
    body.step('poster', script({
      code: 'return { line: "This week: " + $vars.eachClub.currentItem.displayName };',
    })),
  )

  .return({
    headline: out('headline', 'text'),
    firstContact: js`$vars.groups.output[0].mail`,
  })
  .build();
