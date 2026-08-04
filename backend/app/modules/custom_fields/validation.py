from datetime import datetime
from typing import Any

from app.core.errors import ValidationAppError
from app.modules.custom_fields.models import CustomFieldDefinition


def validate_custom_field_values(
    *, definitions: list[CustomFieldDefinition], values: dict[str, Any]
) -> dict[str, Any]:
    """Validate a submitted custom_fields payload against the org's field
    definitions for that entity type: rejects unknown keys, checks each
    value's type, and requires values for fields marked required. Returns the
    values unchanged (normalized) on success — raises ValidationAppError with
    a clear message otherwise."""
    by_key = {definition.field_key: definition for definition in definitions}

    unknown_keys = set(values) - set(by_key)
    if unknown_keys:
        raise ValidationAppError(f"Unknown custom field(s): {', '.join(sorted(unknown_keys))}.")

    for definition in definitions:
        if definition.field_key not in values:
            if definition.is_required:
                raise ValidationAppError(f"Custom field '{definition.label}' is required.")
            continue
        _validate_value(definition, values[definition.field_key])

    return values


def _validate_value(definition: CustomFieldDefinition, value: Any) -> None:
    if value is None:
        if definition.is_required:
            raise ValidationAppError(f"Custom field '{definition.label}' is required.")
        return

    if definition.field_type == "text":
        if not isinstance(value, str):
            raise ValidationAppError(f"Custom field '{definition.label}' must be text.")
    elif definition.field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationAppError(f"Custom field '{definition.label}' must be a number.")
    elif definition.field_type == "boolean":
        if not isinstance(value, bool):
            raise ValidationAppError(f"Custom field '{definition.label}' must be true or false.")
    elif definition.field_type == "date":
        if not isinstance(value, str):
            raise ValidationAppError(f"Custom field '{definition.label}' must be a date string.")
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValidationAppError(
                f"Custom field '{definition.label}' must be a valid ISO date."
            ) from exc
    elif definition.field_type == "select":
        if value not in (definition.options or []):
            raise ValidationAppError(
                f"Custom field '{definition.label}' must be one of the allowed options."
            )
    else:
        raise ValidationAppError(f"Unsupported custom field type: {definition.field_type}.")
