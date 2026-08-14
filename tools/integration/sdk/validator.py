"""ConnectorValidator for configuration, payload, and schema verification."""

from typing import Dict, Any, List, Optional
import urllib.parse


class ConnectorValidationError(Exception):
    """Raised when connector configuration or request validation fails."""
    pass


class ConnectorValidator:
    """Validates configuration parameters, request schemas, and endpoint security."""

    @staticmethod
    def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
        """Validate presence of required configuration fields."""
        missing = [key for key in required_keys if key not in config or config[key] is None]
        if missing:
            raise ConnectorValidationError(f"Missing required configuration keys: {', '.join(missing)}")
        return True

    @staticmethod
    def validate_endpoint_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """Validate endpoint URL structure and scheme safety."""
        if not url:
            raise ConnectorValidationError("Endpoint URL cannot be empty.")

        schemes = allowed_schemes or ["http", "https"]
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme and parsed.scheme not in schemes:
            raise ConnectorValidationError(f"Invalid URL scheme '{parsed.scheme}'. Allowed: {schemes}")

        return True

    @staticmethod
    def validate_params(params: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate request parameter dictionary against expected schema types."""
        for param_name, param_type in schema.items():
            if param_name in params:
                val = params[param_name]
                if param_type == "string" and not isinstance(val, str):
                    raise ConnectorValidationError(f"Parameter '{param_name}' must be string, got {type(val).__name__}")
                elif param_type == "int" and not isinstance(val, int):
                    raise ConnectorValidationError(f"Parameter '{param_name}' must be int, got {type(val).__name__}")
                elif param_type == "bool" and not isinstance(val, bool):
                    raise ConnectorValidationError(f"Parameter '{param_name}' must be bool, got {type(val).__name__}")
        return True
