from pydantic import field_validator


def parse_nullable_rank_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("排序值必须是整数") from exc
    if normalized <= 0:
        raise ValueError("排序值必须从 1 开始")
    return normalized


def nullable_rank_validator(*field_names: str):
    return field_validator(*field_names, mode="before")(parse_nullable_rank_value)


def parse_import_rank_value(value):
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    try:
        parsed = int(normalized)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        raise ValueError("排序值必须从 1 开始")
    return parsed
