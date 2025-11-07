# src/civic_geo_generator/build/pipeline.py
"""Main build pipeline orchestrator using civic libraries."""

from pathlib import Path  # noqa: TCH003
import shutil

from civic_lib_core import log_utils
from civic_lib_geo import geojson_utils, geometry, transform
import geopandas as gpd

from civic_geo_generator.build.config import GeoGeneratorConfig
from civic_geo_generator.build.metadata import MetadataWriter

logger = log_utils.logger


def build(state: str, view: str, version: str | None = None) -> int:
    """Build a geographic layer (main entry point).

    Reads config, processes GeoJSON input, applies transformations,
    repairs geometries, and outputs web-optimized files with metadata.

    Args:
        state: State code, name, or FIPS (e.g., "MN", "Minnesota", "27")
        view: Layer type (e.g., "precincts", "school_districts")
        version: Optional version override (e.g., "2025-04")

    Returns:
        0 on success, 1 on failure
    """
    try:
        # Load configuration
        logger.info(f"Building layer: {state}/{view}")
        config = GeoGeneratorConfig(state, view)
        build_cfg = config.get_build_config()

        # Resolve version
        version = version or build_cfg.get("version")
        if not version:
            raise ValueError("Version is required (either as argument or in config)")
        logger.info(f"Version: {version}")

        # Read input GeoJSON
        input_path: Path = config.get_input_path()
        logger.info(f"Reading input: {input_path}")
        gdf = gpd.read_file(input_path)
        logger.info(f"Loaded {len(gdf)} features")

        # Ensure CRS is set (GeoJSON default)
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)

        # Apply transformations
        logger.info("Applying transformations...")
        gdf = transform.normalize_columns(
            gdf,
            to_lower=build_cfg.get("fields_lowercase", True),
            trim=build_cfg.get("fields_trim", True),
        )

        gdf = update(build_cfg, gdf)

        # Prepare output paths
        output_dir: Path = config.get_output_dir(version)
        output_dir.mkdir(parents=True, exist_ok=True)

        full_name = "full.geojson"
        web_name = "web.geojson"

        full_path: Path = output_dir / full_name
        web_path: Path = output_dir / web_name

        # Write full GeoJSON
        logger.info(f"Writing full GeoJSON: {full_path}")
        geojson_utils.save_geojson(gdf, full_path)

        # For now, web version is same as full (could add simplification later)
        logger.info(f"Writing web GeoJSON: {web_path}")
        shutil.copy2(full_path, web_path)

        # Size check (guarded so tests that mock copy2 do not fail)
        try:
            if web_path.exists() and geojson_utils.needs_chunking(web_path, max_mb=25.0):
                logger.warning(f"File {web_path.name} exceeds 25MB - consider chunking")
        except FileNotFoundError:
            # In tests, shutil.copy2 may be mocked and not create the file.
            logger.debug(f"Size check skipped; missing file: {web_path}")

        # Generate and write metadata
        logger.info("Writing metadata...")
        metadata_writer = MetadataWriter(config, gdf, version)
        metadata_paths = {
            "full_path": full_path,
            "web_name": web_name,
            "topo_name": None,  # TopoJSON support could be added later
        }
        metadata_writer.write(output_dir, metadata_paths)

        logger.info(f"Build completed successfully: {output_dir}")
        return 0

    except Exception as exc:
        logger.error(f"Build failed: {exc}")
        import traceback

        logger.debug(traceback.format_exc())
        return 1


def update(build_cfg, gdf):
    """Apply additional transformations based on build config."""
    if rename_mapping := build_cfg.get("fields_rename"):
        gdf = transform.rename_columns(gdf, rename_mapping)
        logger.debug(f"Renamed columns: {rename_mapping}")

    if add_fields := build_cfg.get("add_fields"):
        gdf = transform.add_fields(gdf, add_fields)
        logger.debug(f"Added fields: {list(add_fields.keys())}")

    if keep_fields := build_cfg.get("fields_keep"):
        gdf = transform.keep_columns(gdf, keep_fields)
        logger.debug(f"Kept columns: {keep_fields}")

        # Repair geometries if requested
    if build_cfg.get("repair_geometries", True):
        logger.info("Repairing geometries...")
        gdf = geometry.repair_geometries(gdf)

        # Validate geometries
    if not geometry.validate_geometries(gdf):
        logger.warning("Some geometries are still invalid after repair")
    return gdf


def main() -> int:
    """CLI entry point for direct execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Build geographic layer")
    parser.add_argument("state", help="State code, name, or FIPS")
    parser.add_argument("view", help="Layer type (e.g., precincts)")
    parser.add_argument("--version", "-v", help="Version string (e.g., 2025-04)")

    args = parser.parse_args()
    return build(args.state, args.view, args.version)


if __name__ == "__main__":
    raise SystemExit(main())
