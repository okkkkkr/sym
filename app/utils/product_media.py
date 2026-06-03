import re
from pathlib import Path


MEDIA_INDEX_PATTERN = re.compile(r"_(\d+)(?:\.[^.]+)?$")
UUID_PREFIX_PATTERN = re.compile(r"^[0-9a-f]{32}_(.+)$", re.IGNORECASE)


def extract_media_sort_name(value: str) -> str:
    name = Path(str(value or "")).name
    matched = UUID_PREFIX_PATTERN.match(name)
    return matched.group(1) if matched else name


def extract_media_sort_index(value: str) -> int | None:
    matched = MEDIA_INDEX_PATTERN.search(extract_media_sort_name(value))
    return int(matched.group(1)) if matched else None


def build_media_sort_key(value: str) -> tuple[int, int, str]:
    normalized_name = extract_media_sort_name(value).lower()
    index = extract_media_sort_index(value)
    if index is None:
        return (1, 0, normalized_name)
    return (0, index, normalized_name)


def sort_media_keys(keys: list[str]) -> list[str]:
    return sorted(keys, key=build_media_sort_key)


def sort_media_paths(paths: list[str]) -> list[str]:
    return sorted(paths, key=build_media_sort_key)
