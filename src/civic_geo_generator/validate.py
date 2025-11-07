"""Validate generated outputs in data-out/ for the selected state/view.

Checks:
- Required files exist for the given snapshot version
- GeoJSON loads; not empty; geometries valid
- CRS is EPSG:4326 (WGS84 lon/lat)
- Required columns present (defaults for precincts; can be overridden via config)
- Optional: check precinct_id uniqueness if present

Usage:
  uv run python -m civic_geo_generator.validate --version 2025-04
"""

from collections.abc import Iterable
import os
from pathlib import Path
from typing import Any

from civic_lib_core import log_utils
import geopandas as gpd
import yaml

from civic_geo_generator.utils.context import GeoContext
from civic_geo_generator.utils.paths import get_state_lowercase_parts

logger = log_utils.logger

DEFAULT_STATE = "MN"
DEFAULT_VIEW = "precincts"


def _get_state_abbr_uc() -> str:
    """Resolve CIVIC_STATE_CODE or CIVIC_STATE_NAME to uppercase 2-letter code."""
    raw = os.getenv("CIVIC_STATE_CODE") or os.getenv("CIVIC_STATE_NAME") or DEFAULT_STATE
    abbr_lc, _ = get_state_lowercase_parts(raw)
    return abbr_lc.upper()


def _get_view_key() -> str:
    """Resolve CIVIC_VIEW or fallback to 'precincts'."""
    return (os.getenv("CIVIC_VIEW") or DEFAULT_VIEW).strip().lower()


class ValidateError(RuntimeError):
    """Custom error class for validation errors."""


def _filenames(write_topojson: bool) -> tuple[list[str], str, str, str | None]:
    """Compute expected filenames based on state/view and settings."""
    full_name = "full.geojson"
    web_name = "web.geojson"
    topo_name = "web.topojson" if write_topojson else None

    required = ["metadata.json", full_name, web_name]
    if topo_name:
        required.append(topo_name)
    return required, full_name, web_name, topo_name


def _require_files(folder: Path, names: Iterable[str]) -> None:
    """Ensure all required output files exist."""
    missing = [n for n in names if not (folder / n).exists()]
    if missing:
        raise ValidateError(f"Missing output files: {missing}")


def _load_gdf(geojson_path: Path) -> gpd.GeoDataFrame:
    """Load GeoJSON and verify CRS and geometry validity."""
    try:
        gdf = gpd.read_file(geojson_path)
    except Exception as exc:
        raise ValidateError(f"Failed to read {geojson_path}: {exc}") from exc
    if gdf.empty:
        raise ValidateError(f"No features in {geojson_path}")

    # Treat missing CRS as EPSG:4326 (GeoJSON default)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)

    if str(gdf.crs).lower() not in ("epsg:4326", "wgs84"):
        raise ValidateError(f"CRS must be EPSG:4326. Found: {gdf.crs}")

    if not gdf.geometry.is_valid.all():
        invalid = int((~gdf.geometry.is_valid).sum())
        raise ValidateError(f"Found {invalid} invalid geometries in {geojson_path}")
    return gdf


def _require_columns(gdf: gpd.GeoDataFrame, cols: Iterable[str]) -> None:
    """Ensure all required columns are present."""
    missing = [c for c in cols if c not in gdf.columns]
    if missing:
        raise ValidateError(f"Missing required columns: {missing}")


def _check_precinct_id_unique(gdf: gpd.GeoDataFrame, col: str = "precinct_id") -> None:
    """Check for duplicate precinct_id values, if the column exists."""
    if col not in gdf.columns:
        return
    s: Any = gdf[col]
    mask: Any = s.duplicated()
    dups_list = list(set(s[mask]))
    if dups_list:
        raise ValidateError(f"Duplicate {col} values: {dups_list[:10]}...")


def main(version: str) -> int:
    """Validate outputs for the selected state/view and snapshot version."""
    try:
        ctx = GeoContext.from_env().__class__(
            state_abbr_uc=GeoContext.from_env().state_abbr_uc,
            state_dirname_lc=GeoContext.from_env().state_dirname_lc,
            view=GeoContext.from_env().view,
            version=version,
        )

        cfg = yaml.safe_load(ctx.get_config_path().read_text())
        out_dir = ctx.get_data_out_dir()

        write_topo = bool(cfg.get("write_topojson", False))
        required, full_name, web_name, topo_name = _filenames(write_topo)
        _require_files(out_dir, required)

        full_path = out_dir / full_name
        gdf = _load_gdf(full_path)

        default_required_precincts: tuple[str, ...] = (
            "precinct_id",
            "precinct_name",
            "county",
        )
        required_columns = cfg.get("required_columns")
        if isinstance(required_columns, list) and required_columns:
            req_cols = [str(c) for c in required_columns]
        else:
            req_cols = list(default_required_precincts)

        _require_columns(gdf, req_cols)

        unique_field = cfg.get("unique_id_column", "precinct_id")
        if unique_field:
            _check_precinct_id_unique(gdf, str(unique_field))

        logger.info("Validation passed.")
        return 0
    except Exception as exc:
        logger.error(f"Validation failed: {exc}")
        return 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Validate generated outputs for a snapshot version.")
    ap.add_argument("--version", "-v", required=True, help='Snapshot tag like "2025-04"')
    args = ap.parse_args()
    raise SystemExit(main(version=args.version))
