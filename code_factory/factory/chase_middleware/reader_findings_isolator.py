"""
Defines a middleware to isolate the Findings from the Reader's output,
stripping away any conversational preamble before the first finding.
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
class ReaderFindingsIsolatorMiddlewareConfig(MiddlewareConfig):
    """Configuration for the ReaderFindingsIsolatorMiddleware. Currently empty."""
    pass


@middleware_registry.register("reader_findings_isolator", ReaderFindingsIsolatorMiddlewareConfig)
class ReaderFindingsIsolatorMiddleware(Middleware):
    """
    A presentation middleware that isolates the Reader's findings.
    It finds the first line that starts with '**' (e.g., **[Finding Name]**)
    and removes all lines before it.
    """

    def __init__(self, config: ReaderFindingsIsolatorMiddlewareConfig):
        super().__init__(config)
        log.debug("ReaderFindingsIsolatorMiddleware initialized.")

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

        # --- 2. FIND THE STARTING HEADER ---
        start_idx = -1

        for i, line in enumerate(lines):
            # Strip whitespace to catch lines that might have accidental indentation
            if line.strip().startswith("**"):
                start_idx = i
                break

        # --- 3. ISOLATION ---
        if start_idx != -1:
            # Extract everything from the first finding to the end of the text
            extracted_lines = lines[start_idx:]
            final_text = "\n".join(extracted_lines).strip()
            
            log.debug("Successfully isolated the Reader Findings.")
            return Content(parts=[Part(type=ContentType.TEXT, data=final_text)])
        else:
            # Fallback: If the LLM forgot the formatting, or if it output exactly "NO_FINDINGS"
            if "NO_FINDINGS" in text_data:
                log.debug("Reader returned NO_FINDINGS. Passing through.")
            else:
                log.warning("Could not find a line starting with '**'. Returning original text.")
            
            return Content(parts=[Part(type=ContentType.TEXT, data=text_data.strip())])