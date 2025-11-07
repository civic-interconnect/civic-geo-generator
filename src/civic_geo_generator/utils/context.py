"""Shared context and helpers for state/view/version resolution and data paths.

This is the single source of truth for:
- Environment variable overrides (CIVIC_STATE_CODE, CIVIC_STATE_NAME, CIVIC_VIEW)
- Canonical state abbreviation and directory name (via civic_lib_geo.us_constants)
- Repository data paths (delegates to paths)
"""

from dataclasses import dataclass
import os
from pathlib import Path

from civic_geo_generator.utils import paths
from civic_geo_generator.utils.paths import get_state_tokens

__all__ = [
    "GeoContext",
    "parse_state_for_context",
    "resolve_view_from_env",
    "resolve_version_from_env",
]

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

DEFAULT_STATE = "MN"
DEFAULT_VIEW = "precincts"
DEFAULT_VERSION = "2025-04"


# ---------------------------------------------------------------------
# Canonical state/view resolution
# ---------------------------------------------------------------------


def parse_state_for_context() -> tuple[str, str]:
    """Resolve upper case 2 char state code and lowercase 2 char directory name from environment variables.

    Returns:
        Tuple of (state_abbr_uppercase, state_dir_lowercase)
        e.g., ('MN', 'mn')
    """
    raw = os.getenv("CIVIC_STATE_CODE") or os.getenv("CIVIC_STATE_NAME") or DEFAULT_STATE
    tokens = get_state_tokens(raw)
    return tokens.abbr_uppercase, tokens.abbr_lowercase  # ('MN', 'mn')


def resolve_view_from_env() -> str:
    """Resolve the 'view' name from environment variables."""
    return (os.getenv("CIVIC_VIEW") or DEFAULT_VIEW).strip().lower()


def resolve_version_from_env() -> str:
    """Resolve the version tag from environment variables or default."""
    return (os.getenv("CIVIC_VERSION") or DEFAULT_VERSION).strip()


# ---------------------------------------------------------------------
# Canonical GeoContext
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class GeoContext:
    """Unified context for build/validate/index operations."""

    state_abbr_uc: str  # 'MN' (uppercase for display/IDs)
    state_dirname_lc: str  # 'mn' (lowercase for paths)
    view: str  # 'precincts'
    version: str  # '2025-04'

    @classmethod
    def from_env(cls) -> "GeoContext":
        """Construct GeoContext from environment variables."""
        abbr_uc, dir_lc = parse_state_for_context()
        return cls(
            state_abbr_uc=abbr_uc,
            state_dirname_lc=dir_lc,
            view=resolve_view_from_env(),
            version=resolve_version_from_env(),
        )

    # --- Convenience path getters ---

    def get_config_path(self) -> Path:
        """Resolve the config YAML path using shared paths logic."""
        return paths.resolve_config_path(self.state_abbr_uc, self.view)

    def get_data_out_dir(self) -> Path:
        """Return the base output directory for this state/view/version."""
        return paths.get_data_out_dir() / "us" / self.state_dirname_lc / self.view / self.version

    def get_full_geojson_path(self) -> Path:
        """Return expected path to the full GeoJSON."""
        name = "full.geojson"
        return self.get_data_out_dir() / name

    def get_web_geojson_path(self) -> Path:
        """Return expected path to the web GeoJSON."""
        name = "web.geojson"
        return self.get_data_out_dir() / name

    def get_metadata_path(self) -> Path:
        """Return expected path to metadata.json."""
        return self.get_data_out_dir() / "metadata.json"
