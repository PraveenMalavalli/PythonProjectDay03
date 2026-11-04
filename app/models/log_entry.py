from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime
    level: str
    module: str
    message: str


@dataclass(frozen=True, slots=True)
class ErrorCount:
    message: str
    count: int


@dataclass(frozen=True, slots=True)
class TimeRange:
    start: str | None
    end: str | None


@dataclass(frozen=True, slots=True)
class LogSummary:
    total_lines: int
    valid_lines: int
    bad_lines: int
    counts_by_level: dict[str, int]
    top_errors: list[ErrorCount]
    time_range: TimeRange
    bad_line_numbers: list[int]
