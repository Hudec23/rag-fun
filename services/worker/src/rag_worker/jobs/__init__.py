"""arq job functions: one module per stage. Each exposes `async def <stage>(ctx, payload) -> dict`
(= run_stage wrapper, written in the skeleton) and `async def <stage>_body(job, rep, ctx)` returning
(artifact, summary) — the part tasks implement."""
