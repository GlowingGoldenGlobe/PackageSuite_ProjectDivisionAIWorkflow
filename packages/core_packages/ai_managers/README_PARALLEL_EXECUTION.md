# Parallel Execution Manager

## Overview

The Parallel Execution Manager is a specialized AI Manager for the GlowingGoldenGlobe project that coordinates multiple AI Manager roles to run simultaneously while respecting hardware resource limitations. This system optimizes resource usage by dynamically adjusting workloads based on system capabilities.

## Key Features

- **Multi-Role Coordination**: Runs different AI Manager roles simultaneously based on priority
- **Resource Monitoring**: Continuously monitors CPU, memory, and disk usage
- **Adaptive Scaling**: Dynamically adjusts which roles are active based on resource availability
- **Task Queuing**: Maintains separate task queues for each role
- **Automatic Script Assessment**: Evaluates Python scripts for quality and performance
- **Configurable Priorities**: Allows customization of role importance and resource requirements
- **File Usage Tracking**: Prevents conflicts when multiple roles attempt to access the same files

## Defined Roles

The Parallel Execution Manager coordinates six key roles:

1. **Agent Simulations** - Runs simulations for different AI agents in the project
2. **Project Management** - Coordinates overall project activities and milestones
3. **Resource Management** - Monitors and optimizes system resource usage
4. **Script Assessment** - Analyzes and improves Python scripts in the project
5. **GUI Testing** - Tests and validates GUI components
6. **Task Management** - Schedules and prioritizes project tasks

## Configuration

The system is configured through `parallel_execution_config.json`, which defines:

- Resource thresholds for CPU, memory, and disk usage
- Priority levels for each role
- Resource requirements for each role
- Monitoring interval for resource checks
- Role-specific configuration options

## Usage

### Basic Usage

```python
from ai_managers.parallel_execution_manager import ParallelExecutionManager

# Create the manager
manager = ParallelExecutionManager()

# Start all roles with resource management
manager.start_all_roles()

# Queue a task for a specific role
manager.queue_task('script_assessment', {
    'name': 'Assess model.py',
    'script_path': '/path/to/model.py',
    'priority': 'high'
})

# When done
manager.stop_all_roles()
```

### Starting Specific Roles

To start only specific roles:

```python
manager = ParallelExecutionManager()

# Start resource monitoring
manager.start_monitoring()

# Start only selected roles
manager._start_role_thread('resource_management')
manager._start_role_thread('project_management')
```

## Resource Requirements

The Parallel Execution Manager requires:

- Python 3.6 or higher
- psutil package (recommended for accurate resource monitoring)
- Sufficient system resources to run multiple roles in parallel

If psutil is not installed, the manager will use estimated resource values.

## Extending the Manager

To add a new role:

1. Add the role name as a class constant
2. Add a queue for the role in `__init__`
3. Define resource requirements and priority
4. Implement a `_run_[role_name]` method
5. Update the `_start_role_thread` method

## Integration with Existing Systems

The Parallel Execution Manager is designed to integrate with all existing AI Manager components in the GlowingGoldenGlobe project. It orchestrates their execution without modifying their core functionality.

## File Usage Tracking System

The Parallel Execution Manager now includes file usage tracking to prevent conflicts when multiple parallel roles try to access the same files simultaneously.

To enable file tracking in your tasks, simply include a `files` list when queuing tasks:

```python
manager.queue_task('agent_simulations', {
    'name': 'Run model simulation',
    'script': 'simulation.py',
    'agent_id': 'AI_Agent_1',
    'files': ['/path/to/simulation.py', '/path/to/data.json']
})
```

For complete documentation on the file tracking system, see:
- **Main Documentation**: `docs/FILE_USAGE_TRACKING.md`
- **Implementation**: `ai_managers/file_usage_tracker.py`
- **General Overview**: See the File Usage Tracking section in the main `README.md`
