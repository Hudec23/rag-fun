/**
 * Route "/ingest/:runId". useIngestRun(runId). Header: filename, collection, "Run all" button
 * (runAllIngest(runId, null, current params of each stage or INGEST_DEFAULTS)) and pending plan chips.
 * <StageStepper> for parse/chunk/embed/store and the selected <StagePanel>. Default selection = first
 * stage not done (else store), computed ONCE when the run first loads; afterwards only the user changes
 * it. The panel gets run = run.stages[stage] and progress = live.progress[that stage run's id]. Passes
 * extra.chunks (from the active chunk artifact) to the embed panel and extra.collectionId to store.
 * Loading/error states as in CollectionsPage.
 */
export function IngestRunPage(): React.ReactElement {
  throw new Error('not implemented')
}
