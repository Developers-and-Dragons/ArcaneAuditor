"""
Shared console output for CLI: three channels (status/info, warnings/errors, results).

- info/success: operational chatter; suppressed when quiet.
- warn/error: always go to stderr; visible even when quiet.
- result: the requested findings payload; always printed to stdout (not suppressed by quiet).

Call set_quiet(True) from the CLI entrypoint (e.g. main.review_app) before running
pipeline code so parser/rules_engine and rules use the same setting.
"""

import typer

_quiet: bool = False


def set_quiet(quiet: bool) -> None:
    """Set whether status/info output is suppressed (e.g. for --quiet / --ci)."""
    global _quiet
    _quiet = quiet


def get_quiet() -> bool:
    """Return current quiet setting."""
    return _quiet


def info(msg: str) -> None:
    """Status/info message (stdout). Suppressed when quiet."""
    if not _quiet:
        typer.echo(msg)


def success(msg: str) -> None:
    """Success message (stdout). Treated like info; suppressed when quiet."""
    if not _quiet:
        typer.echo(msg)


def warn(msg: str) -> None:
    """Warning message (stderr). Always shown, including when quiet."""
    typer.secho(msg, fg=typer.colors.YELLOW, err=True)


def error(msg: str) -> None:
    """Error message (stderr). Always shown, including when quiet."""
    typer.secho(msg, fg=typer.colors.RED, err=True)


def result(msg: str) -> None:
    """Results payload (stdout). Not suppressed by quiet; use for findings output."""
    typer.echo(msg)
