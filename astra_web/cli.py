import argparse
from astra_web.actor import LocalActor
from astra_web.dtypes import FloatPrecision
from astra_web.simulation.actions import (
    compress_simulation,
    uncompress_simulation,
)


def strictly_positive_float(value):
    """Type checker for positive floats."""
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid float")
    if f <= 0:
        raise argparse.ArgumentTypeError(f"{value!r} is not a strictly positive float")
    return f


def main():
    parser = argparse.ArgumentParser(
        description="command line interface of astra-web",
    )

    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    compress_sim = commands.add_parser(
        "compress-sim",
        help="compress simulation data",
    )
    compress_sim.add_argument(
        "--sim-id",
        type=str,
        required=True,
        help="simulation ID",
    )
    compress_sim.add_argument(
        "--precision",
        type=str,
        choices=list(map(lambda x: x.value, FloatPrecision)),
        default=FloatPrecision.FLOAT64.value,
        help="floating point precision of compressed data. default: float64",
    )
    compress_sim.add_argument(
        "--max-rel-err",
        type=strictly_positive_float,
        default=1e-4,
        help="maximum relative error per element. default: 1e-4",
    )

    uncompress_sim = commands.add_parser(
        "uncompress-sim",
        help="uncompress simulation data",
    )
    uncompress_sim.add_argument(
        "--sim-id",
        type=str,
        required=True,
        help="simulation ID",
    )
    uncompress_sim.add_argument(
        "--precision",
        type=str,
        choices=["low", "high"],
        default="high",
        help="ASTRA ASCII precision level: low = 1P,8E12.4,2I4, high = 1P,8E20.12,2I4. default: high",
    )

    args = parser.parse_args()

    actor = LocalActor.instance()

    if args.command == "compress-sim":
        compress_simulation(
            sim_id=args.sim_id,
            actor=actor,
            precision=FloatPrecision.select(args.precision),
            max_rel_err=args.max_rel_err,
        )
    elif args.command == "uncompress-sim":
        uncompress_simulation(
            sim_id=args.sim_id,
            actor=actor,
            high_precision=args.precision == "high",
        )
