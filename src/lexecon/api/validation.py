"""Input validation utilities for API requests.

Provides:
- String length and pattern validation
- Nested data structure validation
- Size limits to prevent DoS attacks
- Type checking for context dicts
"""

from typing import Any, Dict, List, Optional
from pydantic import ValidationError, validator


class ValidationConfig:
    """Configuration for input validation."""

    # String constraints
    MAX_ACTOR_LENGTH = 255  # Actor identifier
    MAX_ACTION_LENGTH = 512  # Proposed action description
    MAX_TOOL_LENGTH = 255  # Tool name
    MAX_INTENT_LENGTH = 2048  # User intent narrative
    MAX_REASON_LENGTH = 10000  # Long text fields

    # Context constraints
    MAX_CONTEXT_DEPTH = 5  # Max nesting levels
    MAX_CONTEXT_SIZE_BYTES = 65536  # 64 KB
    MAX_CONTEXT_KEYS = 100  # Max top-level keys
    MAX_ARRAY_LENGTH = 1000  # Max items in arrays

    # Identifier patterns
    ACTOR_PATTERN = r"^[a-zA-Z0-9_\-\.@]+$"  # Alphanumeric, underscore, dash, dot, @
    TOOL_PATTERN = r"^[a-zA-Z0-9_\-\.]+$"  # Alphanumeric, underscore, dash, dot
    ACTION_PATTERN = r"^[a-zA-Z0-9_\-\.\s/:\(\)]+$"  # Action names with spaces and delimiters


def validate_string_field(
    value: str,
    field_name: str,
    max_length: int,
    pattern: Optional[str] = None,
) -> str:
    """Validate a string field.

    Args:
        value: String to validate
        field_name: Name of field (for error messages)
        max_length: Maximum allowed length
        pattern: Optional regex pattern to match

    Returns:
        Validated string

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

    if pattern:
        import re
        if not re.match(pattern, value):
            raise ValueError(f"{field_name} contains invalid characters")

    return value


def validate_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate context dictionary for safety and size.

    Args:
        context: Context dict to validate

    Returns:
        Validated context

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")

    # Check number of top-level keys
    if len(context) > ValidationConfig.MAX_CONTEXT_KEYS:
        raise ValueError(f"context cannot have more than {ValidationConfig.MAX_CONTEXT_KEYS} keys")

    # Check size in bytes
    import json
    context_bytes = len(json.dumps(context).encode("utf-8"))
    if context_bytes > ValidationConfig.MAX_CONTEXT_SIZE_BYTES:
        raise ValueError(f"context exceeds maximum size of {ValidationConfig.MAX_CONTEXT_SIZE_BYTES} bytes")

    # Validate nesting depth and content
    _validate_depth(context, 0)

    # Validate all keys and values
    for key, value in context.items():
        if not isinstance(key, str):
            raise ValueError("context keys must be strings")

        if not key.strip():
            raise ValueError("context keys cannot be empty")

        # Validate value types
        _validate_value_type(key, value)

    return context


def _validate_depth(obj: Any, depth: int) -> None:
    """Recursively validate nesting depth.

    Args:
        obj: Object to check
        depth: Current nesting depth

    Raises:
        ValueError: If max depth exceeded
    """
    if depth > ValidationConfig.MAX_CONTEXT_DEPTH:
        raise ValueError(f"context exceeds maximum nesting depth of {ValidationConfig.MAX_CONTEXT_DEPTH}")

    if isinstance(obj, dict):
        for value in obj.values():
            _validate_depth(value, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _validate_depth(item, depth + 1)


def _validate_value_type(key: str, value: Any) -> None:
    """Validate that context values are safe types.

    Args:
        key: Key name (for error messages)
        value: Value to validate

    Raises:
        ValueError: If value type is unsafe
    """
    if value is None:
        raise ValueError(f"context[{key}] cannot be None - use omit instead")

    if isinstance(value, (str, int, float, bool)):
        # Primitive types are safe
        if isinstance(value, str) and len(value) > ValidationConfig.MAX_REASON_LENGTH:
            raise ValueError(f"context[{key}] string value exceeds maximum length")
        return

    if isinstance(value, (list, tuple)):
        if len(value) > ValidationConfig.MAX_ARRAY_LENGTH:
            raise ValueError(f"context[{key}] array exceeds maximum length")

        for i, item in enumerate(value):
            if not isinstance(item, (str, int, float, bool, dict, list)):
                raise ValueError(f"context[{key}][{i}] contains unsafe type: {type(item).__name__}")
        return

    if isinstance(value, dict):
        # Nested dict is allowed but will be checked recursively
        return

    # Reject unsafe types
    raise ValueError(
        f"context[{key}] contains unsafe type: {type(value).__name__}. "
        "Only str, int, float, bool, dict, and list are allowed."
    )


def validate_risk_level(value: int) -> int:
    """Validate risk level is in acceptable range.

    Args:
        value: Risk level to validate

    Returns:
        Validated risk level

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, int):
        raise ValueError("risk_level must be an integer")

    if not (1 <= value <= 5):
        raise ValueError("risk_level must be between 1 and 5")

    return value


def validate_policy_mode(value: str) -> str:
    """Validate policy mode is one of allowed values.

    Args:
        value: Policy mode to validate

    Returns:
        Validated policy mode

    Raises:
        ValueError: If validation fails
    """
    allowed_modes = {"strict", "permissive", "paranoid"}

    if not isinstance(value, str):
        raise ValueError("policy_mode must be a string")

    if value.lower() not in allowed_modes:
        raise ValueError(f"policy_mode must be one of: {', '.join(allowed_modes)}")

    return value.lower()


def validate_output_type(value: str) -> str:
    """Validate output type is one of allowed values.

    Args:
        value: Output type to validate

    Returns:
        Validated output type

    Raises:
        ValueError: If validation fails
    """
    allowed_types = {"tool_action", "permit", "deny", "escalate"}

    if not isinstance(value, str):
        raise ValueError("requested_output_type must be a string")

    if value.lower() not in allowed_types:
        raise ValueError(f"requested_output_type must be one of: {', '.join(allowed_types)}")

    return value.lower()


def validate_data_classes(value: List[str]) -> List[str]:
    """Validate data classes list.

    Args:
        value: List to validate

    Returns:
        Validated list

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, list):
        raise ValueError("data_classes must be a list")

    if len(value) > ValidationConfig.MAX_ARRAY_LENGTH:
        raise ValueError(f"data_classes exceeds maximum length of {ValidationConfig.MAX_ARRAY_LENGTH}")

    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"data_classes[{i}] must be a string")

        if not item.strip():
            raise ValueError(f"data_classes[{i}] cannot be empty")

        if len(item) > ValidationConfig.MAX_ACTION_LENGTH:
            raise ValueError(f"data_classes[{i}] exceeds maximum length")

    return value
