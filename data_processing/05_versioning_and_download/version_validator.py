import json
import logging
import re
from dataclasses import dataclass

from chase.config.models import MiddlewareConfig
from chase.core.registry import middleware_registry
from chase.domain.models import Content
from chase.exceptions.exceptions import MiddlewareException
from chase.interfaces.pipeline import Middleware

log = logging.getLogger(__name__)

@dataclass
class VersionJSONValidatorConfig(MiddlewareConfig):
    pass

@middleware_registry.register("version_json_validator", VersionJSONValidatorConfig)
class VersionJSONValidator(Middleware):
    def process(self, content: Content) -> Content:
        raw_text = content.parts[0].data

        match = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
        json_string = match.group(1) if match else raw_text.strip()

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise MiddlewareException(f"Failed to parse JSON: {e}")

        if not isinstance(data, dict):
            raise MiddlewareException("Root must be a JSON object (dictionary).")

        required_keys = {"target_version"}
        if not required_keys.issubset(data.keys()):
            raise MiddlewareException(f"Missing required keys: {required_keys - data.keys()}")

        for key in required_keys:
            if not isinstance(data[key], str):
                raise MiddlewareException(f"Value for '{key}' must be a string.")

        return content