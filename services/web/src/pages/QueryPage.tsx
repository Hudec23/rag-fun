/**
 * Route "/query" (new) and "/query/:runId". New: collection select + question textarea + "Ask" →
 * createQueryRun → navigate to /query/<id>. With runId: useQueryRun; header with the question and
 * "Run all" (runAllQuery equivalent: POST /query-runs/{id}/run-all via startQueryStage chain is NOT
 * used — call apiFetch run-all with from_stage null and defaults); <StageStepper> transform/retrieve/
 * rerank/generate + selected <StagePanel> (generate gets liveText from tokens).
 */
export function QueryPage(): React.ReactElement {
  throw new Error('not implemented')
}
