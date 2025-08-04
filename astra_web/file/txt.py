import os


def write(
    content: str,
    path: str,
    ensure_parent_dir_exists: bool = False,
) -> None:
    """
    Writes a string to a file.
    """

    if ensure_parent_dir_exists:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as file:
        file.write(content)


def read(path: str) -> str:
    """
    Reads a string file and returns its content.
    """

    with open(path, "r") as file:
        return file.read()
