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
export function TokenView(_props: TokenViewProps): React.ReactElement {
  throw new Error('not implemented')
}
