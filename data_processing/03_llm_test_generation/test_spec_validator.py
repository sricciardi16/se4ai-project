import json
import logging
import re
from dataclasses import dataclass

from chase.config.models import MiddlewareConfig
from chase.core.registry import middleware_registry
from chase.domain.models import Content
from chase.exceptions.exceptions import MiddlewareException
from chase.interfaces.pipeline import Middleware

# Set up a logger for this module
log = logging.getLogger(__name__)

@dataclass
class TestSpecJSONValidatorConfig(MiddlewareConfig):
    pass

@middleware_registry.register("test_spec_json_validator", TestSpecJSONValidatorConfig)
class TestSpecJSONValidator(Middleware):
    """
    Validates the JSON output for the test specification conversion phase.
    Ensures the LLM outputs a strict JSON array of test objects.
    """

    def process(self, content: Content) -> Content:
        raw_text = content.parts[0].data

        # Safely extract JSON from markdown blocks, ignoring conversational text
        match = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
        if match:
            json_string = match.group(1)
        else:
            # Fallback in case the LLM just output raw JSON without markdown ticks
            json_string = raw_text.strip()

        # 1. Validate JSON Parsing
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise MiddlewareException(f"Failed to parse JSON. The LLM output invalid JSON syntax: {e}")

        # 2. Validate Root Structure (Must be an Array/List)
        if not isinstance(data, list):
            raise MiddlewareException("The root of the JSON output must be a JSON array (list).")

        # 3. Validate Item Structure
        required_keys = {
            "test_name",
            "target_api",
            "behavioral_specification",
            "crucial_data"
        }

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise MiddlewareException(f"Item at index {idx} in the array must be a JSON object (dictionary).")

            if not required_keys.issubset(item.keys()):
                missing = required_keys - item.keys()
                raise MiddlewareException(f"Item at index {idx} is missing required keys: {missing}")

            # Ensure all required values are strings
            for key in required_keys:
                if not isinstance(item[key], str):
                    raise MiddlewareException(f"The value for '{key}' at index {idx} must be a string.")

        # If it passes all checks, return the content unmodified
        return content