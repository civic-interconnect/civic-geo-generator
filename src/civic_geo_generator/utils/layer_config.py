"""Configuration utilities for loading layer-specific settings.

This module provides utilities for loading and merging YAML configuration files
for geographic data layers, including global defaults and layer-specific overrides.

File: src/civic_geo_generator/utils/layer_config.py
"""

from pathlib import Path
from typing import Any

from civic_lib_core import fs_utils, log_utils
import yaml

logger = log_utils.logger

__all__ = [
    "find_config_files",
    "list_available_states",
    "list_available_views",
    "load_layer_config",
]


def find_config_files(state: str | None = None, view: str | None = None) -> list[Path]:
    """Find all config files, optionally filtered by state and/or view.

    Args:
        state: Optional state code (e.g., "mn")
        view: Optional view/layer type (e.g., "precincts")

    Returns:
        List of Path objects to config files
    """
    config_dir = Path(__file__).parent.parent.parent.parent / "config"

    if state and view:
        # Look for specific file
        pattern = f"us/{state.lower()}/{view}.yaml"
        specific = config_dir / pattern
        if specific.exists():
            return [specific]
        # Try with .yml extension
        specific_yml = config_dir / f"us/{state.lower()}/{view}.yml"
        if specific_yml.exists():
            return [specific_yml]
        return []
    if state:
        # All configs for a state
        state_dir = config_dir / "us" / state.lower()
        if state_dir.exists():
            return list(state_dir.glob("*.yaml")) + list(state_dir.glob("*.yml"))
        return []
    if view:
        # All states with this view type
        return list(config_dir.glob(f"us/*/{view}.yaml")) + list(
            config_dir.glob(f"us/*/{view}.yml")
        )
    # All config files
    return list(config_dir.glob("us/*/*.yaml")) + list(config_dir.glob("us/*/*.yml"))


def list_available_states() -> list[str]:
    """List all states that have config files.

    Returns:
        List of state codes (lowercase)
    """
    config_dir = Path(__file__).parent.parent.parent.parent / "config" / "us"
    if not config_dir.exists():
        return []

    states = [d.name for d in config_dir.iterdir() if d.is_dir()]
    return sorted(states)


def list_available_views(state: str | None = None) -> list[str]:
    """List all available view types, optionally for a specific state.

    Args:
        state: Optional state code to filter by

    Returns:
        List of view names (without .yaml extension)
    """
    configs = find_config_files(state=state)
    views = set()
    for config in configs:
        view_name = config.stem  # filename without extension
        views.add(view_name)
    return sorted(views)


def load_layer_config(layer_name: str, state: str | None = None) -> dict[str, Any]:
    """Load configuration for a given layer, merged with global defaults.

    Args:
        layer_name: Name of the layer (e.g., "mn_precincts_statewide")
        state: Optional state code to narrow search (e.g., "mn")

    Returns:
        Merged configuration dictionary
    """
    config_dir: Path = fs_utils.get_project_root() / "data-config"

    # If state provided, look in state-specific directory
    yaml_dir = config_dir / "us" / state.lower() if state else config_dir

    logger.debug(f"Looking for YAML configs in {yaml_dir}")

    # Find YAML files
    yaml_files = list(yaml_dir.glob("**/*.yaml")) + list(yaml_dir.glob("**/*.yml"))
    if not yaml_files:
        logger.warning(f"No YAML config files found in {yaml_dir}")
        return {}

    logger.debug(f"Found YAML config files: {[f.name for f in yaml_files]}")

    for yaml_file in yaml_files:
        with yaml_file.open(encoding="utf-8") as f:
            logger.debug(f"Loading config from {yaml_file.name}")
            config: dict[str, Any] = yaml.safe_load(f) or {}

            # Check layers section if it exists
            layers = config.get("layers", {})
            if layer_name in layers:
                layer_config = layers[layer_name]
                # Merge with any global defaults
                return {
                    "simplify_tolerance": layer_config.get(
                        "simplify_tolerance", config.get("simplify_tolerance")
                    ),
                    "chunk_max_features": layer_config.get(
                        "chunk_max_features", config.get("chunk_max_features")
                    ),
                    "drop_columns": layer_config.get("drop_columns", config.get("drop_columns")),
                    **layer_config,  # Include all layer-specific fields
                }

    # If not found, return empty dict
    logger.debug(f"No config found for layer: {layer_name}")
    return {}
