"""Unit tests for rag_worker.viz.projection: pca / umap_project — seeded numpy inputs, assert exact
shapes, determinism and edge behaviour; edge cases must not raise."""

import numpy as np

from rag_worker.viz.projection import pca, umap_project


def test_pca_returns_k_rows_and_explained_variance() -> None:
    vectors = np.random.default_rng(0).normal(size=(10, 8)).tolist()
    coords, evr = pca(vectors, 2)
    assert coords is not None
    assert len(coords) == 10
    assert all(len(row) == 2 for row in coords)
    assert all(isinstance(v, float) for row in coords for v in row)
    assert len(evr) == 2
    assert all(0.0 <= v <= 1.0 for v in evr)
    assert sum(evr) <= 1.0


def test_pca_deterministic_on_same_input() -> None:
    vectors = np.random.default_rng(0).normal(size=(10, 8)).tolist()
    assert pca(vectors, 2) == pca(vectors, 2)


def test_pca_too_few_vectors_returns_none() -> None:
    assert pca([[0.5, -1.5, 2.5]], 2) == (None, [])


def test_pca_identical_vectors_zero_coords_no_exception() -> None:
    vectors = [[1.0, 2.0, 3.0]] * 5
    coords, evr = pca(vectors, 2)
    assert coords == [[0.0, 0.0]] * 5
    assert evr == []


def test_umap_none_below_five_and_projection_shape_deterministic() -> None:
    assert umap_project(np.random.default_rng(0).normal(size=(4, 3)).tolist(), 2) is None
    vectors = np.random.default_rng(0).normal(size=(12, 6)).tolist()
    points = umap_project(vectors, 3)
    assert points is not None
    assert umap_project(vectors, 3) == points
    assert len(points) == 12
    assert all(len(row) == 3 for row in points)
    assert all(isinstance(v, float) for row in points for v in row)
