# Claude Parallel Execution Examples

This directory contains example tasks and scripts for the Claude Code Parallel Execution System in the GlowingGoldenGlobe project. These examples demonstrate how to use Claude Code to run multiple tasks simultaneously in parallel when other agents (PyAutoGen, VSCode) aren't available.

## Example Tasks

Each task represents a simulation for the respective AI Agent's responsibility:

- **AI_Agent_1**: `parallel_agent1_task.py` - Micro-robot-composite part development
- **AI_Agent_2**: `parallel_agent2_task.py` - Humanoid torso development
- **AI_Agent_3**: `parallel_agent3_task.py` - Head and neck development
- **AI_Agent_4**: `parallel_agent4_task.py` - Shoulders and arms development
- **AI_Agent_5**: `parallel_agent5_task.py` - Wrists and hands development

Each example task:
- Simulates a multi-step design or development process
- Performs CPU-intensive calculations to simulate real workload
- Shows progress reporting
- Creates output files with results
- Has configurable duration and complexity

## Running Parallel Tasks

You can run these examples in parallel using the `run_parallel_tasks.py` script:

```bash
# Run one instance of each example task in parallel
python run_parallel_tasks.py

# Run multiple instances of each task
python run_parallel_tasks.py --count=3

# Run tasks for a specific agent only
python run_parallel_tasks.py --agent=1
```

## Integration with Claude Parallel Manager

These examples are designed to work with the Claude Parallel Manager system, which:

1. Detects which agents are available (Claude, PyAutoGen, VSCode)
2. Manages system resources to run tasks efficiently
3. Schedules and prioritizes task execution
4. Monitors progress and prevents system overload

## Using in Your Own Code

You can use these examples as templates for creating your own parallel tasks:

1. Create a Python script that performs your task
2. Add proper logging and progress reporting
3. Register the task with the Claude Parallel Manager:

```python
from claude_parallel_manager import ClaudeParallelManager

# Initialize Claude Parallel Manager
manager = ClaudeParallelManager()
manager.start()

# Add a task
task_id = manager.add_script_task(
    script_path="/path/to/your/script.py",
    priority=3,            # Lower number = higher priority
    task_type="simulation"  # Or "utility", "blender_task", etc.
)

# Monitor task status
task_status = manager.get_task_status(task_id)
print(f"Task status: {task_status.get('status')}")
```

## Task Types and Resource Allocation

The system supports different task types with varying resource requirements:

- **blender_task**: High CPU/memory usage, limited to 1 concurrent task
- **simulation**: Moderate CPU/memory usage, limited to 2 concurrent tasks
- **analysis**: Lower CPU/memory usage, limited to 3 concurrent tasks
- **utility**: Minimal CPU/memory usage, limited to 5 concurrent tasks

## Integration with Existing Parallel Execution Manager

These example tasks can also integrate with the project's existing Parallel Execution Manager via the Claude Parallel Integration module. This allows Claude to seamlessly step in when PyAutoGen or VSCode agents aren't available.

## Creating Output Directories

When you run these tasks, they will create output directories in their respective AI_Agent folders:

```
/AI_Agent_1/agent_outputs/
/AI_Agent_2/agent_outputs/
/AI_Agent_3/agent_outputs/
/AI_Agent_4/agent_outputs/
/AI_Agent_5/agent_outputs/
```

Each output file contains simulation results in JSON format.