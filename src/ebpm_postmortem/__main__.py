"""Interface for ``python -m ebpm_postmortem``."""

from argparse import ArgumentParser
from collections.abc import Sequence

from . import __version__
from .bpm_pm import start_server

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
    parser = ArgumentParser()
    # Accept "-D" flag (ignored by the app)
    parser.add_argument("-D", dest="debug", action="store_true")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    parser.parse_args(args)

    start_server()


if __name__ == "__main__":
    main()
