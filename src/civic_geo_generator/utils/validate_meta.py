"""Utility for validating JSON files against a JSON Schema (Draft 2020-12).

File: src/civic_geo_generator/utils/validate_meta.py
"""

import json
from pathlib import Path

from civic_lib_core import log_utils
from jsonschema import Draft202012Validator

logger = log_utils.logger

__all__ = [
    "validate_metadata_schema",
]


def validate_metadata_schema(metadata_path: Path, schema_path: Path) -> bool:
    """Validate a metadata.json file against its schema.

    Returns:
        True if valid, False otherwise.
    """
    with metadata_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        for err in errors:
            logger.error(f"Schema validation error at {list(err.path)}: {err.message}")
        return False

    logger.info(f"{metadata_path.name} validated successfully against schema.")
    return True
