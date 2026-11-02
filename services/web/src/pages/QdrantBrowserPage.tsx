/**
 * Route "/qdrant/:collectionId?". Collection select (navigates). Info card from getQdrantInfo: exists,
 * status, points_count, vector config (shows the names text-dense / text-sparse, size, distance,
 * modifier), payload indexes table. <FilterBuilder> + matching count (countPoints). Points table
 * (scrollPoints limit 20, "Load more" with next_offset): point id (first 8), filename, page,
 * element_type, tags, content (80 chars). Click row → side panel with getPoint raw JSON (<pre>) showing
 * the first 16 dense dims + "… (<n> more)". exists false → "Nothing stored yet in this collection — run
 * the Store stage of an ingest run."
 */
export function QdrantBrowserPage(): React.ReactElement {
  throw new Error('not implemented')
}
