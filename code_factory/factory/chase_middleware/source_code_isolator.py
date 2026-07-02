"""
Defines a middleware to isolate raw source code from LLM outputs,
stripping away markdown fences and any conversational text.
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
class SourceCodeIsolatorMiddlewareConfig(MiddlewareConfig):
    """Configuration for the SourceCodeIsolatorMiddleware. Currently empty."""
    pass


@middleware_registry.register("source_code_isolator", SourceCodeIsolatorMiddlewareConfig)
class SourceCodeIsolatorMiddleware(Middleware):
    """
    A presentation middleware that isolates the raw source code from an LLM response.
    It finds the first line starting with ``` (e.g., ```python or ```bash),
    finds the last line that is exactly ```, and returns ONLY the source code between them,
    discarding any conversational text before or after the fences.
    """

    def __init__(self, config: SourceCodeIsolatorMiddlewareConfig):
        super().__init__(config)
        log.debug("SourceCodeIsolatorMiddleware initialized.")

    def process(self, content: Content) -> Content:
        # --- 1. VALIDATION ---
        if not content.parts:
            return content

        part = content.parts[0]

        if part.type != ContentType.TEXT:
            log.debug(f"Skipping part of type {part.type}. Expected TEXT.")
            return content

        text_data = str(part.data)
        lines = text_data.splitlines()

        # --- 2. FIND THE FIRST COMPLETE CODE BLOCK ---
        start_idx = -1
        end_idx = -1

        # Find the FIRST line that starts with ```
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                start_idx = i
                break

        # If we found a start fence, find the VERY NEXT line that starts with ```
        if start_idx != -1:
            for i in range(start_idx + 1, len(lines)):
                if lines[i].strip().startswith("```"):
                    end_idx = i
                    break

        # --- 3. ISOLATION ---
        if start_idx != -1 and end_idx != -1:
            # Extract everything BETWEEN the two fences
            extracted_lines = lines[start_idx + 1 : end_idx]
            final_text = "\n".join(extracted_lines).strip()
            
            log.debug("Successfully isolated source code from LLM output.")
            return Content(parts=[Part(type=ContentType.TEXT, data=final_text)])
        else:
            # Fallback: If the LLM forgot fences, just return the stripped text
            log.warning("Could not find valid markdown code fences. Returning original text.")
            return Content(parts=[Part(type=ContentType.TEXT, data=text_data.strip())])