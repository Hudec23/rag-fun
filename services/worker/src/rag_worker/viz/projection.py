def pca(vectors: list[list[float]], k: int) -> tuple[list[list[float]] | None, list[float]]:
    """sklearn PCA(n_components=k, random_state=42) -> (coords rounded 6, explained_variance_ratio_
    rounded 6). len(vectors) < k -> (None, []). All-identical vectors -> coords all 0.0 and
    explained variance [] (no exception)."""
    raise NotImplementedError("not implemented")


def umap_project(vectors: list[list[float]], k: int) -> list[list[float]] | None:
    """umap.UMAP(n_components=k, n_neighbors=min(15, n-1), random_state=42, metric='cosine')
    .fit_transform -> rounded 6. n < 5 -> None."""
    raise NotImplementedError("not implemented")
