"""
Defines a middleware to isolate the Technical Specification from the Architect's output,
normalizing the main headers and demoting any sub-headers to preserve strict hierarchy.
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
class ArchitectSpecIsolatorMiddlewareConfig(MiddlewareConfig):
    """Configuration for the ArchitectSpecIsolatorMiddleware. Currently empty."""
    pass


@middleware_registry.register("architect_spec_isolator", ArchitectSpecIsolatorMiddlewareConfig)
class ArchitectSpecIsolatorMiddleware(Middleware):
    """
    A presentation middleware that isolates and normalizes the Technical Specification.
    1. Finds 'Situation Analysis', 'Implementation Plan', and 'Target State' and forces them to be '### '.
    2. Removes all text before 'Situation Analysis'.
    3. Demotes all other headers to be at least '#### ' while preserving their relative hierarchy.
    """

    def __init__(self, config: ArchitectSpecIsolatorMiddlewareConfig):
        super().__init__(config)
        log.debug("ArchitectSpecIsolatorMiddleware initialized.")

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

        # --- 2. NORMALIZE MAIN HEADERS & FIND START ---
        start_idx = -1
        in_code_block = False

        for i, line in enumerate(lines):
            # Toggle code block state
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
                
            # Skip processing if we are inside a code block
            if in_code_block:
                continue

            # Clean the line to make the search robust against LLM formatting quirks
            clean_line = line.lower().replace("#", "").strip()

            if clean_line.startswith("situation analysis"):
                lines[i] = "### Situation Analysis"
                if start_idx == -1:
                    start_idx = i
            elif clean_line.startswith("implementation plan"):
                lines[i] = "### Implementation Plan"
            elif clean_line.startswith("target state"):
                lines[i] = "### Target State"

        # If we couldn't find the start, fallback to original text
        if start_idx == -1:
            log.warning("Could not find 'Situation Analysis'. Returning original text.")
            return Content(parts=[Part(type=ContentType.TEXT, data=text_data.strip())])

        # Remove everything above 'Situation Analysis'
        lines = lines[start_idx:]

        # --- 3. DEMOTE SUB-HEADERS ---
        # We don't want to touch the three main headers we just created
        main_headers = {"### Situation Analysis", "### Implementation Plan", "### Target State"}
        
        # Find the "largest" sub-header (the one with the FEWEST hashes)
        min_hashes = float('inf')
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
                
            if in_code_block or line in main_headers:
                continue
            
            if line.startswith("#"):
                # Count how many '#' are at the start of the line
                hash_count = len(line) - len(line.lstrip("#"))
                if hash_count > 0:
                    min_hashes = min(min_hashes, hash_count)

        # If the largest sub-header has less than 4 hashes, we need to shift them all down
        if min_hashes < 4:
            # Calculate how many '#' we need to add to make the largest one equal to 4
            shift_amount = 4 - min_hashes
            prefix_to_add = "#" * shift_amount
            in_code_block = False

            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                    
                if in_code_block or line in main_headers:
                    continue
                
                if line.startswith("#"):
                    # Add the extra hashes to preserve the relative hierarchy
                    lines[i] = prefix_to_add + line

        # --- 4. FINALIZE ---
        final_text = "\n".join(lines).strip()
        log.debug("Successfully isolated and normalized the Technical Specification.")
        
        return Content(parts=[Part(type=ContentType.TEXT, data=final_text)])