"""Unit tests for rag_worker.viz.similarity.cosine_matrix: pure function, exact matrices, zero-vector
diagonal, symmetry, bounds and opposite vectors."""

from rag_worker.viz.similarity import cosine_matrix


def test_empty_vectors_return_empty() -> None:
    assert cosine_matrix([]) == []


def test_exact_matrix_three_vectors() -> None:
    assert cosine_matrix([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]) == [
        [1.0, 0.0, 0.707107],
        [0.0, 1.0, 0.707107],
        [0.707107, 0.707107, 1.0],
    ]


def test_zero_vector_row_diagonal_one_off_diagonal_zero() -> None:
    m = cosine_matrix([[0.0, 0.0], [1.0, 2.0]])
    assert m == [[1.0, 0.0], [0.0, 1.0]]
    assert m[0][0] == 1.0
    assert m[0][1] == 0.0
    assert m[1][0] == 0.0


def test_symmetric_bounded_and_opposite_vectors_minus_one() -> None:
    m = cosine_matrix([[1.0, 2.0], [3.0, -1.0], [-2.0, -4.0]])
    assert m == [
        [1.0, 0.141421, -1.0],
        [0.141421, 1.0, -0.141421],
        [-1.0, -0.141421, 1.0],
    ]
    assert m == [list(row) for row in zip(*m, strict=False)]
    assert all(-1.0 <= v <= 1.0 for row in m for v in row)
    assert m[0][2] == -1.0
    assert m[2][0] == -1.0
