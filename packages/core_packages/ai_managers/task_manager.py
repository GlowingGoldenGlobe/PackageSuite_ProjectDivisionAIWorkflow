#!/usr/bin/env python
# Project Task Manager for GlowingGoldenGlobe
# Handles to-do lists, schedules, and project planning

import os
import json
import datetime
import uuid


class TaskManager:
    """Manages project tasks and schedules"""

    def __init__(self, config_file="project_tasks.json"):
        self.config_file = config_file
        self.tasks = []
        self.schedules = []
        self.categories = [
    "Development",
    "Testing",
    "Research",
    "Documentation",
     "Other"]
        self.priority_levels = ["Low", "Medium", "High", "Critical"]
        # Load existing tasks if available
        self.load_tasks()

        # Add psutil installation reminder if not present
        self._ensure_psutil_task()

    def load_tasks(self):
        """Load tasks from configuration file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.schedules = data.get("schedules", [])
                    if "categories" in data:
                        self.categories = data["categories"]
                    if "priority_levels" in data:
                        self.priority_levels = data["priority_levels"]
            except Exception as e:
                print(f"Error loading tasks: {str(e)}")

    def save_tasks(self):
        """Save tasks to configuration file"""
        try:
            data = {
                "tasks": self.tasks,
                "schedules": self.schedules,
                "categories": self.categories,
                "priority_levels": self.priority_levels,
                "last_updated": datetime.datetime.now().isoformat()
            }

            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {str(e)}")

    def add_task(self, title, description="",
                 category="Development", priority="Medium", due_date=None):
        """Add a new task to the list"""
        task_id = str(uuid.uuid4())

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "created_date": datetime.datetime.now().isoformat(),
            "due_date": due_date,
            "completed": False,
            "completed_date": None
        }

        self.tasks.append(task)
        self.save_tasks()
        return task_id

    def update_task(self, task_id, **kwargs):
        """Update an existing task"""
        for task in self.tasks:
            if task["id"] == task_id:
                for key, value in kwargs.items():
                    if key in task:
                        task[key] = value

                self.save_tasks()
                return True

        return False

    def delete_task(self, task_id):
        """Delete a task"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                del self.tasks[i]
                self.save_tasks()
                return True

        return False

    def mark_task_completed(self, task_id, completed=True):
        """Mark a task as completed"""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = completed

                if completed:
                    task["completed_date"] = datetime.datetime.now().isoformat()
                else:
                    task["completed_date"] = None

                self.save_tasks()
                return True

        return False

    def get_all_tasks(self):
        """Return all tasks"""
        return self.tasks

    def get_all_schedules(self):
        """Return all schedules"""
        return self.schedules

    def get_task_by_id(self, task_id):
        """Get a task by its ID"""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def get_task_by_title(self, title):
        """Get a task by its title"""
        for task in self.tasks:
            if task.get("title") == title:
                return task
        return None

    def get_tasks_by_category(self, category):
        """Get tasks by category"""
        return [task for task in self.tasks if task["category"] == category]

    def get_tasks_by_priority(self, priority):
        """Get tasks by priority level"""
        return [task for task in self.tasks if task["priority"] == priority]

    def get_tasks_due_soon(self, days=7):
        """Get tasks due within specified number of days"""
        today = datetime.datetime.now().date()
        upcoming = []

        for task in self.tasks:
            if not task["completed"] and task.get("due_date"):
                try:
                    # Parse ISO format date and get just the date part
                    due_date = datetime.datetime.fromisoformat(
                        task["due_date"]).date()
                    days_left = (due_date - today).days

                    if 0 <= days_left <= days:
                        upcoming.append(task)
                except:
                    # Skip tasks with invalid date format
                    continue

        return upcoming

    def add_schedule(self, title, start_date, end_date=None,
                     recurrence=None, description=""):
        """Add a scheduled activity"""
        schedule_id = str(uuid.uuid4())

        schedule = {
            "id": schedule_id,
            "title": title,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "recurrence": recurrence,  # daily, weekly, monthly, etc.
            "created_date": datetime.datetime.now().isoformat()
        }
        
        self.schedules.append(schedule)
        self.save_tasks()
        return schedule_id

    def get_schedule_by_title(self, title):
        """Get a schedule by its title"""
        for schedule in self.schedules:
            if schedule.get("title") == title:
                return schedule
        return None

    def delete_schedule(self, identifier):
        """Delete a scheduled activity by id or title

        Args:
            identifier: Either a schedule ID or a schedule title
        """
        # First try to find by ID
        for i, schedule in enumerate(self.schedules):
            if schedule.get("id") == identifier:
                del self.schedules[i]
                self.save_tasks()
                return True

        # If not found by ID, try by title
        for i, schedule in enumerate(self.schedules):
            if schedule.get("title") == identifier:
                del self.schedules[i]
                self.save_tasks()
                return True

        return False

    def export_tasks(self, file_path):
        """Export tasks to a file"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".md":
            self.export_tasks_to_markdown(file_path)
        elif ext == ".json":
            with open(file_path, "w") as f:
                json.dump({"tasks": self.tasks}, f, indent=2)
        else:
            # Default to text format
            with open(file_path, "w") as f:
                f.write("# GlowingGoldenGlobe Tasks\n\n")
                for task in self.tasks:
                    f.write(
                        f"* {task.get('title', 'Untitled')} - {task.get('status', 'Unknown')}\n")
                    f.write(
    f"  Priority: {
        task.get(
            'priority',
            'None')}, Due: {
                task.get(
                    'due_date',
                     'No date')}\n")
                    f.write(f"  {task.get('description', '')}\n\n")

    def export_tasks_to_markdown(self, file_path):
        """Export tasks to a markdown file"""
        with open(file_path, "w") as f:
            f.write("# GlowingGoldenGlobe Project Tasks\n\n")
            f.write(
    f"Generated on {
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Group by status
            statuses = ["Not Started", "In Progress", "On Hold", "Completed"]
            for status in statuses:
                status_tasks = [
    t for t in self.tasks if t.get("status") == status]
                if status_tasks:
                    f.write(f"## {status}\n\n")

                    # Sort by priority
                    priority_order = {
    "Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                    status_tasks.sort(
    key=lambda t: priority_order.get(
        t.get("priority"), 999))

                    for task in status_tasks:
                        f.write(f"### {task.get('title')}\n\n")
                        f.write(
                            f"* **Priority:** {task.get('priority', 'None')}\n")
                        f.write(
                            f"* **Category:** {task.get('category', 'None')}\n")
                        f.write(
                            f"* **Due Date:** {task.get('due_date', 'None')}\n\n")

                        if task.get("description"):
                            f.write(f"{task.get('description')}\n\n")

                        f.write("---\n\n")

                    f.write("\n")

    def update_schedule(self, original_title, title,
                        description, start_date, end_date, recurrence):
        """Update a scheduled activity"""
        schedule = self.get_schedule_by_title(original_title)
        if schedule:
            schedule["title"] = title
            schedule["description"] = description
            schedule["start_date"] = start_date
            schedule["end_date"] = end_date
            schedule["recurrence"] = recurrence
            schedule["updated_at"] = datetime.datetime.now().isoformat()
            self.save_tasks()
            return True
        return False

    def _ensure_psutil_task(self):
        """Ensure that psutil installation reminder is in the task list"""
        # Check if the psutil task already exists
        for task in self.tasks:
            if task.get("title", "").startswith("Install psutil package"):
                return

        # Add psutil installation as a task
        self.add_task(
            title="Install psutil package for full hardware monitoring",
            description="Run 'pip install psutil' to enable complete hardware monitoring functionality in the GUI.",
            priority="Medium",
            category="Development",
            due_date=datetime.datetime.now().strftime("%Y-%m-%d")
        )

        # Save the tasks
        self.save_tasks()


# Simple usage example
if __name__ == "__main__":
    manager = TaskManager()

    # Add a sample task if none exist
    if not manager.get_all_tasks():
        manager.add_task(
            title="Create hardware monitoring system",
            description="Implement system to track CPU, memory and disk usage during simulations",
            category="Development",
            priority="High",
            due_date=datetime.datetime.now().isoformat()
        )
    
    print("Tasks:")
    for task in manager.get_all_tasks():
        print(f"- {task['title']} ({task['priority']}) - Completed: {task['completed']}")
    
    # Export to Markdown
    manager.export_tasks_to_markdown("project_tasks.md")
