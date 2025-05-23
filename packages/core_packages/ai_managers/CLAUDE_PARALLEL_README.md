# Claude Parallel Workflow System

The Claude Parallel Workflow System is a comprehensive solution for the GlowingGoldenGlobe project that enables Claude Code to manage multiple tasks simultaneously when other AI agents (PyAutoGen, VSCode) aren't available, or to supplement them when they are available but limited in capacity.

## System Components

### Core Components
1. **ClaudeParallelManager** (`claude_parallel_manager.py`)
   - Manages the parallel execution of tasks
   - Coordinates resource allocation based on task types
   - Supports different execution modes based on available agents

2. **ClaudeTaskExecutor** (`claude_task_executor.py`)
   - Executes individual tasks with isolation and monitoring
   - Supports different task types (scripts, Blender scripts, functions, commands)
   - Captures outputs, errors, and execution metrics

3. **AIAgentDetector** (`ai_agent_detector.py`)
   - Detects which AI agents are available (Claude, PyAutoGen, VSCode)
   - Determines the optimal execution mode based on available agents
   - Provides detailed information about agent capabilities

4. **ClaudeParallelIntegration** (`claude_parallel_integration.py`)
   - Integrates the Claude Parallel Manager with the existing ParallelExecutionManager
   - Enables seamless handoff between different AI agents
   - Provides a unified interface for task scheduling and execution

### Advanced Features

5. **ClaudeTaskScheduler** (`claude_task_scheduler.py`)
   - Enables scheduling of tasks for regular execution
   - Supports interval, daily, weekly, monthly, and one-time schedules
   - Automatically adds scheduled tasks to the execution queue

6. **ClaudeResourceMonitor** (`claude_resource_monitor.py`)
   - Monitors system resources (CPU, memory, disk, network)
   - Provides adaptive resource allocation strategies
   - Tracks resource usage history for optimization

7. **GUI Integration** (`gui/claude_parallel_gui.py`, `gui/gui_claude_integration.py`)
   - Provides a graphical interface for managing parallel tasks
   - Integrates with the existing GlowingGoldenGlobe GUI
   - Displays real-time resource usage and task status

8. **Example Tasks** (`ai_managers/examples_parallel_run/`)
   - Provides example tasks for each AI Agent (1-5)
   - Demonstrates parallel execution of various task types
   - Includes a batch runner script for testing

## Configuration Files

1. `claude_parallel_config.json` - Main configuration for the parallel execution system
2. `claude_scheduler_config.json` - Configuration for the task scheduler
3. `claude_resource_config.json` - Configuration for the resource monitor

## Getting Started

### Starting the Parallel Execution System

```python
from claude_parallel_manager import ClaudeParallelManager
from claude_resource_monitor import ClaudeResourceMonitor
from claude_task_scheduler import ClaudeTaskScheduler

# Initialize and start the Claude Parallel Manager
manager = ClaudeParallelManager()
manager.start()

# Initialize and start the Resource Monitor
resource_monitor = ClaudeResourceMonitor()
resource_monitor.start(strategy_callback=manager.apply_resource_strategy)

# Initialize and start the Task Scheduler
scheduler = ClaudeTaskScheduler()
scheduler.start(claude_manager=manager)

# Add a task to the parallel execution system
task_id = manager.add_script_task(
    script_path="/path/to/your/script.py",
    priority=3,  # Lower numbers = higher priority
    task_type="simulation"  # or "utility", "blender_task", "analysis"
)
```

### Using the GUI

The Claude Parallel System can be accessed through the main GlowingGoldenGlobe GUI:

1. Launch the GUI: `python gui/gui_main.py`
2. The Claude Parallel tab will be automatically added
3. Use the GUI to start/stop the system, add tasks, and monitor execution

Alternatively, you can launch the Claude Parallel GUI directly:

```bash
python gui/claude_parallel_gui.py
```

### Running Example Tasks

The system includes example tasks that demonstrate parallel execution:

```bash
python ai_managers/examples_parallel_run/run_parallel_tasks.py
```

### Scheduling Tasks

You can schedule tasks for regular execution:

```python
from claude_task_scheduler import ClaudeTaskScheduler, ScheduledTask

scheduler = ClaudeTaskScheduler()

# Add a daily task
scheduler.add_task(
    task_data={
        "script_path": "/path/to/your/script.py",
        "task_type": "utility",
        "priority": 5
    },
    schedule_type=ScheduledTask.DAILY,
    schedule_params={"time": "12:00"}
)

# Start the scheduler
scheduler.start(claude_manager=manager)
```

## Execution Modes

The system supports different execution modes based on available agents:

1. **Claude Only Mode** - Only Claude Code is available, handles all parallel execution
2. **Supplement Mode** - Claude supplements PyAutoGen and/or VSCode agents
3. **Takeover Mode** - Claude takes over when other agents are unavailable

## Task Types and Resource Allocation

The system supports different task types with varying resource requirements:

- **blender_task**: High CPU/memory usage, limited to 1 concurrent task
- **simulation**: Moderate CPU/memory usage, limited to 2 concurrent tasks
- **analysis**: Lower CPU/memory usage, limited to 3 concurrent tasks
- **utility**: Minimal CPU/memory usage, limited to 5 concurrent tasks

Resource allocation is automatically adjusted based on system load and task priorities.

## Integration with Existing Systems

The Claude Parallel Workflow System is fully integrated with the existing project:

1. Works alongside the ParallelExecutionManager
2. Integrates with the main GUI interface
3. Uses the same project structure and naming conventions
4. Shares task outputs with the appropriate agent output directories

## Future Enhancements

A scheduled task has been added to implement metrics visualization in 2 months, which will provide:

- Visual representation of resource usage over time
- Task execution statistics and performance metrics
- Optimization recommendations based on historical data

## Technical Notes

- All components run as separate threads to avoid blocking the main application
- Resource monitoring adapts to system capabilities
- The system is designed to be portable across different operating systems
- Configuration files use JSON format for easy editing
- Extensive logging is implemented for troubleshooting