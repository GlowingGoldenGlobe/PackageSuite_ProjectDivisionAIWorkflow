"""VS Code agent orchestration package exports."""

from .agent_registry import get_tab_paths, load_task_payload, load_completed_payload, load_proposal_payload
from .orchestrator_bridge import (
    load_restricted_files,
    save_restricted_files,
    mark_file_busy,
    mark_file_free,
    load_task_tab,
    write_task_tab,
)
from .templates import load_template, list_templates

__all__ = [
    "get_tab_paths",
    "load_task_payload",
    "load_completed_payload",
    "load_proposal_payload",
    "load_restricted_files",
    "save_restricted_files",
    "mark_file_busy",
    "mark_file_free",
    "load_task_tab",
    "write_task_tab",
    "load_template",
    "list_templates",
]
