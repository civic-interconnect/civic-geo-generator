"""Utilities for resolving paths to various data directories.

In the civic_geo_generator package.

File: src/civic_geo_generator/utils/paths.py
"""

from collections.abc import Iterable, Sequence
import os
from pathlib import Path

from civic_lib_core import log_utils
from civic_lib_geo.us_constants import get_state_tokens

__all__ = [
    "get_cd118_in_dir",
    "get_cd118_out_dir",
    "get_config_roots",
    "get_data_in_dir",
    "get_data_out_dir",
    "get_national_out_dir",
    "get_repo_root",
    "get_states_out_dir",
    "get_state_lowercase_parts",
    "get_tiger_in_dir",
    "resolve_config_path",
]


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def _iter_candidate_config_paths(state: str, view: str) -> Iterable[Path]:
    """Yield relative candidate paths for a state/view combo.

    - data-config/us/{dir_name}/{view}.yaml
    """
    abbr_lc, dir_name = get_state_lowercase_parts(state)
    view = (view or "").strip()
    yield Path("data-config") / "us" / dir_name / f"{view}.yaml"


def get_cd118_in_dir() -> Path:
    """Return the folder under data-in/ where raw CD118 shapefiles are extracted."""
    return get_tiger_in_dir() / "tl_2022_us_cd118"


def get_cd118_out_dir() -> Path:
    """Return the directory under data-out/national/ where CD118 geojsons are stored."""
    return get_national_out_dir()


def get_config_roots(
    config_root: str | Path | None = None,
    extra_roots: Sequence[str | Path] | None = None,
) -> list[Path]:
    """Return an ordered list of candidate roots to search for config files."""
    roots: list[Path] = []
    seen: set[str] = set()

    def _add(p: str | Path) -> None:
        pp = Path(p).resolve()
        key = str(pp)
        if key not in seen:
            seen.add(key)
            roots.append(pp)

    if config_root:
        _add(config_root)

    env_root = os.getenv("CIGEO_CONFIG_ROOT")
    if env_root:
        _add(env_root)

    if extra_roots:
        for r in extra_roots:
            _add(r)

    _add(Path.cwd())
    _add(get_repo_root())

    return [p for p in roots if p.exists()]


def get_data_in_dir() -> Path:
    """Return the root data-in directory for raw input data (downloads, archives)."""
    return _ensure_dir(get_repo_root() / "data-in")


def get_data_out_dir() -> Path:
    """Return the root data-out directory for processed GeoJSON and chunked outputs."""
    return _ensure_dir(get_repo_root() / "data-out")


def get_national_out_dir() -> Path:
    """Return the directory under data-out/ where national-level files are written.

    Includes layers like national states, counties, or CD118 merged geojsons.
    """
    return _ensure_dir(get_data_out_dir() / "national")


def get_repo_root(levels_up: int = 3) -> Path:
    """Return the root directory of this repo by walking up a fixed number of parent folders.

    Defaults to 3 levels up, assuming this file is under:
        src/civic_geo_generator/utils/
    """
    return Path(__file__).resolve().parents[levels_up]


def get_states_out_dir() -> Path:
    """Return the directory under data-out/ where per-state folders are written."""
    return _ensure_dir(get_data_out_dir() / "us")


def get_state_lowercase_parts(state: str) -> tuple[str, str]:
    """Get lowercase abbreviation and directory name for a state.

    Args:
        state: Any state identifier ('MN', 'Minnesota', '27', etc.)

    Returns:
        Tuple of (abbr_lowercase, dir_name) - both are 'mn' for Minnesota

    Examples:
        >>> get_state_parts('Minnesota')
        ('mn', 'mn')
    """
    tokens = get_state_tokens(state)
    return tokens.abbr_lowercase, tokens.abbr_lowercase  # Both 'mn' now


def get_tiger_in_dir() -> Path:
    """Return the folder under data-in/ where TIGER shapefiles are stored after download and extraction."""
    return _ensure_dir(get_data_in_dir() / "tiger")


def resolve_config_path(
    state: str,
    view: str,
    config_root: str | Path | None = None,
    extra_roots: Sequence[str | Path] | None = None,
) -> Path:
    """Resolve the YAML config path for the given state and view."""
    roots = get_config_roots(config_root=config_root, extra_roots=extra_roots)

    tried: list[Path] = []
    for root in roots:
        for rel in _iter_candidate_config_paths(state, view):
            candidate = root / rel
            tried.append(candidate)
            if candidate.exists():
                log_utils.logger.debug(f"Config found: {candidate}")
                return candidate

    msg = ["Could not locate config for:", f"  state={state!r}", f"  view={view!r}", "Tried:"]
    msg.extend([f"  - {p}" for p in tried])
    raise FileNotFoundError("\n".join(msg))
