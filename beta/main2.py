#!/usr/bin/env python3
"""
checkmarks - A tool to parse Markdown task lists and display progress.
"""

import argparse
import os
import re
import json
import sys
from typing import List, Tuple, NamedTuple

# If "rich" is installed, we can do fancy progress bars/tables.
# If not, we'll gracefully degrade to simple prints.
try:
    from rich.progress import Progress
    from rich.table import Table
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

CONFIG_FILENAME = os.path.expanduser("~/.checkmarks_config.json")


class MarkdownFileData(NamedTuple):
    """
    Holds all relevant parsed information about a Markdown file:
      - file_path: The absolute or relative file path
      - title: The first # heading found (or the file name if none)
      - completed: Number of completed tasks
      - total: Number of total tasks
    """

    file_path: str
    title: str
    completed: int
    total: int


def load_dashboard_config() -> List[str]:
    """
    Loads the list of tracked files from the global configuration file.
    If the config file doesn't exist or is invalid, returns an empty list.
    """
    if not os.path.isfile(CONFIG_FILENAME):
        return []
    with open(CONFIG_FILENAME, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data.get("tracked_files", [])
        except json.JSONDecodeError:
            return []


def save_dashboard_config(tracked_files: List[str]) -> None:
    """
    Saves the given list of file paths to the global configuration file.
    """
    data = {"tracked_files": tracked_files}
    with open(CONFIG_FILENAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_markdown_file(file_path: str) -> MarkdownFileData:
    """
    Parses a single Markdown file to extract:
      - The first top-level heading as title
      - The number of completed tasks [x]
      - The total number of tasks [ ] or [x]

    Args:
        file_path: Path to a Markdown file

    Returns:
        A MarkdownFileData NamedTuple with (file_path, title, completed, total).
        If the file doesn't exist, returns defaults with title=file name, completed=0, total=0.
    """
    if not os.path.isfile(file_path):
        # Default fallback if file doesn't exist
        return MarkdownFileData(
            file_path=file_path, title=os.path.basename(file_path), completed=0, total=0
        )

    title = os.path.basename(file_path)
    completed = 0
    total = 0

    task_pattern = re.compile(r"^(\s*)[-*]\s+\[([ xX])\]\s+", re.IGNORECASE)
    title_pattern = re.compile(r"^\s*#\s+(.+)$")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Check for the first heading (once only)
            title_match = title_pattern.match(line)
            if title_match and title == os.path.basename(file_path):
                title = title_match.group(1).strip()

            # Check for task lines
            task_match = task_pattern.match(line)
            if task_match:
                total += 1
                if task_match.group(2).lower() == "x":
                    completed += 1

    return MarkdownFileData(
        file_path=file_path, title=title, completed=completed, total=total
    )


def generate_dashboard_data(tracked_files: List[str]) -> List[MarkdownFileData]:
    """
    Given a list of file paths, parse each one and return a list
    of MarkdownFileData.

    Args:
        tracked_files: A list of markdown file paths

    Returns:
        A list of MarkdownFileData objects, one for each tracked file.
    """
    return [parse_markdown_file(fp) for fp in tracked_files]


def create_ascii_progress_bar(completed: int, total: int, width: int = 30) -> str:
    """
    Creates a simple ASCII progress bar string.

    Args:
        completed: Number of completed tasks
        total: Total tasks
        width: The displayed width of the bar in characters

    Returns:
        A string that represents the progress bar plus percentage.
    """
    if total == 0:
        return "No tasks"
    ratio = completed / total
    fill_length = int(ratio * width)
    bar = "#" * fill_length + "-" * (width - fill_length)
    return f"[{bar}] {ratio*100:.1f}%  ({completed}/{total})"


def print_simple_progress_bar(completed: int, total: int, width: int = 30) -> None:
    """
    Print a simple ASCII progress bar directly to stdout.
    Uses the helper create_ascii_progress_bar to build the string.
    """
    print(create_ascii_progress_bar(completed, total, width))


def cmd_parse_file(file_path: str) -> None:
    """
    Parse a single file for tasks and display title plus ASCII progress.
    """
    data = parse_markdown_file(file_path)
    print(f"File: {data.title}")
    print_simple_progress_bar(data.completed, data.total)


def cmd_add_file(file_path: str) -> None:
    """
    Add a single Markdown file to the dashboard config.
    """
    tracked_files = load_dashboard_config()
    if file_path not in tracked_files:
        tracked_files.append(file_path)
        save_dashboard_config(tracked_files)
        print(f"Added '{file_path}' to the dashboard.")
    else:
        print(f"'{file_path}' is already in the dashboard.")


def cmd_remove_file(file_path: str) -> None:
    """
    Remove a single Markdown file from the dashboard config.
    """
    tracked_files = load_dashboard_config()
    if file_path in tracked_files:
        tracked_files.remove(file_path)
        save_dashboard_config(tracked_files)
        print(f"Removed '{file_path}' from the dashboard.")
    else:
        print(f"'{file_path}' is not in the dashboard.")


def cmd_dashboard(use_table: bool = False, use_progress: bool = False) -> None:
    """
    Show the dashboard of tracked files. If Rich is installed and the user
    wants a table or progress view, display it that way. Otherwise,
    fall back to ASCII output.
    """
    tracked_files = load_dashboard_config()
    if not tracked_files:
        print("No files are being tracked yet. Use 'add' command to add files.")
        return

    dashboard_data = generate_dashboard_data(tracked_files)

    # Rich Table
    if RICH_AVAILABLE and use_table:
        print_dashboard_as_table(dashboard_data)
    # Rich Progress
    elif RICH_AVAILABLE and use_progress:
        print_dashboard_as_rich_progress(dashboard_data)
    else:
        # Fallback: text-based progress
        print("Tracked files:")
        for data in dashboard_data:
            print(f"- {data.title}")
            print_simple_progress_bar(data.completed, data.total)


def print_dashboard_as_table(dashboard_data: List[MarkdownFileData]) -> None:
    """
    Print the dashboard data as a Rich table (requires rich).
    """
    console = Console()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Title", justify="left")
    table.add_column("Completed", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Progress", justify="left")

    for data in dashboard_data:
        if data.total == 0:
            table.add_row(data.title, "0", "0", "No tasks")
        else:
            ratio = data.completed / data.total
            bar_length = 20
            fill_len = int(ratio * bar_length)
            bar = "#" * fill_len + "-" * (bar_length - fill_len)
            ratio_str = f"{ratio*100:.1f}%"
            table.add_row(
                data.title, str(data.completed), str(data.total), f"{bar} {ratio_str}"
            )

    console.print(table)


def print_dashboard_as_rich_progress(dashboard_data: List[MarkdownFileData]) -> None:
    """
    Print the dashboard data as animated Rich progress bars (requires rich).
    """
    console = Console()
    with Progress(console=console) as progress:
        for data in dashboard_data:
            if data.total == 0:
                task_id = progress.add_task(data.title, total=1)
                progress.update(task_id, completed=1)
            else:
                task_id = progress.add_task(data.title, total=data.total)
                progress.update(task_id, completed=data.completed)


def cmd_export_to_html(output_path: str) -> None:
    """
    Export the current dashboard to a standalone HTML file.
    """
    tracked_files = load_dashboard_config()
    if not tracked_files:
        print("No files are being tracked yet. Nothing to export.")
        return

    dashboard_data = generate_dashboard_data(tracked_files)

    lines = [
        "<html>",
        "<head><meta charset='utf-8'><title>Checkmarks Dashboard</title></head>",
        "<body>",
        "<h1>Checkmarks Dashboard</h1>",
        "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>",
        "<tr><th>Title</th><th>Completed</th><th>Total</th><th>Progress</th></tr>",
    ]

    for data in dashboard_data:
        if data.total == 0:
            progress_str = "No tasks"
        else:
            ratio = data.completed / data.total
            bar_length = 20
            fill_len = int(ratio * bar_length)
            bar = "#" * fill_len + "-" * (bar_length - fill_len)
            progress_str = f"{bar} {ratio*100:.1f}%"
        lines.append(
            f"<tr><td>{data.title}</td>"
            f"<td>{data.completed}</td><td>{data.total}</td><td>{progress_str}</td></tr>"
        )

    lines.append("</table></body></html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Dashboard exported to: {output_path}")


def cmd_scan_directory(directory: str) -> None:
    """
    Scan a directory (recursively) for Markdown files that contain tasks.
    If found, ask the user if they should be added to the dashboard.
    """
    if not os.path.isdir(directory):
        print(f"'{directory}' is not a directory.")
        return

    potential_files = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name.lower().endswith(".md"):
                file_path = os.path.join(root, name)
                data = parse_markdown_file(file_path)
                if data.total > 0:
                    potential_files.append(data)

    if not potential_files:
        print("No Markdown files with tasks found in that directory.")
        return

    tracked_files = load_dashboard_config()

    for data in potential_files:
        if data.file_path in tracked_files:
            print(f"Already tracked: {data.title} ({os.path.basename(data.file_path)})")
            continue

        print(
            f"Found: {data.title} ({data.completed}/{data.total} tasks). Add to dashboard? [y/n]"
        )
        choice = input("> ").strip().lower()
        if choice == "y":
            tracked_files.append(data.file_path)
            print(f"Added {data.title} to the dashboard.")
        else:
            print(f"Skipped {data.title}.")

    save_dashboard_config(tracked_files)


def main() -> None:
    """
    Main entry point: parse CLI arguments and dispatch to subcommands.
    """
    parser = argparse.ArgumentParser(
        description="checkmarks - Parse Markdown task lists and display progress."
    )
    subparsers = parser.add_subparsers(dest="command")

    # 'parse' subcommand
    parse_parser = subparsers.add_parser("parse", help="Parse a single Markdown file.")
    parse_parser.add_argument("file", type=str, help="Path to a Markdown file")

    # 'add' subcommand
    add_parser = subparsers.add_parser(
        "add", help="Add a Markdown file to the dashboard."
    )
    add_parser.add_argument("file", type=str, help="Path to a Markdown file")

    # 'remove' subcommand
    remove_parser = subparsers.add_parser(
        "remove", help="Remove a Markdown file from the dashboard."
    )
    remove_parser.add_argument("file", type=str, help="Path to a Markdown file")

    # 'dashboard' subcommand
    dash_parser = subparsers.add_parser("dashboard", help="Show the dashboard.")
    dash_parser.add_argument(
        "--table", action="store_true", help="Display as a Rich table (requires rich)."
    )
    dash_parser.add_argument(
        "--progress",
        action="store_true",
        help="Display as Rich progress bars (requires rich).",
    )

    # 'export' subcommand
    export_parser = subparsers.add_parser(
        "export", help="Export the dashboard to HTML."
    )
    export_parser.add_argument("output", type=str, help="Output HTML file path")

    # 'scan' subcommand
    scan_parser = subparsers.add_parser(
        "scan", help="Scan a directory for Markdown files."
    )
    scan_parser.add_argument("directory", type=str, help="Directory path")

    # ---------------------------------------------------------------------
    # Special cases for default behavior:
    #   1) No arguments => show the dashboard
    #   2) Single argument => if it’s a local .md file, parse it
    # ---------------------------------------------------------------------
    if len(sys.argv) == 1:
        cmd_dashboard()
        return

    if len(sys.argv) == 2:
        single_arg = sys.argv[1]
        if single_arg.lower().endswith(".md") and os.path.isfile(single_arg):
            cmd_parse_file(single_arg)
            return

    # Parse arguments normally
    args = parser.parse_args()

    # Dispatch subcommands
    if args.command == "parse":
        cmd_parse_file(args.file)
    elif args.command == "add":
        cmd_add_file(args.file)
    elif args.command == "remove":
        cmd_remove_file(args.file)
    elif args.command == "dashboard":
        cmd_dashboard(args.table, args.progress)
    elif args.command == "export":
        cmd_export_to_html(args.output)
    elif args.command == "scan":
        cmd_scan_directory(args.directory)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
