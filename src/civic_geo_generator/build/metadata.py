"""Metadata generation for processed geographic layers."""

import json
from pathlib import Path
from typing import Any

from civic_lib_core import date_utils, log_utils
import geopandas as gpd

logger = log_utils.logger


class MetadataWriter:
    """Generates metadata.json for processed geographic layers."""

    def __init__(self, config, gdf: gpd.GeoDataFrame, version: str):
        """Initialize metadata writer.

        Args:
            config: GeoGeneratorConfig instance
            gdf: Processed GeoDataFrame
            version: Version string
        """
        self.config = config
        self.gdf = gdf
        self.version = version
        self.build_cfg = config.get_build_config()

    def generate_metadata(self, paths: dict[str, Any]) -> dict[str, Any]:
        """Generate metadata dictionary.

        Args:
            paths: Dictionary with full_path, web_name, topo_name

        Returns:
            Complete metadata dictionary
        """
        # Calculate bounds
        minx, miny, maxx, maxy = [float(x) for x in self.gdf.total_bounds]

        # Determine ID and name fields based on view type
        id_field = self._get_id_field()
        name_field = self._get_name_field()

        # Get source information from config
        source_name = str(self.build_cfg.get("source_name", "Unknown"))
        source_url = str(self.build_cfg.get("source_url", ""))
        license_name = str(self.build_cfg.get("license", "Unknown"))
        license_url = str(self.build_cfg.get("license_url", ""))

        # Build metadata structure
        metadata = {
            "$schema": self.config.get_schema_url(),
            "id": f"{self.config.state_abbr.lower()}-{self.config.view}",
            "title": f"{self.config.state_name} {self.config.view.replace('_', ' ').title()}",
            "unit_type": self._get_unit_type(),
            "id_field": id_field,
            "name_field": name_field,
            "snapshot_version": self.version,
            "generated_at": date_utils.now_utc_str(),
            "paths": {
                "full_geojson": paths["full_path"].name,
                "web_geojson": paths["web_name"],
            },
            "stats": {
                "features": int(len(self.gdf)),
                "bbox": [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)],
            },
            "spatial": {
                "crs": "EPSG:4326",
                "geometry_type": self._get_geometry_type(),
            },
            "source_name": source_name,
            "source_url": source_url,
            "license": license_name,
        }

        # Add optional fields
        if paths.get("topo_name"):
            metadata["paths"]["web_topojson"] = paths["topo_name"]

        if license_url:
            metadata["license_url"] = license_url

        if simplify_pct := self.build_cfg.get("simplify_pct"):
            metadata["web"] = {"topojson_simplify_pct": int(simplify_pct)}

        # Add source field mappings if provided
        if source_fields := self.build_cfg.get("source_fields"):
            metadata["source_fields"] = source_fields
        else:
            metadata["source_fields"] = self._get_default_source_fields()

        return metadata

    def write(self, output_dir: Path, paths: dict[str, Any]) -> Path:
        """Write metadata.json to output directory.

        Args:
            output_dir: Directory to write metadata.json
            paths: Dictionary with full_path, web_name, topo_name

        Returns:
            Path to written metadata.json
        """
        metadata = self.generate_metadata(paths)
        metadata_path = output_dir / "metadata.json"

        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Wrote metadata: {metadata_path}")
        return metadata_path

    def _get_id_field(self) -> str:
        """Determine the ID field based on view type and available columns."""
        # Common patterns
        if self.config.view == "precincts":
            for field in ["precinct_id", "precinctid", "id"]:
                if field in self.gdf.columns:
                    return field
        elif self.config.view == "school_districts":
            for field in ["district_id", "districtid", "id"]:
                if field in self.gdf.columns:
                    return field

        # Generic fallback
        for field in ["unit_id", "id", "objectid", "fid"]:
            if field in self.gdf.columns:
                return field

        return "id"  # Default even if not present

    def _get_name_field(self) -> str:
        """Determine the name field based on view type and available columns."""
        # Common patterns
        if self.config.view == "precincts":
            for field in ["precinct_name", "precinctname", "name"]:
                if field in self.gdf.columns:
                    return field
        elif self.config.view == "school_districts":
            for field in ["district_name", "districtname", "name"]:
                if field in self.gdf.columns:
                    return field

        # Generic fallback
        for field in ["unit_name", "name", "label"]:
            if field in self.gdf.columns:
                return field

        return "name"  # Default even if not present

    def _get_unit_type(self) -> str:
        """Get the unit type for the metadata."""
        unit_type_map = {
            "precincts": "precinct",
            "school_districts": "school_district",
            "counties": "county",
            "congressional_districts": "congressional_district",
            "state_house": "state_house_district",
            "state_senate": "state_senate_district",
        }
        return unit_type_map.get(self.config.view, "other")

    def _get_geometry_type(self) -> str:
        """Detect the primary geometry type."""
        geom_types = self.gdf.geometry.type.unique()
        if "MultiPolygon" in geom_types:
            return "MultiPolygon"
        if "Polygon" in geom_types:
            return "Polygon"
        return str(geom_types[0]) if len(geom_types) > 0 else "Unknown"

    def _get_default_source_fields(self) -> dict[str, list[str]]:
        """Generate default source field mappings."""
        id_field = self._get_id_field()
        name_field = self._get_name_field()

        source_fields = {
            id_field: [id_field],
            name_field: [name_field],
        }

        # Add county if present
        if "county" in self.gdf.columns:
            source_fields["county"] = ["county"]

        return source_fields
