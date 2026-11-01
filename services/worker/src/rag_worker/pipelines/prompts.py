"""Prompt templates (Jinja, Haystack ChatPromptBuilder). Fixed text; shown in the UI."""

REWRITE_SYSTEM = (
    "You rewrite a user question into one precise search query for a document search engine. "
    "Answer with the query only, no quotes, no explanation."
)
MULTI_QUERY_SYSTEM = (
    "You write {{ n }} different search queries that together cover the user question. "
    "Answer with exactly one query per line, no numbering, no explanation."
)
HYDE_SYSTEM = (
    "Write a short factual passage (3-5 sentences) that would answer the user question, as if it "
    "were taken from a reference document. Answer with the passage only."
)
ANSWER_SYSTEM = (
    "Answer the question using only the numbered context passages. Cite every claim with the "
    "passage number in square brackets, e.g. [1] or [2, 3]. If the context does not contain the "
    "answer, say that you do not know."
)
ANSWER_USER = "Context:\n{% for c in context %}[{{ c.n }}] {{ c.text }}\n\n{% endfor %}Question: {{ question }}"
