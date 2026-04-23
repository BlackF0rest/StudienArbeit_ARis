from __future__ import annotations
from typing import Any

TELEPROMPTER_FIELDS: dict[str, type] = {
    "text": str,
    "speed": (int, float),
    "fontSize": (int, float),
    "fontColor": str,
    "backgroundColor": str,
    "fontFamily": str,
    "lineHeight": (int, float),
    "opacity": (int, float),
}


def _coerce_value(field: str, value: Any, expected_type: type | tuple[type, ...]) -> tuple[Any, str | None]:
    if isinstance(value, expected_type):
        return value, None

    if expected_type == str:
        return str(value), f"{field} was coerced to string"

    if expected_type == (int, float):
        try:
            return float(value), f"{field} was coerced to number"
        except (TypeError, ValueError):
            return None, f"{field} must be a number"

    return None, f"{field} has an unsupported type"


def validate_teleprompter_payload(
    payload: Any,
    defaults: dict[str, Any],
    strict: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, str], list[str]]:
    if not isinstance(payload, dict):
        return None, {"payload": "JSON object expected"}, []

    cleaned: dict[str, Any] = {}
    errors: dict[str, str] = {}
    warnings: list[str] = []

    for field, expected_type in TELEPROMPTER_FIELDS.items():
        if field not in payload:
            if strict:
                errors[field] = "field is required"
                continue
            cleaned[field] = defaults[field]
            warnings.append(f"{field} missing; default value used")
            continue

        value, warning_or_error = _coerce_value(field, payload[field], expected_type)
        if value is None:
            if strict:
                errors[field] = warning_or_error or "invalid value"
            else:
                cleaned[field] = defaults[field]
                warnings.append(f"{field} invalid; default value used")
        else:
            cleaned[field] = value
            if warning_or_error:
                warnings.append(warning_or_error)

    return cleaned, errors, warnings
