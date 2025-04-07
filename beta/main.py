#!/usr/bin/env python3
"""
checkmarks - A tool to parse Markdown task lists and display progress.

Usage:
  python checkmarks.py parse /path/to/file.md
  python checkmarks.py add /path/to/file.md
  python checkmarks.py dashboard [--table | --progress]
  python checkmarks.py export /path/to/output.html
  python checkmarks.py scan /path/to/directory

Commands:
- parse: Parse a single Markdown file and display a simple progress bar + title.
- add:   Add a Markdown file to the dashboard's tracked list (stored in config).
- dashboard:
    - No flags: Display each tracked file with a simple ASCII progress bar
    - --table: Show a Rich table (requires `rich` installed)
    - --progress: Show animated Rich progress bars (requires `rich` installed)
- export: Export the current dashboard to an HTML file
- scan:   Recursively find .md files in a directory that contain tasks
          and interactively add them to the tracked list.
"""

import argparse
import os
import re
import json
from typing import List, Tuple

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


def load_dashboard_config() -> List[str]:
    """
    Load the list of tracked files from the global configuration file.

    Returns:
        A list of file paths being tracked.
    """
    if os.path.isfile(CONFIG_FILENAME):
        with open(CONFIG_FILENAME, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("tracked_files", [])
            except json.JSONDecodeError:
                return []
    else:
        return []


def save_dashboard_config(tracked_files: List[str]) -> None:
    """
    Save the list of tracked files to the global configuration file.

    Args:
        tracked_files: List of file paths to be saved.
    """
    data = {"tracked_files": tracked_files}
    with open(CONFIG_FILENAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_markdown_tasks(file_path: str) -> Tuple[int, int]:
    """
    Parse a Markdown file for tasks of the form:
      - [ ] Task ...
      - [x] Task ...

    Args:
        file_path: Path to the Markdown file.

    Returns:
        A tuple (completed_count, total_count).
    """
    completed = 0
    total = 0
    # Matches lines like "- [ ] something" or "* [x] done"
    task_pattern = re.compile(r"^(\s*)[-*]\s+\[([ xX])\]\s+", re.IGNORECASE)

    if not os.path.isfile(file_path):
        return (0, 0)

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = task_pattern.match(line)
            if match:
                total += 1
                if match.group(2).lower() == "x":
                    completed += 1

    return (completed, total)


def parse_markdown_title(file_path: str) -> str:
    """
    Parse the first top-level heading (i.e. '# Title') in the Markdown file.
    If none is found, return the filename (without path).

    Args:
        file_path: Path to the Markdown file.

    Returns:
        The Markdown file's title or the file's basename if no title found.
    """
    title_pattern = re.compile(r"^\s*#\s+(.+)$")

    if not os.path.isfile(file_path):
        return os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = title_pattern.match(line)
            if match:
                return match.group(1).strip()

    return os.path.basename(file_path)


def print_simple_progress_bar(
    completed: int, total: int, width: int = 30
) -> None:
    """
    Print a simple ASCII progress bar to the terminal.

    Args:
        completed: Number of completed tasks.
        total: Number of total tasks.
        width: The width of the progress bar in characters.
    """
    if total == 0:
        print("No tasks found.")
        return

    ratio = completed / total
    fill_length = int(ratio * width)
    bar = "#" * fill_length + "-" * (width - fill_length)
    percent = ratio * 100
    print(f"[{bar}] {percent:.1f}%  ({completed}/{total} tasks)")


def cmd_parse_file(file_path: str) -> None:
    """
    Parse a single Markdown file, display its title and progress bar.

    Args:
        file_path: The Markdown file path to parse.
    """
    title = parse_markdown_title(file_path)
    completed, total = parse_markdown_tasks(file_path)
    print(f"File: {title}")
    print_simple_progress_bar(completed, total)


def cmd_add_file(file_path: str) -> None:
    """
    Add a Markdown file to the dashboard configuration.

    Args:
        file_path: The Markdown file path to add.
    """
    tracked_files = load_dashboard_config()
    if file_path not in tracked_files:
        tracked_files.append(file_path)
        save_dashboard_config(tracked_files)
        print(f"Added '{file_path}' to the dashboard.")
    else:
        print(f"'{file_path}' is already in the dashboard.")


def generate_dashboard_data(
    tracked_files: List[str],
) -> List[Tuple[str, int, int, str]]:
    """
    Generate a list of (title, completed, total, file_path) for each file in the dashboard.

    Args:
        tracked_files: A list of file paths to parse.

    Returns:
        A list of tuples: (title, completed count, total count, file_path).
    """
    dashboard_data = []
    for file_path in tracked_files:
        c, t = parse_markdown_tasks(file_path)
        title = parse_markdown_title(file_path)
        dashboard_data.append((title, c, t, file_path))
    return dashboard_data


def cmd_dashboard(
    table_view: bool = False, progress_view: bool = False
) -> None:
    """
    Show the dashboard of all tracked files.

    Args:
        table_view: If True, show the dashboard as a Rich table (requires rich).
        progress_view: If True, show the dashboard as animated progress bars (requires rich).
    """
    tracked_files = load_dashboard_config()
    if not tracked_files:
        print(
            "No files are being tracked yet. Use 'add' command to add files."
        )
        return

    # Each entry is (title, completed, total, file_path)
    dashboard_data = generate_dashboard_data(tracked_files)

    # If rich is not available, fallback to simple prints
    if RICH_AVAILABLE and table_view:
        print_dashboard_as_table(dashboard_data)
    elif RICH_AVAILABLE and progress_view:
        print_dashboard_as_rich_progress(dashboard_data)
    else:
        # Fallback: just print text-based progress bars
        print("Tracked files:")
        for title, completed, total, _ in dashboard_data:
            print(f"- {title}")
            print_simple_progress_bar(completed, total)


def print_dashboard_as_table(
    dashboard_data: List[Tuple[str, int, int, str]],
) -> None:
    """
    Print the dashboard data as a Rich table.

    Args:
        dashboard_data: List of tuples (title, completed, total, file_path).
    """
    console = Console()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Title", justify="left")
    table.add_column("Completed", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Progress", justify="left")

    for title, completed, total, file_path in dashboard_data:
        if total == 0:
            progress_str = "No tasks"
            ratio_str = "-"
        else:
            ratio = completed / total
            ratio_str = f"{ratio * 100:.1f}%"
            bar_length = 20
            fill_len = int(ratio * bar_length)
            progress_str = "#" * fill_len + "-" * (bar_length - fill_len)

        table.add_row(
            title, str(completed), str(total), f"{progress_str} {ratio_str}"
        )

    console.print(table)


def print_dashboard_as_rich_progress(
    dashboard_data: List[Tuple[str, int, int, str]],
) -> None:
    """
    Print the dashboard data as animated rich progress bars.

    Args:
        dashboard_data: List of tuples (title, completed, total, file_path).
    """
    console = Console()
    with Progress(console=console) as progress:
        for title, completed, total, file_path in dashboard_data:
            if total == 0:
                # No tasks, add a completed dummy task
                task_id = progress.add_task(title, total=1)
                progress.update(task_id, completed=1)
            else:
                task_id = progress.add_task(title, total=total)
                progress.update(task_id, completed=completed)


def cmd_export_to_html(output_path: str) -> None:
    """
    Export the current dashboard to a standalone HTML file.

    Args:
        output_path: The file path to write HTML output to.
    """
    tracked_files = load_dashboard_config()
    if not tracked_files:
        print("No files are being tracked yet. Nothing to export.")
        return

    dashboard_data = generate_dashboard_data(tracked_files)

    html_content = [
        "<html>",
        "<head><meta charset='utf-8'><title>Checkmarks Dashboard</title></head>",
        "<body>",
        "<h1>Checkmarks Dashboard</h1>",
        "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>",
        "<tr><th>Title</th><th>Completed</th><th>Total</th><th>Progress</th></tr>",
    ]

    for title, completed, total, file_path in dashboard_data:
        if total == 0:
            progress_str = "No tasks"
            ratio_str = "-"
        else:
            ratio = completed / total
            ratio_str = f"{ratio * 100:.1f}%"
            bar_length = 20
            fill_len = int(ratio * bar_length)
            progress_bar = "#" * fill_len + "-" * (bar_length - fill_len)
            progress_str = f"{progress_bar} {ratio_str}"
        html_content.append(
            f"<tr><td>{title}</td>"
            f"<td>{completed}</td><td>{total}</td><td>{progress_str}</td></tr>"
        )

    html_content.append("</table>")
    html_content.append("</body></html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_content))

    print(f"Dashboard exported to: {output_path}")


def cmd_scan_directory(directory: str) -> None:
    """
    Scan a directory for Markdown files containing tasks and interactively
    add them to the dashboard configuration.

    Args:
        directory: Path to the directory to scan.
    """
    if not os.path.isdir(directory):
        print(f"'{directory}' is not a directory.")
        return

    potential_files = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name.lower().endswith(".md"):
                file_path = os.path.join(root, name)
                c, t = parse_markdown_tasks(file_path)
                if t > 0:
                    potential_files.append((file_path, c, t))

    if not potential_files:
        print("No Markdown files with tasks found in that directory.")
        return

    tracked_files = load_dashboard_config()
    for file_path, c, t in potential_files:
        title = parse_markdown_title(file_path)
        if file_path in tracked_files:
            print(f"Already tracked: {title} ({os.path.basename(file_path)})")
            continue
        print(f"Found: {title} ({c}/{t} tasks). Add to dashboard? [y/n]")
        choice = input("> ").strip().lower()
        if choice == "y":
            tracked_files.append(file_path)
            print(f"Added {title} to the dashboard.")
        else:
            print(f"Skipped {title}.")
    save_dashboard_config(tracked_files)


def main() -> None:
    """
    Entry point for the checkmarks CLI application.
    """
    parser = argparse.ArgumentParser(
        description="checkmarks - Parse Markdown task lists and display progress."
    )
    subparsers = parser.add_subparsers(dest="command")

    # parse command
    parse_parser = subparsers.add_parser(
        "parse", help="Parse a single Markdown file."
    )
    parse_parser.add_argument("file", type=str, help="Path to a Markdown file")

    # add command
    add_parser = subparsers.add_parser(
        "add", help="Add a Markdown file to the dashboard."
    )
    add_parser.add_argument("file", type=str, help="Path to a Markdown file")

    # dashboard command
    dash_parser = subparsers.add_parser(
        "dashboard", help="Show the dashboard."
    )
    dash_parser.add_argument(
        "--table",
        action="store_true",
        help="Display as a Rich table (requires rich).",
    )
    dash_parser.add_argument(
        "--progress",
        action="store_true",
        help="Display as Rich progress bars (requires rich).",
    )

    # export command
    export_parser = subparsers.add_parser(
        "export", help="Export the dashboard to HTML."
    )
    export_parser.add_argument(
        "output", type=str, help="Output HTML file path"
    )

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="Scan a directory for Markdown files with tasks."
    )
    scan_parser.add_argument("directory", type=str, help="Directory path")

    args = parser.parse_args()

    if args.command == "parse":
        cmd_parse_file(args.file)
    elif args.command == "add":
        cmd_add_file(args.file)
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
