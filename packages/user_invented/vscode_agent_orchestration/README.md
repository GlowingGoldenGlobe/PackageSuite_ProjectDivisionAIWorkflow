# VS Code Agent Orchestration

Utilities that expose the repository's VS Code agent orchestration workflow through a reusable package.

## Files Included:
- __init__.py
- orchestrator_bridge.py
- agent_registry.py

## Highlights
- Wraps busy ledger helpers so packages can mark files busy or free without duplicating orchestration code.
- Surfaces restricted file registry handling for orchestrator-only documents (for example the canonical tasks log).
- Provides child agent accessors that locate task, completion, and proposal ledgers while enforcing prompt instructions.
- Ships prompt templates that instruct agents to reserve files via busy-ledger commands and report outcomes before handing work back to the orchestrator.

## Workflow Overview
- Orchestrator owns the canonical task log (project_modifications_tasks/tasks_022026_1.md) and updates tab assignments under orchestration/vscode_orchestration_gpt5/.
- Child agent tabs operate on their scoped task_tab_[n].json, completed_tab_[n].json, and task_proposal_tab_[n].json files while respecting the restricted files registry.
- Busy ledgers (busy_files_tab_[n].json and busy_files_all_agents.json) prevent simultaneous edits; the package proxies busy ledger mark/free operations from orchestration/vscode_orchestration_gpt5/busy_ledgers.py.
- tab_plan.json records default (four) and optional (up to nine) child tabs so automation can scale without manual path specification.

## Repository Integration
- The package expects the repository to expose orchestration artifacts under orchestration/vscode_orchestration_gpt5/ as documented in the workspace README for that directory.
- orchestrator_bridge.py interacts with:
	- task_tab_*.json, completed_tab_*.json, task_proposal_tab_*.json (per-tab ledgers)
	- restricted_files_orchestrator.json (single-writer file registry)
	- busy ledgers via orchestration.vscode_orchestration_gpt5.busy_ledgers
- agent_registry.py resolves per-tab file paths and supplies default payloads with prompt instructions to enforce restricted file consultation before edits.
- A templates directory ships with pre-created JSON payloads (tab_plan.json, task/complete/proposal/busy ledgers, and restricted files). Use `load_template("tab_plan.json")` or helper shorthands like `list_templates()` to seed new installations.

## Usage
```python
from vscode_agent_orchestration import (
		get_tab_paths,
		load_task_payload,
		write_task_tab,
		mark_file_busy,
		mark_file_free,
        load_template,
)

paths = get_tab_paths("1")
payload = load_task_payload("1")
payload["assignments"].append({"title": "Update docs", "restricted": False})
mark_file_busy("1", "docs/README.md", note="drafting update")
write_task_tab("1", payload)
mark_file_free("1", "docs/README.md")

# bootstrap a fresh task tab from the packaged template
default_task = load_template("task_tab_default.json")
```
