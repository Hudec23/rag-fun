import type { FilterCondition, PayloadFilter, RetrieveArtifact } from '../../api/types'
import { HybridLists } from '../../viz/HybridLists'

export interface RetrieveViewProps {
  stageRunId: string
  artifact: RetrieveArtifact
}

/**
 * Header "<mode> · top_k <k> · RRF k <rrf_k>" and active filters as chips ("tags in finance");
 * then <HybridLists>.
 */
export function RetrieveView({ artifact }: RetrieveViewProps): React.ReactElement {
  const chips = filterChips(artifact.filters)

  return (
    <section className="flex flex-col gap-3 p-4">
      <header className="flex flex-wrap items-center gap-2 text-sm">
        <span>{`${artifact.mode} · top_k ${artifact.top_k} · RRF k ${artifact.rrf_k}`}</span>
        {chips.map((chip, i) => (
          <span
            key={i}
            className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800"
          >
            {chip}
          </span>
        ))}
      </header>
      <HybridLists artifact={artifact} />
    </section>
  )
}

/** One chip of text per active condition: must = AND, should = "any of", must_not = "not". */
function filterChips(filter: PayloadFilter): string[] {
  const chips = (filter.must ?? []).map(conditionText)
  for (const condition of filter.should ?? []) chips.push(`any of ${conditionText(condition)}`)
  for (const condition of filter.must_not ?? []) chips.push(`not ${conditionText(condition)}`)
  return chips
}

/** "tags in finance", "mime = application/pdf", "page 1–3". */
function conditionText(condition: FilterCondition): string {
  if ('range' in condition) {
    const { gte, lte } = condition.range
    if (gte !== undefined && lte !== undefined) return `${condition.key} ${gte}–${lte}`
    if (gte !== undefined) return `${condition.key} ≥ ${gte}`
    if (lte !== undefined) return `${condition.key} ≤ ${lte}`
    return condition.key
  }
  if ('any' in condition.match) {
    return `${condition.key} in ${condition.match.any.map(String).join(', ')}`
  }
  return `${condition.key} = ${condition.match.value}`
}
