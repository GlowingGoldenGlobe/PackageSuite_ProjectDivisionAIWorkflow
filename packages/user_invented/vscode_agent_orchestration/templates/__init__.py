"""Template payloads for VS Code agent orchestration."""

from __future__ import annotations

import json
from importlib import resources
from typing import Dict

_TEMPLATE_PACKAGE = __name__


def load_template(name: str) -> Dict:
    """Load a JSON template bundled with the package."""
    with resources.files(_TEMPLATE_PACKAGE).joinpath(name).open("r", encoding="utf-8") as handle:  # type: ignore[arg-type]
        return json.load(handle)


def list_templates() -> Dict[str, str]:
    return {
        "tab_plan": "tab_plan.json",
        "task_default": "task_tab_default.json",
        "task_optional": "task_tab_optional.json",
        "completed": "completed_tab.json",
        "proposal": "task_proposal_tab.json",
        "busy_tab": "busy_files_tab.json",
        "busy_all": "busy_files_all_agents.json",
        "restricted": "restricted_files_orchestrator.json",
    }
