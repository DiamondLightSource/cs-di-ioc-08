"""Interface for ``python -m ebpm_postmortem``."""

import os
from argparse import ArgumentParser
from collections.abc import Sequence

from . import __version__
from .bpm_pm import start_server

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
    parser = ArgumentParser()
    parser.add_argument("-d", dest="debug", action="store_true")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    parser.add_argument(
        "--pmdir",
        default=None,
        help="Directory for postmortem files",
    )
    parsed_args = parser.parse_args(args)

    if parsed_args.debug:
        os.environ["EPICS_CAS_SERVER_PORT"] = "6064"
    if parsed_args.pmdir:
        pmdir = parsed_args.pmdir
    else:
        if parsed_args.debug:
            pmdir = "/tmp/BPM_postmortems"
        else:
            pmdir = "/dls/ops-data/Postmortems/BPM_postmortems"

    start_server(pmdir, parsed_args.debug)


if __name__ == "__main__":
    main()
