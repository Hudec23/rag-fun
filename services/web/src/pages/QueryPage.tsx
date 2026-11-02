/**
 * Route "/query" (new) and "/query/:runId". New: collection select + question textarea + "Ask" (disabled
 * while the question is empty) → createQueryRun → navigate to /query/<id>. With runId: useQueryRun;
 * header with the question and "Run all" → runAllQuery(runId, null, {transform, retrieve, rerank,
 * generate} = each stage's current params or lib/defaults); <StageStepper> transform/retrieve/rerank/
 * generate + selected <StagePanel> (generate gets liveText = live.tokens[generate stage run id]).
 */
export function QueryPage(): React.ReactElement {
  throw new Error('not implemented')
}
