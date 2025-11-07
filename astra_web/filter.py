def get_filter_subtree(filter: list[str] | None, prefix: str) -> list[str] | None:
    """
    Filters the include list to only include paths that start with the given prefix and removes the prefix from the returned paths.

    Example:
        filter = ["simulation.input.run", "simulation.output", "generator.input"]
        prefix = "simulation"
        returns ["input.run", "output"]
    """
    if filter is None:
        return None

    def remove_leading_dot(s: str) -> str:
        return s[1:] if s.startswith(".") else s

    fs = (f[len(prefix) + 1 :] for f in filter if f.startswith(prefix))
    return list(map(remove_leading_dot, fs))


def filter_has_prefix(filter: list[str] | None, prefix: str) -> bool:
    """
    Checks if any path in the include list starts with the given prefix.
    Returns True if include is None.

    Example:
        filter = ["simulation.input.run", "simulation.output", "generator.input"]
        prefix = "simulation"
        returns True
    """
    if filter is None:
        return True

    return any(f.startswith(prefix) for f in filter)
