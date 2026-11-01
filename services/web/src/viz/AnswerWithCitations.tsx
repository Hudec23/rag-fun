import type { GenerateArtifact } from '../api/types'

export interface AnswerWithCitationsProps {
  answer: string
  context: GenerateArtifact['context']
  streaming?: boolean
}

/**
 * Answer text where every "[n]" / "[n, m]" marker becomes buttons "[n]" (one per number) that map to
 * context[n] (unknown n → plain text). Clicking a citation shows that chunk card (filename, page,
 * text) below and marks the button aria-pressed. streaming → blinking cursor after the text.
 * Below the answer: the context list numbered [1]..[k].
 */
export function AnswerWithCitations(_props: AnswerWithCitationsProps): React.ReactElement {
  throw new Error('not implemented')
}
