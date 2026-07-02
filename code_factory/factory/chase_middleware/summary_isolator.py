"""
Defines a middleware to isolate the Summary text from the Summarizer's output,
stripping away the '### Summary' header and any conversational preamble before it.
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
class SummaryIsolatorMiddlewareConfig(MiddlewareConfig):
    """Configuration for the SummaryIsolatorMiddleware. Currently empty."""
    pass


@middleware_registry.register("summary_isolator", SummaryIsolatorMiddlewareConfig)
class SummaryIsolatorMiddleware(Middleware):
    """
    A presentation middleware that isolates the pure summary text.
    It finds the first line that starts with '### Summary' and removes
    both that header line and all lines before it.
    """

    def __init__(self, config: SummaryIsolatorMiddlewareConfig):
        super().__init__(config)
        log.debug("SummaryIsolatorMiddleware initialized.")

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

        # --- 2. FIND THE HEADER ---
        start_idx = -1

        for i, line in enumerate(lines):
            # Strip whitespace to catch lines that might have accidental indentation
            if line.strip().startswith("### Summary"):
                start_idx = i
                break

        # --- 3. ISOLATION ---
        if start_idx != -1:
            # Extract everything AFTER the header (start_idx + 1)
            extracted_lines = lines[start_idx + 1:]
            final_text = "\n".join(extracted_lines).strip()
            
            log.debug("Successfully isolated the Summary text.")
            return Content(parts=[Part(type=ContentType.TEXT, data=final_text)])
        else:
            # Fallback: If the LLM forgot the header, return the original text
            log.warning("Could not find '### Summary' header. Returning original text.")
            return Content(parts=[Part(type=ContentType.TEXT, data=text_data.strip())])