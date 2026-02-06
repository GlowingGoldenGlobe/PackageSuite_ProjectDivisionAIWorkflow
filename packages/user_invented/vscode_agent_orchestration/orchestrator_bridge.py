"""Bridge helpers between orchestrator state and packaged utilities."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List

try:
    from orchestration.vscode_orchestration_gpt5 import busy_ledgers
except ModuleNotFoundError:
    REPO_ROOT = Path(__file__).resolve()
    for _ in range(4):
        REPO_ROOT = REPO_ROOT.parent
    sys.path.append(str(REPO_ROOT))
    from orchestration.vscode_orchestration_gpt5 import busy_ledgers  # type: ignore

_REPO_ROOT = Path(__file__).resolve()
for _ in range(4):
    _REPO_ROOT = _REPO_ROOT.parent

_ORCH_ROOT = _REPO_ROOT / "orchestration" / "vscode_orchestration_gpt5"
_RESTRICTED_PATH = _ORCH_ROOT / "restricted_files_orchestrator.json"
_TASK_TEMPLATE = "task_tab_{tab_id}.json"


def _atomic_write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tmp:
        json.dump(payload, tmp, indent=2, sort_keys=True)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, path)


def _task_path(tab_id: str) -> Path:
    return _ORCH_ROOT / _TASK_TEMPLATE.format(tab_id=tab_id)


def load_restricted_files() -> List[Dict[str, str]]:
    if not _RESTRICTED_PATH.exists():
        return []
    with _RESTRICTED_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return list(data.get("files", []))


def save_restricted_files(files: Iterable[Dict[str, str]]) -> None:
    payload = {"description": "Registry of files restricted to orchestrator writes unless delegated.", "files": list(files)}
    _atomic_write_json(_RESTRICTED_PATH, payload)


def mark_file_busy(tab_id: str, target_path: str, note: str | None = None) -> None:
    busy_ledgers.mark_busy(tab_id, target_path, note)


def mark_file_free(tab_id: str, target_path: str) -> None:
    busy_ledgers.mark_free(tab_id, target_path)


def load_task_tab(tab_id: str) -> Dict:
    path = _task_path(tab_id)
    if not path.exists():
        return {"tab_id": tab_id, "assignments": []}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_task_tab(tab_id: str, payload: Dict) -> None:
    payload.setdefault("tab_id", tab_id)
    _atomic_write_json(_task_path(tab_id), payload)
