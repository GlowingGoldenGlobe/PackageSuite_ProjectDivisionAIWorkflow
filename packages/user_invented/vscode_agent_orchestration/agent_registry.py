"""Helpers for agents to locate orchestration ledger files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

_REPO_ROOT = Path(__file__).resolve()
for _ in range(4):
    _REPO_ROOT = _REPO_ROOT.parent

_ORCH_ROOT = _REPO_ROOT / "orchestration" / "vscode_orchestration_gpt5"
_RESTRICTED_PATH = _ORCH_ROOT / "restricted_files_orchestrator.json"


def get_tab_paths(tab_id: str) -> Dict[str, Path]:
    base = _ORCH_ROOT
    return {
        "task": base / f"task_tab_{tab_id}.json",
        "completed": base / f"completed_tab_{tab_id}.json",
        "proposal": base / f"task_proposal_tab_{tab_id}.json",
        "busy": base / f"busy_files_tab_{tab_id}.json",
        "restricted": _RESTRICTED_PATH,
    }


def _load_json(path: Path, default_payload: Dict) -> Dict:
    if not path.exists():
        return default_payload
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_task_payload(tab_id: str) -> Dict:
    defaults = {
        "tab_id": tab_id,
        "role": "child_agent",
        "assignments": [],
        "last_sync": None,
        "prompt_instructions": [
            "Consult orchestration/vscode_orchestration_gpt5/restricted_files_orchestrator.json before editing any shared file.",
            "Do not modify files listed in the restricted registry unless the orchestrator explicitly delegates the edit.",
        ],
    }
    return _load_json(get_tab_paths(tab_id)["task"], defaults)


def load_completed_payload(tab_id: str) -> Dict:
    defaults = {"tab_id": tab_id, "completed": []}
    return _load_json(get_tab_paths(tab_id)["completed"], defaults)


def load_proposal_payload(tab_id: str) -> Dict:
    defaults = {"tab_id": tab_id, "proposals": []}
    return _load_json(get_tab_paths(tab_id)["proposal"], defaults)
