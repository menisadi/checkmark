"""Core library (pure functions + `ChecklistManager`).

Only **pure** helpers live here; anything that prints or touches the terminal
should go in `cli.py` or a future `display.py` module.  This makes unit testing
and reuse (e.g. a Streamlit wrapper) painless.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "ChecklistManager",
    "parse_markdown_tasks",
    "parse_markdown_title",
    "build_stats",
]

# ─────────────────────────────────────────────────────────────────────────────
# Pure parsing helpers
# ─────────────────────────────────────────────────────────────────────────────

TASK_RE = re.compile(r"^\\s*[-*]\\s*\\[(x|X| )]", re.ASCII)
TITLE_RE = re.compile(r"^\\s*#\\s+(.+)$")


def parse_markdown_tasks(file_path: str | Path) -> Tuple[int, int]:
    """Return *(completed, total)* tasks counted in a Markdown file.

    We look for GitHub-style task list markers:
    ``- [ ]`` and ``- [x]`` (or ``*`` bullets). Leading whitespace is ignored.
    """

    completed = 0
    total = 0

    p = Path(file_path).expanduser()
    if not p.is_file():
        return (0, 0)

    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            m = TASK_RE.match(line)
            if m:
                total += 1
                if m.group(1).lower() == "x":
                    completed += 1
    return (completed, total)


def parse_markdown_title(file_path: str | Path) -> str:
    """Return the first markdown H1 in *file_path* or its basename."""

    p = Path(file_path).expanduser()
    if not p.is_file():
        return p.name

    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            m = TITLE_RE.match(line)
            if m:
                return m.group(1).strip()
    return p.stem


@dataclass(slots=True)
class ChecklistStat:
    path: Path
    title: str
    completed: int
    total: int

    @property
    def percent(self) -> float:
        return 0.0 if self.total == 0 else (self.completed / self.total) * 100


def build_stats(paths: Iterable[str | Path]) -> List[ChecklistStat]:
    """Return a list of *ChecklistStat* for each markdown file in *paths*."""

    stats: List[ChecklistStat] = []
    for p in paths:
        pth = Path(p).expanduser()
        title = parse_markdown_title(pth)
        completed, total = parse_markdown_tasks(pth)
        stats.append(ChecklistStat(pth, title, completed, total))
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Global config manager (unchanged API, rebuilt internals for testability)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG_PATH: Path = Path.home() / ".checkmarks_config.json"


class ChecklistManager:
    """Load / save global tracking config and expose CRUD operations."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._data: dict[str, list[str]]
        self._load()

    # ---------------------------------------------------------------------
    # persistence helpers
    # ---------------------------------------------------------------------
    def _load(self) -> None:
        if self.config_path.is_file():
            try:
                self._data = json.loads(self.config_path.read_text())
            except json.JSONDecodeError:
                self._data = {"lists": []}
        else:
            self._data = {"lists": []}

    def _save(self) -> None:
        self.config_path.write_text(json.dumps(self._data, indent=2))

    # ---------------------------------------------------------------------
    # public API
    # ---------------------------------------------------------------------
    def add(self, markdown_path: str | Path) -> None:
        md = str(Path(markdown_path).expanduser().resolve())
        if md not in self._data["lists"]:
            self._data["lists"].append(md)
            self._save()

    def remove(self, markdown_path: str | Path) -> None:
        md = str(Path(markdown_path).expanduser().resolve())
        if md in self._data["lists"]:
            self._data["lists"].remove(md)
            self._save()

    def list_paths(self) -> List[str]:
        return self._data["lists"]

    # convenience pass-throughs ------------------------------------------------
    def stats(self) -> List[ChecklistStat]:
        return build_stats(self.list_paths())
