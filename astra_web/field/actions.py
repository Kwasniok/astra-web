import os
from astra_web.actor import Actor
from astra_web.field.schemas.field_table import FieldTable
from astra_web.file import find_symlinks


def write_field_table(file_name: str, table: FieldTable, actor: Actor):
    """
    Write the field table to disk.
    """
    os.makedirs(actor.field_path(), exist_ok=True)
    path = actor.field_path(file_name)
    if os.path.exists(path):
        raise FileExistsError(f"Field table '{file_name}' already exists.")
    table.write_to_csv(path)


def read_field_table(file_name: str, actor: Actor) -> FieldTable:
    """
    Read the field table from disk.
    """
    path = actor.field_path(file_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Field table '{file_name}' does not exist.")
    return FieldTable.read_from_csv(path)


def delete_field_table(
    file_name: str,
    actor: Actor,
    force: bool = False,
) -> list[str]:
    """
    Deletes the field table from disk.

    Returns a list of symlinks that are referencing to the field file and blocking the deletion when not forced. Otherwise, returns None.
    """
    path = actor.field_path(file_name)
    if not os.path.exists(path):
        return []

    if not force:
        # delete only when nothing is referencing it
        links = find_symlinks(
            path,
            actor.data_path(),
            link_name=file_name,
        )
        if len(links) > 0:
            return links
        # now it's safe to remove

    os.remove(path)
    return []


def list_field_table_file_names(actor: Actor) -> list[str]:
    """
    List all field table file names in the actor's field path.
    """
    field_path = actor.field_path()
    if not os.path.exists(field_path):
        return []

    return [
        f for f in os.listdir(field_path) if os.path.isfile(os.path.join(field_path, f))
    ]
