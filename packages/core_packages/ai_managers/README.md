# AI Managers Directory

This directory contains specialized AI Manager modules for the GlowingGoldenGlobe project. These modules function as "specialized mini-brains" with specific responsibilities rather than general-purpose implementation files.

## What is an AI Manager?

As defined in `AI_MANAGER_CONCEPT.md`:

> The concept of an AI Manager is that it makes observations and assessments like a standalone mini-brain, but specialized, not AGI - sort of like an employee manager but with only the ability to perform a specific role and not with the ability to do anything other than its specialized script about its responsibilities.

### AI Manager Qualification Criteria

A component qualifies as an AI Manager if it:
- **Observes and Assesses**: Monitors conditions within its domain and makes evaluations
- **Makes Autonomous Decisions**: Chooses between options based on its assessments
- **Coordinates Operations**: Orchestrates multiple activities within its specialty area
- **Has Domain Expertise**: Specializes in a specific area of responsibility
- **Acts as Mini-Brain**: Functions independently within its scope

### NOT an AI Manager: Service Modules

A component is a Service Module (utility) if it:
- **Executes Tasks When Called**: Responds to external requests without autonomous decision-making
- **Provides Functions**: Offers specific operations or utilities to other components
- **No Strategic Assessment**: Performs predefined tasks without evaluating conditions
- **Tool-like Behavior**: Acts as a passive instrument rather than active coordinator

**Examples:**
- AI Manager: `project_ai_manager.py` (decides project priorities, coordinates activities)
- Service Module: `clipboard_workflow_utils.py` (provides file backup/restore functions when called)

AI Managers are distinguished from regular implementation files by their:
- Decision-making capabilities
- Domain-specific assessments
- Responsibility-oriented functions
- Coordination roles

## Available AI Managers

- **Project AI Manager** (`project_ai_manager.py`): Orchestrates overall project activities and makes project-level decisions
- **Resource AI Manager** (`project_resource_manager.py`): Assesses hardware resources and makes allocation decisions
- **Task Manager** (`task_manager.py`): Schedules and coordinates project tasks
- **Git Task Manager** (`git_task_manager.py`): Manages version control operations and task integration
- **Refined Model Manager** (`refined_model_manager.py`): Evaluates and manages model quality
- **AI Assessment Controls** (`ai_assessment_controls.py`): Makes intelligent decisions about agent configuration, interleaving modes, and resource allocation during sessions

## Integration

The AI Manager architecture is illustrated in the `docs/ai_managers_chart.md` document, showing how these specialized modules interact with implementation files and each other.

For more detailed explanations about the AI Manager concept, refer to `AI_MANAGER_CONCEPT.md` in the root directory.

## Automation Guidelines

When implementing automation within AI Managers, the following principles must be followed:

### Core Principle

**Automation should work effectively within established guidelines, not deviate from them without good reason.**

### Implementation Rules

1. **Respect Established Patterns**
   - Follow the project's existing patterns and decisions
   - Do not arbitrarily deviate from existing conventions
   - Maintain consistency with previously agreed-upon approaches

2. **Rational Implementation**
   - Changes must have a legitimate justification
   - Never break previously discussed guidelines without a compelling reason
   - Any deviation must be explained with a valid technical rationale

3. **Maintain Project Integrity**
   - Custom elements (like icons, styles, naming conventions) must be preserved
   - Respect architectural decisions that have already been made
   - Integration should enhance existing components, not replace or duplicate them

4. **Effective Automation**
   - Automation should execute reliably within reasonable boundaries
   - It should not require constant supervision
   - Automation is desired and should NOT be defeated with unnecessary interaction

These guidelines apply to all AI Managers and should be referenced by any module that implements automated workflows. For file creation guidelines, also reference `docs/duplicate_file_prevention_task.md`.

## Claude Interleaving and AI Assessment

The AI Assessment Controls module (`ai_assessment_controls.py`) provides intelligent session management capabilities:

### Key Features

1. **Session Startup Assessment**
   - Analyzes planned task complexity
   - Evaluates system resource availability
   - Determines optimal interleaving mode per agent
   - Recommends resource allocation and parallel execution strategy

2. **Dynamic Task Completion Handling**
   - Monitors when agents complete tasks
   - Makes real-time decisions for freed agents:
     - Reassign to high-priority tasks
     - Redistribute work from overloaded agents
     - Optimize parallel execution capacity
   - Ensures efficient resource utilization

3. **Interleaving Mode Decisions**
   - Enables "extended thinking" for complex tasks requiring:
     - Multi-step reasoning
     - Optimization problems
     - Debugging and analysis
   - Disables for simple tasks to conserve resources

### Integration with GUI

The AI Assessment Controls are integrated into the Agent Configuration tab of the GUI, providing:
- Visual feedback on AI decisions
- Manual override capabilities
- Real-time monitoring of assessments
- Resource threshold configuration

For detailed usage instructions, see the [Claude Interleaving & AI Assessment User Guide](../help/interleaving_user_guide.md).

### Configuration Storage

Assessment decisions and configurations are stored in `ai_session_assessment.json`, maintaining:
- Session history
- Auto-adjustment settings
- Resource thresholds
- Task distribution patterns