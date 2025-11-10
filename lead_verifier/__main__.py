"""Package entry point for ``python -m lead_verifier``."""
from __future__ import annotations

import sys

from . import cli


def main(argv: list[str] | None = None) -> int:
    """Invoke the orchestrator CLI with helpful defaults for developers."""

    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        parser = cli.build_parser(prog="python -m lead_verifier")
        parser.print_help()
        return 2

    return cli.main(argv)


if __name__ == "__main__":  # pragma: no cover - module entry point
    sys.exit(main())
