import logging
import re
from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from typing import Literal, cast

from app.exception.log_exceptions import InvalidLogLineError
from app.models.log_entry import (
    ErrorCount,
    LogEntry,
    LogSummary,
    TimeRange,
)

logger = logging.getLogger(__name__)

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)


LEVELS: tuple[LogLevel, ...] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
)


def validate_level(level: str) -> LogLevel:
    if level not in LEVELS:
        raise ValueError(f"Invalid log level: {level}")

    return cast(LogLevel, level)


def parse_log_line(line: str) -> LogEntry:
    parts = line.strip().split(maxsplit=3)

    if len(parts) != 4:
        raise InvalidLogLineError(
            "expected TIMESTAMP LEVEL MODULE MESSAGE"
        )

    raw_timestamp, level, module, message = parts

    if TIMESTAMP_PATTERN.fullmatch(raw_timestamp) is None:
        raise InvalidLogLineError("invalid timestamp format")

    try:
        timestamp = datetime.fromisoformat(raw_timestamp)
    except ValueError as error:
        raise InvalidLogLineError(
            "invalid timestamp value"
        ) from error

    if level not in LEVELS:
        raise InvalidLogLineError(
            f"unsupported level: {level}"
        )

    return LogEntry(
        timestamp=timestamp,
        level=level,
        module=module,
        message=message,
    )


def analyse_lines(
    lines: Iterable[str],
    top_n: int = 5,
) -> LogSummary:

    if top_n < 1:
        raise ValueError("top_n must be a positive integer")

    counts: dict[str, int] = dict.fromkeys(LEVELS, 0)
    errors: Counter[str] = Counter()

    first: datetime | None = None
    last: datetime | None = None

    total_lines = 0
    bad_line_numbers: list[int] = []

    for line_number, line in enumerate(lines, start=1):
        total_lines += 1

        try:
            entry = parse_log_line(line)

        except InvalidLogLineError as error:
            bad_line_numbers.append(line_number)

            logger.warning(
                "Skipping invalid line %d: %s",
                line_number,
                error,
            )
            continue

        counts[entry.level] += 1

        if entry.level == "ERROR":
            errors[entry.message] += 1

        if first is None or entry.timestamp < first:
            first = entry.timestamp

        if last is None or entry.timestamp > last:
            last = entry.timestamp

    ranked_errors = sorted(
        errors.items(),
        key=lambda item: (-item[1], item[0]),
    )

    top_errors = [
        ErrorCount(message=msg, count=count)
        for msg, count in ranked_errors[:top_n]
    ]

    return LogSummary(
        total_lines=total_lines,
        valid_lines=total_lines - len(bad_line_numbers),
        bad_lines=len(bad_line_numbers),
        counts_by_level=counts,
        top_errors=top_errors,
        time_range=TimeRange(
            start=first.isoformat() if first is not None else None,
            end=last.isoformat() if last is not None else None,
        ),
        bad_line_numbers=bad_line_numbers,
    )
