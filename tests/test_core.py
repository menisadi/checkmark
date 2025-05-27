"""Smoke tests for add/remove round‑trip."""

from pathlib import Path
from tempfile import TemporaryDirectory

from checkmarks.core import ChecklistManager


def test_add_and_remove_round_trip():
    with TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "config.json"
        md = Path(tmpdir) / "todo.md"
        md.write_text("- [ ] sample task\n")

        mgr = ChecklistManager(config_path=cfg)
        mgr.add(md)
        assert mgr.list_paths() == [str(md.resolve())]

        mgr.remove(md)
        assert mgr.list_paths() == []
