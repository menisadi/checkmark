"""Core behaviour tests."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from checkmarks.core import ChecklistManager


# ─────────────────────────────────────────────────────────────────────────────
# add/remove round‑trip
# ─────────────────────────────────────────────────────────────────────────────


def test_add_and_remove_round_trip():
    with TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "config.json"
        md = Path(tmpdir) / "todo.md"
        md.write_text("- [ ] sample task")

        mgr = ChecklistManager(config_path=cfg)
        mgr.add(md)
        assert mgr.list_paths() == [str(md.resolve())]

        mgr.remove(md)
        assert mgr.list_paths() == []


# ─────────────────────────────────────────────────────────────────────────────
# legacy schema migration
# ─────────────────────────────────────────────────────────────────────────────


def test_legacy_schema_migrated():
    with TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "config.json"
        legacy = ["a.md", "b.md"]
        cfg.write_text(json.dumps(legacy))

        mgr = ChecklistManager(config_path=cfg)
        assert mgr.list_paths() == legacy
