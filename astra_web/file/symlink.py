import os


def find_symlinks(
    target_file: str, root_dir: str, link_name: str | None = None
) -> list[str]:
    """
    Finds all symlinks that point to a specific target file within a given root directory.

    :param link_name: If provided, only symlinks with this name will be considered.

    Returns a list of symlinks that point to the target file within the specified root directory.
    """

    target_realpath = os.path.realpath(target_file)
    matching_symlinks: list[str] = []

    def is_link_to_target(full_path: str) -> bool:
        if not os.path.islink(full_path):
            return False
        try:
            link_target = os.path.realpath(full_path)
            return link_target == target_realpath
        except OSError:
            return False  # skip broken/inaccessible symlinks

    if link_name is None:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                if is_link_to_target(full_path):
                    matching_symlinks.append(full_path)
    else:
        for dirpath, _, filenames in os.walk(root_dir):
            if link_name in filenames:
                full_path = os.path.join(dirpath, link_name)
                if is_link_to_target(full_path):
                    matching_symlinks.append(full_path)

    return matching_symlinks
