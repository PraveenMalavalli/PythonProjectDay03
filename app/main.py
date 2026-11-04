
import argparse
import json
import logging
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from app.services.log_analyser import analyse_lines

logger = logging.getLogger(__name__)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize application log levels and errors"
    )

    parser.add_argument(
        "-r", "--read",
        required=True,
        metavar="FILE",
        help="Input .log file",
    )

    parser.add_argument(
        "-o", "--output",
        default="summary.json",
        metavar="JSON",
        help="Output JSON file",
    )

    parser.add_argument(
        "-t", "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top errors",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    parser = make_parser()
    args = parser.parse_args(argv)

    if args.top < 1:
        parser.error("--top must be greater than zero")

    try:
        with Path(args.read).open("r", encoding="utf-8") as log_file:
            summary = analyse_lines(log_file, args.top)

    except FileNotFoundError:
        logger.error("Input log file not found: %s", args.read)
        return 1

    except (OSError, UnicodeError) as error:
        logger.error("Could not read input log: %s", error)
        return 1

    try:
        Path(args.output).write_text(
            json.dumps(
                asdict(summary),
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

    except OSError as error:
        logger.error("Could not write JSON output: %s", error)
        return 1

    logger.info(
        "Analysed %d lines (%d invalid); wrote %s",
        summary.total_lines,
        summary.bad_lines,
        args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
