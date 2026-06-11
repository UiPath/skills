// Typed full-listing helper for SDK list calls.
//
// Every SDK list call returns ONE page (the "NonPaginatedResponse" name is
// misleading — the server still caps it). Listing everything means looping the
// cursor, and hand-writing that loop in every widget invites `let page: any`
// and copy-paste drift. Use this instead:
//
//   const { fetchAll } = await import('@/lib/paginate')
//   const { Jobs } = await import('@uipath/uipath-typescript/jobs')
//   const svc = new Jobs(sdk as never)
//   return await fetchAll(cursor => svc.getAll({ pageSize: 200, cursor }))

/** Structural shape of any SDK page — paginated responses add the cursor fields. */
interface SdkPage<T> {
  items: T[]
  hasNextPage?: boolean
  nextCursor?: string
}

/** Hard stop so a server-side cursor bug can never loop forever. */
const MAX_PAGES = 100

/**
 * Fetch every page of an SDK list call and return the concatenated items.
 * @param getPage Calls the SDK with the given cursor (undefined on the first call).
 */
export async function fetchAll<T>(getPage: (cursor?: string) => Promise<SdkPage<T>>): Promise<T[]> {
  const all: T[] = []
  let cursor: string | undefined
  for (let i = 0; i < MAX_PAGES; i++) {
    const page = await getPage(cursor)
    all.push(...(page.items ?? []))
    if (page.hasNextPage && page.nextCursor) {
      cursor = page.nextCursor
      continue
    }
    return all
  }
  return all
}
