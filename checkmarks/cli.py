"""Argparse-based CLI entry-point for *checkmarks*."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import NoReturn

from checkmarks.core import (
    ChecklistManager,
    parse_markdown_tasks,
    parse_markdown_title,
    build_stats,
)

__all__ = ["main"]


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

_BAR_WIDTH = 20


def _ascii_bar(completed: int, total: int) -> str:
    """Return a simple ASCII progress bar like ``[####------] 40%``."""
    if total == 0:
        return "[{}] n/a".format("-" * _BAR_WIDTH)
    ratio = completed / total
    filled = math.floor(ratio * _BAR_WIDTH)
    bar = "#" * filled + "-" * (_BAR_WIDTH - filled)
    return f"[{bar}] {ratio * 100:5.1f}%"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="checkmarks", description="Track progress in markdown checklists."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config JSON (defaults to ~/.checkmarks_config.json)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = subparsers.add_parser("add", help="Add a markdown file to tracking list")
    p_add.add_argument("file", help="Markdown file to add")

    # remove
    p_rm = subparsers.add_parser(
        "remove", help="Remove a markdown file from tracking list"
    )
    p_rm.add_argument("file", help="Markdown file to remove")

    # list
    subparsers.add_parser("list", help="List tracked markdown files")

    # parse
    p_parse = subparsers.add_parser(
        "parse", help="Parse a markdown file and show progress"
    )
    p_parse.add_argument("file", help="Markdown file to parse")

    # dashboard
    subparsers.add_parser(
        "dashboard", help="Show summary dashboard for all tracked files"
    )
    return parser


def cmd_parse(file: Path) -> None:
    title = parse_markdown_title(file)
    completed, total = parse_markdown_tasks(file)
    print(f"{title}")  # noqa: T201
    print(_ascii_bar(completed, total))  # noqa: T201


def cmd_dashboard(mgr: ChecklistManager) -> None:
    stats = mgr.stats()
    if not stats:
        print(
            "No files tracked yet. Use 'checkmarks add <file.md>' first."
        )  # noqa: T201
        return

    # find longest title width
    max_title = max(len(s.title) for s in stats)
    for s in stats:
        bar = _ascii_bar(s.completed, s.total)
        print(f"{s.title.ljust(max_title)}  {bar}")  # noqa: T201


def main(argv: list[str] | None = None) -> NoReturn:  # noqa: D401
    """CLI dispatch."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    mgr = ChecklistManager(config_path=args.config)

    if args.command == "add":
        mgr.add(args.file)

    elif args.command == "remove":
        mgr.remove(args.file)

    elif args.command == "list":
        for p in mgr.list_paths():
            print(p)  # noqa: T201

    elif args.command == "parse":
        cmd_parse(Path(args.file))

    elif args.command == "dashboard":
        cmd_dashboard(mgr)

    else:  # pragma: no cover
        parser.error("Unhandled command: %s" % args.command)
