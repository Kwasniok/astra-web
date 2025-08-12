from typing import Any, Iterable, Callable, cast
from pydantic import BaseModel
from astra_web.host_localizer import HostLocalizer
from .schemas.io import FeatureTableInput, FeatureTable, CompleteData
from astra_web.generator.host_localized import load_generator_data
from astra_web.simulation.host_localized import (
    list_simulation_ids,
    load_simulation_data,
)
from astra_web.choices import ListDispatchedCategory
from astra_web.file.json import JSONType


def make_feature_table(
    sim_ids: list[str] | None,
    features: FeatureTableInput,
    localizer: HostLocalizer,
) -> FeatureTable:
    """
    Returns a table according to the selected features.

    note: Queries finished simulations only!

    :param features: List of features to include in the table. See `CompleteData` for available features.
    :param sim_ids: Optional list of simulation IDs to restrict the query to. If `None`, all finished simulations are included.

    Raises:
        ValueError: If a feature is not found.
    """

    feature_table: dict[str, list[Any]] = {col: [] for col in features}
    feature_tree = _build_tree(features)

    def append_row(data: CompleteData) -> None:
        for path, value in _traverse(data, feature_tree):
            feature_table[path].append(value)

    for sim_id in list_simulation_ids(localizer, ListDispatchedCategory.FINISHED):
        if sim_ids is not None and sim_id not in sim_ids:
            # skip excluded simulations
            continue
        append_row(get_all_features(sim_id, localizer))

    return feature_table


def get_all_features(
    sim_id: str,
    localizer: HostLocalizer,
) -> CompleteData:
    """
    Returns all features of a simulation.

    note: Finished simulations only!

    Raises:
        ValueError: If simulation is not found or incomplete.
    """

    sim = load_simulation_data(sim_id, localizer)
    if sim is None or sim.data is None:
        raise ValueError(f"Simulation with ID {sim_id} not found or has no data.")
    gen_id = sim.web_input.run_specs.generator_id

    gen = load_generator_data(gen_id, localizer)
    if gen is None:
        raise ValueError(f"Generator with ID {gen_id} not found.")

    return CompleteData(
        sim_id=sim_id,
        generator_input=gen.web_input,
        simulation_input=sim.web_input,
        simulation_output=sim.data,
    )


def get_all_varying_features(
    sim_ids: list[str] | None,
    localizer: HostLocalizer,
) -> dict[str, list[JSONType]]:
    """
    Returns a dictionary of all varying features across for the specified simulations.

    :param sim_ids: Optional list of simulation IDs to restrict the query to. If `None`, all finished simulations are included.


    note: Queries finished simulations only!
    """

    result: list[JSONType] = []

    for sim_id in list_simulation_ids(localizer, ListDispatchedCategory.FINISHED):
        if sim_ids is not None and sim_id not in sim_ids:
            # skip excluded simulations
            continue
        result.append(get_all_features(sim_id, localizer).model_dump(mode="json"))

    return _deep_diff_dicts(result)


def _build_tree(paths: Iterable[str]) -> dict[str, Any]:
    """
    Builds a tree structure from a list of dot-separated paths.

    Example:
        ["a.b.c", "a.b.d", "a.e"]
        ->
        {
        "a":
            {
            "b":
                {
                "c": {},
                "d": {}
                },
            "e": {}
            }
        }
    """
    tree: dict[str, Any] = {}

    for path in paths:
        parts = path.split(".")
        current_level: dict[str, Any] = tree

        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    return tree


def _traverse(
    obj: BaseModel, tree: dict[str, Any], path: list[str] | None = None
) -> Iterable[tuple[str, Any]]:
    """
     Traverses the object and yields the paths to the attributes as given by the tree as well as their values.

    :param obj: The object to traverse.
    :param tree: The tree structure defining the attribute paths to traverse.

    Returns an iterable of pairs of the dot separated path and value.

    Raises ValueError if an attribute is not found in the object.
    """
    if path is None:
        path = []

    for key, subtree in tree.items():
        if key in obj.__class__.model_fields:
            attr = getattr(obj, key)
            current_path = path + [key]

            if subtree and isinstance(attr, BaseModel):
                yield from _traverse(attr, subtree, current_path)
            else:
                yield (".".join(current_path), attr)
        else:
            current_path = path + [key]
            quote: Callable[[str], str] = lambda x: f"`{x}`"
            raise ValueError(
                f"Feature `{'.'.join(current_path)}` not found. `{obj.__class__.__name__}` does not have field `{key}` but has fields {','.join(map(quote, obj.__class__.model_fields))}"
            )


def _deep_diff_dicts(
    dicts: list[JSONType], path: str = ""
) -> dict[str, list[JSONType]]:
    """
    Recursively diff a list of (nested) dictionaries.
    Returns a mapping: "path" -> list of values from each dict (in order).
    Only includes paths where not all values are equal.
    """

    differences: dict[str, list[JSONType]] = {}

    # all dicts
    if all(isinstance(d, dict) for d in dicts):
        keys = {k for d in dicts if isinstance(d, dict) for k in d}
        for key in keys:
            new_values = [(d.get(key) if isinstance(d, dict) else None) for d in dicts]
            if all(isinstance(v, dict) for v in new_values if v is not None):
                differences.update(
                    _deep_diff_dicts(new_values, f"{path}.{key}" if path else key)
                )
            elif all(isinstance(v, list) for v in new_values if v is not None):
                differences.update(
                    _deep_diff_dicts(new_values, f"{path}.{key}" if path else key)
                )
            elif not all(v == new_values[0] for v in new_values):
                differences[f"{path}.{key}" if path else key] = new_values

    # all lists
    elif all(isinstance(d, list) for d in dicts):
        ds = cast(list[list[JSONType]], dicts)
        max_len = max(len(d) for d in ds)
        for i in range(max_len):
            new_values = [(d[i] if i < len(d) else None) for d in ds]
            if all(isinstance(v, dict) for v in new_values if v is not None):
                differences.update(_deep_diff_dicts(new_values, f"{path}[{i}]"))
            elif all(isinstance(v, list) for v in new_values if v is not None):
                differences.update(_deep_diff_dicts(new_values, f"{path}[{i}]"))
            elif not all(v == new_values[0] for v in new_values):
                differences[f"{path}[{i}]"] = new_values

    # otherwise: compare directly
    else:
        if not all(v == dicts[0] for v in dicts):
            differences[path] = dicts

    return differences
