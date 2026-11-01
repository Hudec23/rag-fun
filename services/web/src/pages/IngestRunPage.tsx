/**
 * Route "/ingest/:runId". useIngestRun(runId). Header: filename, collection, "Run all" button
 * (runAllIngest(runId, null, current params of each stage or INGEST_DEFAULTS)) and pending plan chips.
 * <StageStepper> for parse/chunk/embed/store (default selection: first stage not done, else store) and
 * the selected <StagePanel>. Passes extra.chunks (from the active chunk artifact) to the embed panel
 * and extra.collectionId to store. Loading/error states as in CollectionsPage.
 */
export function IngestRunPage(): React.ReactElement {
  throw new Error('not implemented')
}
