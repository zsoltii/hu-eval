#!/usr/bin/env python
"""
checkpoint.py — Atomi state mentés/betöltés hosszú futású benchmarkokhoz.

Használat:
    from checkpoint import Checkpoint
    cp = Checkpoint(Path("./state/qwen3.5-4b/hulu.json"))
    cp.mark_completed("hulu_00001", is_correct=True)
    cp.save()
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class Checkpoint:
    """Állapotmentő + betöltő. Atomi write, hogy részleges state soha ne maradjon."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state = self._load() or self._initial()

    def _initial(self) -> dict:
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": None,
            "status": "in_progress",  # in_progress | completed | failed_stopped
            "stop_reason": None,
            "current_index": 0,
            "completed_ids": [],
            "num_correct": 0,
        }

    def _load(self) -> dict | None:
        if not self.state_path.exists():
            return None
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None  # sérült state = tiszta újraindítás

    def save(self) -> None:
        """Atomi write: tmp fájl + os.replace(). Soha nem marad félig írt state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.state_path.parent,
            delete=False,
            prefix=".state_",
            suffix=".tmp",
        ) as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
            tmp_path = f.name
        os.replace(tmp_path, self.state_path)

    def mark_completed(self, item_id: str, is_correct: bool) -> None:
        self.state["current_index"] += 1
        self.state["completed_ids"].append(item_id)
        self.state["num_correct"] += int(is_correct)

    def mark_stopped(self, reason: str) -> None:
        self.state["status"] = "failed_stopped"
        self.state["stop_reason"] = reason
        self.save()

    def mark_completed_full(self) -> None:
        self.state["status"] = "completed"
        self.state["stop_reason"] = None
        self.save()

    @property
    def resume_from(self) -> int:
        """Hányadik item-től kell folytatni."""
        return self.state["current_index"]

    @property
    def is_completed(self) -> bool:
        return self.state.get("status") == "completed"
