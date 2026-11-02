import numpy as np
from sklearn.decomposition import PCA
from umap import UMAP


def pca(vectors: list[list[float]], k: int) -> tuple[list[list[float]] | None, list[float]]:
    """sklearn PCA(n_components=k, random_state=42) -> (coords rounded 6, explained_variance_ratio_
    rounded 6). len(vectors) < k -> (None, []). All-identical vectors -> coords all 0.0 and
    explained variance [] (no exception)."""
    n = len(vectors)
    if n < k:
        return None, []
    data = np.asarray(vectors, dtype=float)
    model = PCA(n_components=k, random_state=42).fit(data)
    if model.explained_variance_.sum() == 0.0:
        return [[0.0] * k for _ in range(n)], []
    reduced = model.transform(data)
    return (
        [[round(float(v), 6) for v in row] for row in reduced],
        [round(float(r), 6) for r in model.explained_variance_ratio_],
    )


def umap_project(vectors: list[list[float]], k: int) -> list[list[float]] | None:
    """umap.UMAP(n_components=k, n_neighbors=min(15, n-1), random_state=42, metric='cosine')
    .fit_transform -> rounded 6. n < 5 -> None."""
    n = len(vectors)
    if n < 5:
        return None
    points = UMAP(
        n_components=k,
        n_neighbors=min(15, n - 1),
        random_state=42,
        metric="cosine",
    ).fit_transform(np.asarray(vectors, dtype=float))
    return [[round(float(v), 6) for v in row] for row in points]
