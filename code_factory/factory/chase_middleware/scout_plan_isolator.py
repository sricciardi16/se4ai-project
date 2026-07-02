"""
Defines a middleware to isolate the Context Retrieval Plan from the Scout's output,
stripping away any conversational preamble before the first file item.
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
class ScoutPlanIsolatorMiddlewareConfig(MiddlewareConfig):
    """Configuration for the ScoutPlanIsolatorMiddleware. Currently empty."""
    pass


@middleware_registry.register("scout_plan_isolator", ScoutPlanIsolatorMiddlewareConfig)
class ScoutPlanIsolatorMiddleware(Middleware):
    """
    A presentation middleware that isolates the markdown file list.
    It finds the first line that starts with '- File:' or '* File:'
    (case-insensitive) and removes all lines before it.
    """

    def __init__(self, config: ScoutPlanIsolatorMiddlewareConfig):
        super().__init__(config)
        log.debug("ScoutPlanIsolatorMiddleware initialized.")

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
            if stripped_lower.startswith("- file:") or stripped_lower.startswith("* file:") or stripped_lower.startswith("- **file:") or stripped_lower.startswith("* **file:"):  
                start_idx = i
                break

        # --- 3. ISOLATION ---
        if start_idx != -1:
            # Extract everything from the first file item to the end of the text
            extracted_lines = lines[start_idx:]
            final_text = "\n".join(extracted_lines).strip()
            
            log.debug("Successfully isolated the Scout Plan.")
            return Content(parts=[Part(type=ContentType.TEXT, data=final_text)])
        else:
            # Fallback: If the LLM forgot the exact formatting, return the original text
            log.warning("Could not find '- File:' or '* File:'. Returning original text.")
            return Content(parts=[Part(type=ContentType.TEXT, data=text_data.strip())])