"""Configuration management for civic-geo-generator build pipeline."""

import os
from pathlib import Path
from typing import Any

from civic_lib_core import log_utils
from civic_lib_geo.us_constants import get_state_record_by_any
import yaml

from civic_geo_generator.utils.paths import get_data_in_dir, get_data_out_dir

logger = log_utils.logger


class GeoGeneratorConfig:
    """Manages build configuration loading and access."""

    def __init__(self, state: str, view: str):
        """Initialize config for a state/view combination.

        Args:
            state: State code, name, or FIPS (e.g., "MN", "Minnesota", "27")
            view: Layer type (e.g., "precincts", "school_districts")
        """
        # Validate and normalize state
        self.state_record = get_state_record_by_any(state)
        if not self.state_record:
            raise ValueError(f"Unknown state: {state}")

        self.state_abbr = self.state_record["abbr"]  # e.g., "MN"
        self.state_name = self.state_record["name"]  # e.g., "Minnesota"
        self.state_fips = self.state_record["fips"]  # e.g., "27"
        self.state_name_lower = self.state_name.lower().replace(" ", "_")  # e.g., "minnesota"

        self.view = view.lower()
        self._config: dict[str, Any] | None = None
        self._build_cfg: dict[str, Any] | None = None

    def find_config_path(self) -> Path:
        """Find config file - supports both old and new structure.

        Search order:
        1. Environment variable override (CIVIC_CFG)
        2. data-config/us/{state}/{view}.yaml

        Returns:
            Path to config file

        Raises:
            FileNotFoundError: If no config found
        """
        # Check for explicit override
        if env_cfg := os.getenv("CIVIC_CFG"):
            p = Path(env_cfg)
            if p.exists():
                return p
            raise FileNotFoundError(f"Config override not found: {p}")

        config_dir = Path("data-config")
        new_paths = [
            config_dir / "us" / self.state_abbr.lower() / f"{self.view}.yaml",
            config_dir / "us" / self.state_abbr.lower() / f"{self.view}.yml",
        ]

        for p in new_paths:
            if p.exists():
                logger.info(f"Using config: {p}")
                return p

        # List what we tried
        searched = [str(p) for p in new_paths]
        raise FileNotFoundError(
            f"No config found for {self.state_abbr}/{self.view}.\nSearched: {', '.join(searched)}"
        )

    def load(self) -> dict[str, Any]:
        """Load the full config file.

        Returns:
            Complete config dictionary
        """
        if self._config is None:
            path = self.find_config_path()
            with path.open("r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded config from {path}")
        return self._config or {}

    def get_build_config(self) -> dict[str, Any]:
        """Get the build section of config.

        Returns:
            Build configuration dictionary

        Raises:
            ValueError: If build section is missing
        """
        if self._build_cfg is None:
            config = self.load()
            self._build_cfg = config.get("build", {})
            if not self._build_cfg:
                raise ValueError(
                    f"Missing 'build' section in config for {self.state_abbr}/{self.view}"
                )
        return self._build_cfg

    def get_input_path(self) -> Path:
        """Get the input file path from config.

        Returns:
            Path to input GeoJSON file

        Raises:
            ValueError: If input_path not specified
            FileNotFoundError: If input file doesn't exist
        """
        build_cfg = self.get_build_config()
        rel_path = build_cfg.get("input_path")
        if not rel_path:
            raise ValueError("build.input_path is required in config")

        full_path = get_data_in_dir() / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Input file not found: {full_path}")

        return full_path

    def get_output_dir(self, version: str) -> Path:
        """Get the output directory for processed files.

        Args:
            version: Version string (e.g., "2025-04")

        Returns:
            Path to output directory (created if doesn't exist)
        """
        out_dir = get_data_out_dir() / "us" / self.state_abbr.lower() / self.view / version
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def get_schema_url(self) -> str:
        """Determine the appropriate schema URL for metadata.json.

        Priority:
        1. Explicit schema_url in build config
        2. Environment variable CIVIC_SCHEMA_URL
        3. Local development mode (CIVIC_USE_LOCAL_SCHEMA=true)
        4. GitHub raw URL (default)

        Returns:
            Schema URL string
        """
        build_cfg = self.get_build_config()

        # Check explicit override in config
        if url := build_cfg.get("schema_url"):
            return url

        # Check environment override
        if url := os.getenv("CIVIC_SCHEMA_URL"):
            return url

        # Local development mode
        if os.getenv("CIVIC_USE_LOCAL_SCHEMA", "").lower() == "true":
            return "../../../../schemas/output/metadata/v0.1.0/schema.json"

        # Build GitHub URL
        org = os.getenv("CIVIC_GH_ORG", "civic-interconnect")
        repo = os.getenv("CIVIC_GH_REPO", "civic-geo-generator")
        ref = build_cfg.get("schema_ref", "main")  # Git ref (branch/tag)
        schema_version = build_cfg.get("schema_version", "v0.1.0")  # folder name
        return (
            f"https://raw.githubusercontent.com/{org}/{repo}/{ref}/"
            f"schemas/output/metadata/{schema_version}/schema.json"
        )
