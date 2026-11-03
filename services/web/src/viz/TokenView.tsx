export interface TokenViewProps {
  tokens: string[]
  tokenCount: number
  maxTokens: number
  overLimit: boolean
}

/**
 * Token pills in order (alternating two background colors, data-testid="token"), header
 * "<tokenCount> / <maxTokens> tokens", red badge "over limit — truncated by the model" when overLimit,
 * note "showing first <tokens.length>" when tokens.length < tokenCount.
 */
export function TokenView({
  tokens,
  tokenCount,
  maxTokens,
  overLimit,
}: TokenViewProps): React.ReactElement {
  return (
    <section className="flex flex-col gap-3 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium">
          {tokenCount} / {maxTokens} tokens
        </span>
        {overLimit ? (
          <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
            over limit — truncated by the model
          </span>
        ) : null}
        {tokens.length < tokenCount ? (
          <span className="text-xs text-gray-500">showing first {tokens.length}</span>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {tokens.map((token, i) => (
          <span
            key={i}
            data-testid="token"
            className={`rounded px-2 py-0.5 font-mono text-xs ${i % 2 === 0 ? 'bg-gray-100' : 'bg-gray-50'}`}
          >
            {token}
          </span>
        ))}
      </div>
    </section>
  )
}
