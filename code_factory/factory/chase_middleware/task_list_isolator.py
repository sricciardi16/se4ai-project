"""
Defines a middleware to isolate the Task List from the Task Splitter's output,
stripping away any conversational preamble before the first task item.
"""

import logging
from dataclasses import dataclass

# --- Domain Model Imports ---
from chase.domain.models import Content, Part, ContentType

# --- Configuration and Registry Imports ---
from chase.config.models import MiddlewareConfig
from chase.core.registry import middleware_registry

# --- Interface Imports ---
from chase.interfaces.pipeline import Middleware

# Set up a logger for this module
log = logging.getLogger(__name__)


@dataclass
class TaskListIsolatorMiddlewareConfig(MiddlewareConfig):
    """Configuration for the TaskListIsolatorMiddleware. Currently empty."""
    pass


@middleware_registry.register("task_list_isolator", TaskListIsolatorMiddlewareConfig)
class TaskListIsolatorMiddleware(Middleware):
    """
    A presentation middleware that isolates the markdown task list.
    It finds the first line that starts with '- Task Name' or '* Task Name'
    (case-insensitive) and removes all lines before it.
    """

    def __init__(self, config: TaskListIsolatorMiddlewareConfig):
        super().__init__(config)
        log.debug("TaskListIsolatorMiddleware initialized.")

    def process(self, content: Content) -> Content:
        # --- 1. VALIDATION ---
        if not content.parts:
            return content

        part = content.parts[0]

        # Process only TEXT parts
        if part.type != ContentType.TEXT:
            log.debug(f"Skipping part of type {part.type}. Expected TEXT.")
            return content

        text_data = str(part.data)
        lines = text_data.splitlines()

        # --- 2. FIND THE STARTING LIST ITEM ---
        start_idx = -1

        for i, line in enumerate(lines):
            # Strip whitespace and convert to lowercase for a robust check
            stripped_lower = line.strip().lower()
            if stripped_lower.startswith("- task name") or stripped_lower.startswith("* task name"):
                start_idx = i
                break

        # --- 3. ISOLATION ---
        if start_idx != -1:
            # Extract everything from the first task to the end of the text
            extracted_lines = lines[start_idx:]
            final_text = "\n".join(extracted_lines).strip()
            
            log.debug("Successfully isolated the Task List.")
            return Content(parts=[Part(type=ContentType.TEXT, data=final_text)])
        else:
            # Fallback: If the LLM forgot the exact formatting, return the original text
            log.warning("Could not find '- Task Name' or '* Task Name'. Returning original text.")
            return Content(parts=[Part(type=ContentType.TEXT, data=text_data.strip())])