from typing import Any, Iterable

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots


def make_modules_plot(input: dict[str:Any], fields: dict[str:Any]) -> go.Figure:
    """
    Returns a plotly figure showing the longitudinal field profiles of the cavities and solenoids.

    Arguments:
    input: dict
        The input dictionary containing the cavity and solenoid definitions.
    fields: dict
        A dictionary mapping field file names to their longitudinal amplitudes.
    """

    fig = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])

    # add cavities
    for c in input["cavities"]:
        field = pd.DataFrame(fields[c["field_file_name"]])
        z = field["z"] + c["z"]
        e = field["v"] * c["max_field_strength"] / field["v"].abs().max()
        fig.add_scatter(
            x=z,
            y=e,
            secondary_y=False,
            mode="lines",
            name=f'{c["comment"]} @ {c["frequency"]} GHz, phi={c["phase"]}°',
        )
        fig.add_vline(x=c["z"], line_width=0.5, line_dash="solid", line_color="gray")
        if c["z"] != 0.0:
            fig.add_annotation(
                text=str(c["z"]),
                x=c["z"],
                y=1,
                xref="x",
                yref="paper",
                textangle=-45,
            )
    # add solenoids
    for s in input["solenoids"]:
        field = pd.DataFrame(fields[s["field_file_name"]])
        z = field["z"] + s["z"]
        b = field["v"] * s["max_field_strength"] / field["v"].abs().max()
        fig.add_scatter(
            x=z,
            y=b,
            secondary_y=True,
            mode="lines",
            name=s["comment"],
        )
        fig.add_vline(x=s["z"], line_width=0.5, line_dash="solid", line_color="gray")
        if s["z"] != 0.0:
            fig.add_annotation(
                text=str(s["z"]),
                x=s["z"],
                y=1,
                xref="x",
                yref="paper",
                textangle=-45,
            )

    fig.update_layout(
        title="Longitudinal Field Amplitudes",
        xaxis_title="z [m]",
    )
    fig.update_yaxes(title="E [MV/m] ", secondary_y=False)
    fig.update_yaxes(title="B [T]", secondary_y=True)
    fig.update_xaxes(range=[0, None])

    return fig
