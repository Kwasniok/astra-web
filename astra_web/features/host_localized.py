import re
from typing import Any, Callable, Iterable, cast

from pydantic import BaseModel

from astra_web._aux import get_filter_subtree
from astra_web.file.json import JSONType
from astra_web.generator.host_localized import load_generator_data
from astra_web.host_localizer import HostLocalizer
from astra_web.simulation.host_localized import (
    get_generator_id,
    get_simulation_comment,
    get_simulation_status,
    list_simulation_ids,
    load_simulation_data,
)
from astra_web.status import DispatchStatus

from .schemas.io import Features, FeatureTable, FeatureTableInput


def make_feature_table(
    sim_ids: list[str] | None,
    features: FeatureTableInput,
    localizer: HostLocalizer,
    *,
    filter_by_comment: str | None = None,
) -> FeatureTable:
    """
    Returns a table according to the selected features.

    note: Queries finished simulations only!

    :param features: List of features to include in the table. See `CompleteData` for available features.
    :param sim_ids: Optional list of simulation IDs to restrict the query to. If `None`, all finished simulations are included.
    :param filter_by_comment: Optional substring to filter simulations by their comment field. Only simulations matching the regex are included. Syntax: Python regex.

    Raises:
        ValueError: If a feature is not found.
    """

    if sim_ids is None:
        sim_ids = list_simulation_ids(localizer, DispatchStatus.ANY)

    feature_table: dict[str, list[Any]] = {col: [] for col in features}
    feature_tree = _build_tree(features)
    comment_re = re.compile(filter_by_comment) if filter_by_comment else None

    def append_row(data: Features) -> None:
        for path, value in _traverse(data, feature_tree):
            feature_table[path].append(value)

    for sim_id in sim_ids:
        if get_simulation_status(sim_id, localizer) != DispatchStatus.FINISHED:
            # skip unfinished simulations
            continue
        if comment_re and not comment_re.search(
            get_simulation_comment(sim_id, localizer)
        ):
            # skip non-matching comments
            continue
        append_row(
            get_features(
                sim_id,
                localizer,
                include=features,
            )
        )

    return feature_table


def get_features(
    sim_id: str,
    localizer: HostLocalizer,
    include: list[str] | None = None,
) -> Features:
    """
    Returns all features of a simulation.

    note: Finished simulations only!

    Parameters:
        include: Optional list of feature paths to include - all others are excluded. If `None`, all features are included.
        Used for optimization: Do not load features that are not requested anyway.
            Example: `["simulation.input.cavities", "generator.output"]`

    Raises:
        ValueError: If simulation is not found or incomplete.
    """

    # for loading optimization: filter includes by category
    include_sim = get_filter_subtree(include, "simulation")
    include_gen = get_filter_subtree(include, "generator")

    if include_sim == []:
        # explicitly nothing to include -> skip loading any simulation data
        sim = None
        gen_id = get_generator_id(sim_id, localizer)  # raises ValueError
    else:
        sim = load_simulation_data(sim_id, localizer, include_sim)
        if sim is None:
            raise ValueError(
                f"Simulation with ID {sim_id} not found or is not finished yet."
            )
        gen_id = sim.input.run.generator_id

    if include_gen == []:
        # explicitly nothing to include -> skip loading any generator data
        gen = None
    else:
        gen = load_generator_data(gen_id, localizer, include_gen)
        if gen is None:
            raise ValueError(f"Generator with ID {gen_id} not found.")

    return Features(
        sim_id=sim_id,
        generator=gen,
        simulation=sim,
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

    for sim_id in list_simulation_ids(localizer, DispatchStatus.FINISHED):
        if sim_ids is not None and sim_id not in sim_ids:
            # skip excluded simulations
            continue
        result.append(get_features(sim_id, localizer).model_dump(mode="json"))

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
