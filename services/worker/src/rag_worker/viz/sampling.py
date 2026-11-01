def sample_indices(n: int, cap: int = 200) -> list[int]:
    """Evenly spaced indices: [round(x) for x in numpy.linspace(0, n-1, min(n, cap))] as ints,
    strictly increasing and unique. n = 0 -> []; n <= cap -> list(range(n))."""
    raise NotImplementedError("not implemented")
