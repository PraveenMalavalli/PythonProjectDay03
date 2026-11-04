


class LogAnalysisError(Exception):
    """Base exception for log analysis errors."""


class InvalidLogLineError(LogAnalysisError, ValueError):
    """Raised when a log line is invalid."""
