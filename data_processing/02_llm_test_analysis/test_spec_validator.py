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
    Validates the JSON output for the behavioral extraction phase.
    Ensures the LLM outputs the exact schema required for functional and robustness tests.
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

        # 2. Validate Root Structure
        if not isinstance(data, dict):
            raise MiddlewareException("The root of the JSON output must be a dictionary.")

        expected_root_keys = {"functional_behaviors", "robustness_behaviors"}
        if not expected_root_keys.issubset(data.keys()):
            raise MiddlewareException(f"JSON is missing required root arrays. Required: {expected_root_keys}.")

        # 3. Validate Item Structure
        required_item_keys = {
            "original_test_name",
            "new_test_name",
            "target_api",
            "behavioral_specification",
            "crucial_data"
        }

        for category in expected_root_keys:
            items = data[category]
            if not isinstance(items, list):
                raise MiddlewareException(f"The value of '{category}' must be a list (array).")

            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    raise MiddlewareException(f"Item at index {idx} in '{category}' must be a dictionary.")

                if not required_item_keys.issubset(item.keys()):
                    missing = required_item_keys - item.keys()
                    raise MiddlewareException(f"Item at index {idx} in '{category}' is missing keys: {missing}")

                # Ensure all values are strings (as requested in the prompt)
                for key in required_item_keys:
                    if not isinstance(item[key], str):
                        raise MiddlewareException(f"The value for '{key}' in '{category}' index {idx} must be a string.")

        # If it passes all checks, return the content unmodified
        return content