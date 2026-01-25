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


def validate_recommendation_dict(value: Optional[Dict[str, Any]], field_name: str) -> Optional[Dict[str, Any]]:
    """Validate AI recommendation or decision dict.

    Ensures 'confidence' key exists for recommendations.

    Args:
        value: Dict to validate
        field_name: Field name for error messages

    Returns:
        Validated dict

    Raises:
        ValueError: If validation fails
    """
    if value is None:
        return None

    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary")

    # Validate size and structure
    validated = validate_context(value)

    # Check for required 'confidence' key in recommendations
    if field_name == "ai_recommendation":
        if "confidence" not in validated:
            raise ValueError(f"{field_name} must include 'confidence' key")

        confidence = validated["confidence"]
        if not isinstance(confidence, (int, float)):
            raise ValueError(f"{field_name}['confidence'] must be a number")

        if not (0 <= confidence <= 1):
            raise ValueError(f"{field_name}['confidence'] must be between 0 and 1")

    return validated


def validate_override_scope(value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Validate override scope limitations dict.

    Args:
        value: Dict to validate

    Returns:
        Validated dict

    Raises:
        ValueError: If validation fails
    """
    if value is None:
        return None

    return validate_context(value)


def validate_iso_timestamp(value: Optional[str], field_name: str = "timestamp") -> Optional[str]:
    """Validate ISO 8601 timestamp string.

    Args:
        value: Timestamp string to validate
        field_name: Field name for error messages

    Returns:
        Validated timestamp

    Raises:
        ValueError: If validation fails
    """
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    try:
        # Try to parse as ISO format
        from datetime import datetime
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    except (ValueError, AttributeError) as e:
        raise ValueError(f"{field_name} must be valid ISO 8601 format (e.g., 2024-01-25T10:30:00Z)")


def validate_justification(value: str) -> str:
    """Validate override justification text.

    Args:
        value: Justification text

    Returns:
        Validated text

    Raises:
        ValueError: If validation fails
    """
    return validate_string_field(
        value,
        "justification",
        ValidationConfig.MAX_REASON_LENGTH,
    )


def validate_reason(value: str) -> str:
    """Validate intervention reason text.

    Args:
        value: Reason text

    Returns:
        Validated text

    Raises:
        ValueError: If validation fails
    """
    return validate_string_field(
        value,
        "reason",
        ValidationConfig.MAX_REASON_LENGTH,
    )


def validate_time_window(value: str) -> str:
    """Validate time window for audit export.

    Args:
        value: Time window value

    Returns:
        Validated time window

    Raises:
        ValueError: If validation fails
    """
    allowed_windows = {"all", "today", "week", "month", "quarter", "year"}

    if not isinstance(value, str):
        raise ValueError("time_window must be a string")

    value_lower = value.lower()
    if value_lower not in allowed_windows:
        raise ValueError(f"time_window must be one of: {', '.join(allowed_windows)}")

    return value_lower


def validate_export_formats(value: List[str]) -> List[str]:
    """Validate export formats list.

    Args:
        value: List of formats

    Returns:
        Validated list

    Raises:
        ValueError: If validation fails
    """
    allowed_formats = {"json", "csv", "markdown", "html"}

    if not isinstance(value, list):
        raise ValueError("formats must be a list")

    if not value:
        raise ValueError("formats cannot be empty")

    if len(value) > 10:
        raise ValueError("formats cannot have more than 10 items")

    validated = []
    for fmt in value:
        if not isinstance(fmt, str):
            raise ValueError("formats items must be strings")

        fmt_lower = fmt.lower()
        if fmt_lower not in allowed_formats:
            raise ValueError(f"Invalid format '{fmt}'. Must be one of: {', '.join(allowed_formats)}")

        if fmt_lower not in validated:  # No duplicates
            validated.append(fmt_lower)

    return validated


def validate_export_email(value: str) -> str:
    """Validate email address for export requester.

    Args:
        value: Email address

    Returns:
        Validated email

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError("Email must be a string")

    value = value.strip()

    if not value:
        raise ValueError("Email cannot be empty")

    if len(value) > 254:  # RFC 5321
        raise ValueError("Email exceeds maximum length of 254 characters")

    # Basic email pattern (not comprehensive, good enough for validation)
    import re
    email_pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

    if not re.match(email_pattern, value):
        raise ValueError("Invalid email address format")

    return value
