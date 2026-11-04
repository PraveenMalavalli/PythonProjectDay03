
import json
from datetime import datetime

import pytest

from app.exception.log_exceptions import InvalidLogLineError
from app.main import main
from app.services.log_analyser import analyse_lines, parse_log_line


# Test 1: Valid log line
def test_valid_log_line():
    line = "2026-03-02T08:02:24 ERROR billing payment gateway timeout"

    result = parse_log_line(line)

    assert result.timestamp == datetime(2026, 3, 2, 8, 2, 24)
    assert result.level == "ERROR"
    assert result.module == "billing"
    assert result.message == "payment gateway timeout"


# Test 2: All supported log levels
@pytest.mark.parametrize(
    "level",
    ["DEBUG", "INFO", "WARNING", "ERROR"],
)
def test_valid_log_levels(level):
    line = f"2026-03-02T08:02:24 {level} billing test message"

    result = parse_log_line(line)

    assert result.level == level


# Test 3: Invalid log level
def test_invalid_log_level():
    line = "2026-03-02T08:02:24 LOUD billing test message"

    with pytest.raises(InvalidLogLineError):
        parse_log_line(line)


# Test 4: Missing fields
@pytest.mark.parametrize(
    "line",
    [
        "",
        "2026-03-02T08:02:24 ERROR",
        "2026-03-02T08:02:24 ERROR billing",
    ],
)
def test_missing_fields(line):
    with pytest.raises(InvalidLogLineError):
        parse_log_line(line)


# Test 5: Invalid timestamp
@pytest.mark.parametrize(
    "timestamp",
    [
        "invalid-date",
        "2026-02-30T08:02:24",
        "2026-03-02",
    ],
)
def test_invalid_timestamp(timestamp):
    line = f"{timestamp} ERROR billing failed"

    with pytest.raises(InvalidLogLineError):
        parse_log_line(line)


# Test 6: Count logs by level
def test_level_counts():
    lines = [
        "2026-03-02T08:00:00 INFO api started",
        "2026-03-02T08:01:00 ERROR db connection failed",
        "2026-03-02T08:02:00 INFO api request completed",
        "2026-03-02T08:03:00 WARNING api slow response",
    ]

    result = analyse_lines(lines)

    assert result.total_lines == 4
    assert result.valid_lines == 4
    assert result.bad_lines == 0

    assert result.counts_by_level["INFO"] == 2
    assert result.counts_by_level["ERROR"] == 1
    assert result.counts_by_level["WARNING"] == 1
    assert result.counts_by_level["DEBUG"] == 0


# Test 7: Count bad lines without crashing
def test_bad_lines():
    lines = [
        "2026-03-02T08:00:00 INFO api started",
        "invalid log line",
        "2026-03-02T08:01:00 ERROR db failed",
        "",
    ]

    result = analyse_lines(lines)

    assert result.total_lines == 4
    assert result.valid_lines == 2
    assert result.bad_lines == 2
    assert result.bad_line_numbers == [2, 4]


# Test 8: Most frequent errors
def test_top_errors():
    lines = [
        "2026-03-02T08:00:00 ERROR db connection failed",
        "2026-03-02T08:01:00 ERROR api timeout",
        "2026-03-02T08:02:00 ERROR db connection failed",
        "2026-03-02T08:03:00 ERROR db connection failed",
    ]

    result = analyse_lines(lines, top_n=2)

    assert len(result.top_errors) == 2
    assert result.top_errors[0].message == "connection failed"
    assert result.top_errors[0].count == 3
    assert result.top_errors[1].message == "timeout"
    assert result.top_errors[1].count == 1


# Test 9: Earliest and latest timestamps
def test_time_range():
    lines = [
        "2026-03-02T12:00:00 INFO api noon event",
        "2026-03-02T08:00:00 INFO api morning event",
        "2026-03-02T16:00:00 ERROR db evening event",
    ]

    result = analyse_lines(lines)

    assert result.time_range.start == "2026-03-02T08:00:00"
    assert result.time_range.end == "2026-03-02T16:00:00"


# Test 10: Empty log
def test_empty_log():
    result = analyse_lines([])

    assert result.total_lines == 0
    assert result.valid_lines == 0
    assert result.bad_lines == 0
    assert result.top_errors == []
    assert result.time_range.start is None
    assert result.time_range.end is None


# Test 11: Unicode log message
def test_unicode_message():
    line = "2026-03-02T08:00:00 ERROR api café payment failed"

    result = parse_log_line(line)

    assert result.message == "café payment failed"


# Test 12: Very long log line
def test_very_long_line():
    message = "A" * 100000
    line = f"2026-03-02T08:00:00 ERROR api {message}"

    result = analyse_lines([line])

    assert result.total_lines == 1
    assert result.valid_lines == 1
    assert result.bad_lines == 0
    assert result.top_errors[0].message == message


# Test 13: Invalid top N
def test_invalid_top_n():
    with pytest.raises(ValueError, match="positive integer"):
        analyse_lines([], top_n=0)


# Test 14: CLI creates valid JSON
def test_cli_json_output(tmp_path):
    log_file = tmp_path / "sample.log"
    output_file = tmp_path / "summary.json"

    log_file.write_text(
        "2026-03-02T08:00:00 ERROR api timeout\n"
        "2026-03-02T08:01:00 INFO api started\n",
        encoding="utf-8",
    )

    exit_code = main([
        "-r", str(log_file),
        "-t", "3",
        "-o", str(output_file),
    ])

    assert exit_code == 0
    assert output_file.exists()

    data = json.loads(output_file.read_text(encoding="utf-8"))

    assert data["total_lines"] == 2
    assert data["bad_lines"] == 0
    assert data["counts_by_level"]["ERROR"] == 1
    assert data["counts_by_level"]["INFO"] == 1


# Test 15: Missing input file
def test_missing_file(tmp_path, caplog):
    missing_file = tmp_path / "missing.log"
    output_file = tmp_path / "summary.json"

    exit_code = main([
        "-r", str(missing_file),
        "-o", str(output_file),
    ])

    assert exit_code == 1
    assert "not found" in caplog.text.lower()
    assert not output_file.exists()


# Test 16: CLI rejects invalid top N
def test_cli_invalid_top():
    with pytest.raises(SystemExit) as error:
        main(["-r", "messy.log", "-t", "0"])

    assert error.value.code == 2
