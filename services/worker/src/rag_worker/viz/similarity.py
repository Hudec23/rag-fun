import math


def cosine_matrix(vectors: list[list[float]]) -> list[list[float]]:
    """Square cosine similarity matrix, values clipped to [-1, 1], rounded 6, diagonal exactly 1.0
    (also for zero vectors). [] -> []."""
    n = len(vectors)
    if n == 0:
        return []
    norms = [math.sqrt(sum(x * x for x in v)) for v in vectors]
    matrix: list[list[float]] = []
    for i in range(n):
        row: list[float] = []
        for j in range(n):
            if i == j:
                row.append(1.0)
                continue
            if norms[i] == 0.0 or norms[j] == 0.0:
                row.append(0.0)
                continue
            dot = sum(a * b for a, b in zip(vectors[i], vectors[j], strict=False))
            value = dot / (norms[i] * norms[j])
            row.append(round(max(-1.0, min(1.0, value)), 6))
        matrix.append(row)
    return matrix
